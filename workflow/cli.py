"""Public command line. All mutations use the per-vault coordinator."""
import argparse
import json
from pathlib import Path
import platform
import shutil
import sys
from zoneinfo import ZoneInfo
from .core import Vault,Zotero,COLORS,read_json,save,now
from . import addons,scheduler

ROOT=Path(__file__).resolve().parents[1]


def default_config():
    return {'version':1,'zotero_api':'http://127.0.0.1:23119/api','collection_keys':[], 'include_children':True,
        'timezone':'UTC','routes':{},'citekey_overrides':{},'main_attachments':{},
        'colors':{name:meaning for name,meaning in COLORS.values()},
        'marker':{'enabled':False,'executable':'.marker-venv/bin/marker_single','timeout_seconds':3600},
        'qmd':{'enabled':False,'node':'node','runtime':'.workflow/qmd-runtime','timeout_seconds':1800},
        'codex':{'enabled':False,'executable':'codex','model':None,'timeout_seconds':3600},
        'scite':{'enabled':False},'scheduler':{'enabled':False,'mode':'convert','interval_seconds':3600,'notifications':True}}


def doctor(vault):
    checks=[]
    def check(name,fn):
        try: value=fn();checks.append({'check':name,'ok':True,'detail':value})
        except Exception as e:checks.append({'check':name,'ok':False,'detail':str(e)})
    check('Python',lambda:sys.version.split()[0] if sys.version_info>=(3,12) else (_ for _ in ()).throw(ValueError('Use Python 3.12+')))
    check('Zotero collection scope',lambda: sorted(vault.scope(vault.collections())))
    check('Paper identity and note conflicts',lambda: vault.sync(dry_run=True))
    for entry in checks:
        if isinstance(entry.get('detail'),dict) and entry['detail'].get('issues'):entry['ok']=False
    for name in ('marker','codex'):
        cfg=vault.config.get(name,{})
        if cfg.get('enabled'):check(name,lambda cfg=cfg:addons.executable(vault,cfg['executable']))
    if vault.config.get('qmd',{}).get('enabled'):
        check('QMD Node',lambda:addons.executable(vault,vault.config['qmd']['node']))
        check('QMD SDK',lambda: str(vault.path(vault.config['qmd']['runtime']+'/sdk/dist/index.js')) if vault.path(vault.config['qmd']['runtime']+'/sdk/dist/index.js').is_file() else (_ for _ in ()).throw(ValueError('Install QMD first')))
    check('Vault writable',lambda: 'yes' if __import__('os').access(vault.root,__import__('os').W_OK) else (_ for _ in ()).throw(ValueError('Vault not writable')))
    return {'ok':all(c['ok'] for c in checks),'platform':platform.platform(),'checks':checks,
        'manual_checks':['Chrome Connector: save a test item into the selected collection','Scite Zotero plugin: verify columns and open a report'],
        'note':'Executable detection does not establish conversion, AI authentication, or plugin functionality.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Local Zotero → Obsidian reading workflow')
    parser.add_argument('--vault',type=Path,default=ROOT)
    sub=parser.add_subparsers(dest='command',required=True)
    init=sub.add_parser('init');init.add_argument('--collection',action='append');init.add_argument('--timezone',default='UTC');init.add_argument('--demo',action='store_true');init.add_argument('--list-collections',action='store_true')
    sub.add_parser('doctor');sub.add_parser('status')
    sync=sub.add_parser('sync');sync.add_argument('--dry-run',action='store_true')
    cv=sub.add_parser('convert');cv.add_argument('item')
    idx=sub.add_parser('index');idx.add_argument('--semantic',action='store_true')
    search=sub.add_parser('search');search.add_argument('query');search.add_argument('--method',choices=['keyword','semantic','hybrid'],default='keyword');search.add_argument('--limit',type=int,default=10)
    summary=sub.add_parser('summarize');summary.add_argument('item',nargs='?');summary.add_argument('--run',action='store_true');summary.add_argument('--refresh',action='store_true');summary.add_argument('--reason');summary.add_argument('--publish',type=Path);summary.add_argument('--token');summary.add_argument('--accept',action='store_true')
    sc=sub.add_parser('scite');sc.add_argument('item')
    sched=sub.add_parser('schedule');sched.add_argument('action',choices=['install','disable','uninstall','status','run','check','queue','retry']);sched.add_argument('--item')
    args=parser.parse_args(argv);root=args.vault.resolve()
    if args.command=='init':
        cfg=default_config();cfg['timezone']=args.timezone;ZoneInfo(args.timezone)
        if args.demo:cfg.update(fixture='examples/library.json',collection_keys=['DEMO0001'])
        elif args.collection:cfg['collection_keys']=args.collection
        if args.list_collections:return {'collections':Zotero(cfg,root).all('collections')}
        if (root/'config.local.json').exists():raise ValueError('Configuration exists; edit config.local.json deliberately or use a separate demo vault')
        if not cfg['collection_keys']:raise ValueError('Use --list-collections, then --collection KEY --timezone Region/City; or --demo')
        if not root.is_dir():raise ValueError('Clone/open the template directory first')
        save(root/'config.local.json',cfg)
        return {'configured':str(root/'config.local.json'),'next':'doctor, then sync','demo':args.demo}
    vault=Vault(root)
    with vault.lock():
        if args.command=='doctor':return doctor(vault)
        if args.command=='sync':return vault.sync(args.dry_run)
        if args.command=='status':return {'last_sync':read_json(vault.private/'last-sync.json'), 'scheduler':read_json(vault.private/'scheduler-status.json'),
            'pending_note_transactions':len(list((vault.private/'pending').glob('*.json'))),'jobs':read_json(vault.private/'jobs.json',{})}
        if args.command=='convert':return addons.convert(vault,vault.item(args.item))
        if args.command=='index':return addons.index(vault,args.semantic)
        if args.command=='search':
            if not 1<=args.limit<=100:raise ValueError('Limit must be 1–100')
            return addons.search(vault,args.query,args.method,args.limit)
        if args.command=='scite':return addons.snapshot(vault,vault.item(args.item))
        if args.command=='summarize':
            addons.recover_publications(vault)
            if args.publish:
                if not args.token:raise ValueError('Publication requires the preparation --token')
                return addons.publish_summary(vault,args.token,read_json(args.publish),args.accept)
            if not args.item:raise ValueError('Supply a paper item key or citation key')
            item=vault.item(args.item)
            return addons.run_summary(vault,item,args.refresh,args.reason) if args.run else addons.prepare_summary(vault,item,args.refresh,args.reason)
        if args.command=='schedule':
            if args.action=='install':return scheduler.install(vault)
            if args.action in ('disable','uninstall'):return scheduler.install(vault,remove=True)
            if args.action in ('queue','retry'):
                if not args.item:raise ValueError('Use --item KEY')
                return scheduler.queue(vault,vault.item(args.item))
            if args.action=='status':return {'label':scheduler.label(vault),'config':vault.config['scheduler'],'last_run':read_json(vault.private/'scheduler-status.json')}
            return scheduler.tick(vault,check_only=args.action=='check')


def entry():
    try:
        result=main();print(json.dumps(result,ensure_ascii=False,indent=2))
        if result.get('issues') or result.get('ok') is False or result.get('state')=='failed':return 2
        return 0
    except (Exception,KeyboardInterrupt) as e:
        print(json.dumps({'error':str(e) or 'Interrupted; check status before retrying'},ensure_ascii=False));return 1
