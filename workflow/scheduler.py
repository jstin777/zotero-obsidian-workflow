"""One local worker per tick; no AI polling on idle runs."""
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import time
from .core import now, read_json, save, sha
from . import addons


def label(vault): return 'org.zotero-obsidian.workflow.' + sha(str(vault.root))[:12]


def install(vault, remove=False):
    if sys.platform != 'darwin': raise ValueError('LaunchAgent installation is supported on macOS only')
    name=label(vault); target=Path.home()/'Library/LaunchAgents'/(name+'.plist');domain='gui/'+str(os.getuid())
    if remove:
        subprocess.run(['/bin/launchctl','bootout',domain+'/'+name],capture_output=True)
        target.unlink(missing_ok=True);vault.config['scheduler']['enabled']=False;save(vault.config_path,vault.config)
        return {'state':'disabled','data_preserved':True}
    if not vault.config.get('marker',{}).get('enabled'): raise ValueError('Configure Marker before enabling scheduled processing')
    addons.executable(vault,vault.config['marker']['executable'])
    if vault.config['scheduler']['mode']=='summary':
        if not vault.config.get('codex',{}).get('enabled'):raise ValueError('Enable Codex for summary mode')
        addons.executable(vault,vault.config['codex']['executable'])
    logs=vault.private/'logs';logs.mkdir(parents=True,exist_ok=True)
    plist={'Label':name,'ProgramArguments':[sys.executable,str(vault.root/'tools/workflow.py'),'--vault',str(vault.root),'schedule','run'],
        'WorkingDirectory':str(vault.root),'StartInterval':vault.config['scheduler'].get('interval_seconds',3600),
        'RunAtLoad':False,'ProcessType':'Background','EnvironmentVariables':{'PATH':os.environ.get('PATH','/usr/bin:/bin')},
        'StandardOutPath':str(logs/'scheduler.stdout.log'),'StandardErrorPath':str(logs/'scheduler.stderr.log')}
    target.parent.mkdir(parents=True,exist_ok=True)
    staged=vault.private/'launchagent.plist';staged.write_bytes(plistlib.dumps(plist))
    subprocess.run(['/usr/bin/plutil','-lint',str(staged)],check=True,capture_output=True)
    subprocess.run(['/bin/launchctl','bootout',domain+'/'+name],capture_output=True)
    target.write_bytes(staged.read_bytes())
    subprocess.run(['/bin/launchctl','bootstrap',domain,str(target)],check=True,capture_output=True)
    vault.config['scheduler']['enabled']=True;save(vault.config_path,vault.config)
    return {'state':'enabled','label':name,'interval_seconds':plist['StartInterval']}


def queue(vault,item):
    jobs=read_json(vault.private/'jobs.json',{})
    jobs[item['key']]={'queued':True,'attempts':0,'retry_after':0,'state':'queued'}
    save(vault.private/'jobs.json',jobs)
    return {'queued':item['key']}


def notify(vault,key,message):
    cfg=vault.config.get('scheduler',{})
    if not cfg.get('notifications',True) or sys.platform!='darwin':return
    previous=read_json(vault.private/'notifications.json',{})
    if previous.get(key)==message:return
    script='on run argv\ndisplay notification (item 1 of argv) with title "Zotero–Obsidian Workflow"\nend run'
    result=subprocess.run(['/usr/bin/osascript','-e',script,message],capture_output=True,timeout=15)
    previous[key]=message;save(vault.private/'notifications.json',previous)
    if result.returncode: save(vault.private/'notification-error.json',{'at':now(),'error':result.stderr.decode(errors='replace')})


def tick(vault,check_only=False):
    addons.recover_publications(vault)
    sync=vault.sync()
    jobs=read_json(vault.private/'jobs.json',{})
    catalog=read_json(vault.private/'catalog.json',{})
    publications=read_json(vault.private/'summaries.json',{})
    candidates=[];waiting=[]
    for item in catalog.get('items',{}).values():
        if not item['active']:continue
        job=jobs.get(item['key'],{})
        if job.get('state')=='complete' and not job.get('queued'):continue
        if item['key'] in publications and not job.get('queued'):continue
        if item['deferred'] and not job.get('queued'):continue
        if job.get('attempts',0)>=3 or job.get('retry_after',0)>time.time():waiting.append(item['key']);continue
        candidates.append(item)
    if not candidates:
        result={'state':'retry-wait' if waiting else 'idle','waiting':waiting,'ai_invoked':False,'sync_issues':sync['issues']}
    elif check_only:
        result={'state':'actionable','item':candidates[0]['key'],'ai_invoked':False,'sync_issues':sync['issues']}
    else:
        item=candidates[0];key=item['key'];job=jobs.get(key,{})
        # Persist attempt before starting so interruptions count toward bounded retry.
        prior_started=job.get('started_at')
        job.update(attempts=job.get('attempts',0)+1,retry_after=time.time()+21600,state='running',queued=True,started_at=now())
        jobs[key]=job;save(vault.private/'jobs.json',jobs)
        result={'item':key,'ai_invoked':False}
        try:
            addons.convert(vault,item)
            if vault.config['scheduler']['mode']=='summary':
                if key in publications:
                    if not prior_started or publications[key]['published_at'] < prior_started:
                        raise ValueError('Existing summary needs explicit reviewed refresh; scheduling cannot replace it')
                    addons.summary_current(vault,publications[key])
                else:
                    result['ai_invoked']=True;addons.run_summary(vault,item)
            addons.index(vault,semantic=vault.config.get('qmd',{}).get('enabled',False))
            job.update(state='complete',queued=False,completed_at=now())
            result['state']='complete';notify(vault,key,item['citekey']+' processed')
        except Exception as error:
            job.update(state='failed',error=str(error));result.update(state='failed',error=str(error))
            notify(vault,key,item['citekey']+': '+str(error))
        save(vault.private/'jobs.json',jobs)
    if not check_only:save(vault.private/'scheduler-status.json',dict(result,checked_at=now()))
    return result
