import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from workflow.core import Vault,LOCAL,COLORS,read_json,save,sha,file_hash
from workflow.cli import ROOT,default_config,main
from workflow import addons,scheduler,scite

class Base(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  shutil.copytree(ROOT/'examples',self.root/'examples');shutil.copytree(ROOT/'templates',self.root/'templates')
  c=default_config();c.update(fixture='examples/library.json',collection_keys=['DEMO0001'])
  save(self.root/'config.local.json',c);self.v=Vault(self.root)
 def tearDown(self):self.tmp.cleanup()
 def sync(self):
  with self.v.lock():return self.v.sync()
 def first(self):return self.v.api.fixture['items'][0]
 def annotation(self):return next(i for i in self.v.api.fixture['items'] if i['data']['itemType']=='annotation')
 def note(self):return self.root/'zotero-notes/Example Topic/exampleReading2026.md'
 def source(self):
  self.sync();item=self.v.item('PAPER001');pdf=self.root/'examples/demonstration.pdf'
  text='{0}------------------------------------------------\n\nThis synthetic experiment has eight annotations.\nNo real people participated in the demonstration.\n'
  p=self.root/'sources/markdown/demo/paper.md';p.parent.mkdir(parents=True);p.write_text(text)
  r={'id':'source1','item':'PAPER001','attachment':'PDF00001','pdf':str(pdf),'pdf_hash':file_hash(pdf),'markdown':'sources/markdown/demo/paper.md',
     'files':{'sources/markdown/demo/paper.md':file_hash(p)},'page_count':1,'active':True}
  save(self.v.private/'sources.json',{'source1':r});return item,r
 def payload(self):return {**{k:'A clearly labelled fictional demonstration.' for k in addons.SECTIONS},'source_limits':'Synthetic example only.',
   'evidence':[{'section':k,'attachment':'PDF00001','page':1,'quote':'This synthetic experiment has eight annotations.'} for k in addons.SECTIONS]}

class SyncTests(Base):
 def test_base_and_idempotent(self):
  self.assertEqual(self.sync()['created'],3);before=self.note().read_bytes()
  self.assertEqual(self.sync()['unchanged'],3);self.assertEqual(before,self.note().read_bytes())
  self.assertTrue((self.root/'papers/exampleUnmarked2026.md').exists())
  self.assertFalse((self.root/'zotero-notes/exampleUnmarked2026.md').exists())
 def test_all_colors_notes_tags_exact_links(self):
  self.sync();text=self.note().read_text()
  for name,_ in COLORS.values():self.assertIn('('+name+')',text)
  self.assertIn('page=1&annotation=ANNOT000',text);self.assertIn('#method/useful',text)
  self.assertEqual(text.count('This fictional document helps'),1);self.assertIn('These notes concern this attachment',text)
 def test_local_review_survives_and_import_edit_conflicts(self):
  self.sync();self.note().write_text(self.note().read_text()+'\nMy local idea. #idea/project\n')
  self.annotation()['data']['annotationComment']='New upstream comment';self.sync()
  self.assertIn('My local idea',self.note().read_text());self.assertIn('New upstream comment',self.note().read_text())
  self.note().write_text(self.note().read_text().replace('New upstream comment','Edited imported region'))
  before=self.note().read_bytes();self.assertTrue(self.sync()['issues']);self.assertEqual(before,self.note().read_bytes())
 def test_deletion_and_move(self):
  self.sync();old=self.note();old.write_text(old.read_text()+'\nKeep this local text\n')
  self.v.api.fixture['items']=[i for i in self.v.api.fixture['items'] if i['data']['itemType']!='annotation']
  self.first()['data']['collections']=['DEMO0001'];self.sync()
  new=self.root/'zotero-notes/exampleReading2026.md'
  self.assertIn('Keep this local text',new.read_text());self.assertNotIn('zotero-annotation:',new.read_text());self.assertIn('Moved to',old.read_text())
 def test_unmanaged_note_and_duplicate_key(self):
  self.note().parent.mkdir(parents=True);self.note().write_text('Human writing')
  self.assertTrue(self.sync()['issues']);self.assertEqual(self.note().read_text(),'Human writing')
  self.v.api.fixture['items'][-1]['data']['citationKey']='exampleReading2026'
  other=copy.deepcopy(self.first());other['key']='OTHER001';self.v.api.fixture['items'].append(other)
  self.assertTrue(any('Duplicate citation' in x for x in self.sync()['issues']))
 def test_missing_citekey(self):
  self.first()['data'].pop('citationKey');self.assertTrue(any('citation key' in x for x in self.sync()['issues']))
 def test_unknown_and_three_way_status_conflict(self):
  self.sync();h=read_json(self.v.private/'reading-history.json')['items'];self.assertEqual(h['PAPER001']['reading_status'],'unread');self.assertEqual(h['PAPER002']['reading_status'],'unknown')
  self.first()['data']['tags']=[{'tag':'⏳'}];self.sync();h=read_json(self.v.private/'reading-history.json')['items']['PAPER001'];self.assertEqual(h['reading_status'],'reading');self.assertIsNotNone(h['reading_started_on'])
  self.first()['data']['tags']=[{'tag':'✅'}];self.sync();h=read_json(self.v.private/'reading-history.json')['items']['PAPER001'];self.assertEqual(h['read_date_basis'],'observed-tag-change')
  self.first()['data']['tags']=[{'tag':'✅'},{'tag':'reading/unread'}];self.sync();self.assertEqual(read_json(self.v.private/'reading-history.json')['items']['PAPER001']['reading_status'],'conflict')
 def test_baseline_date_unknown(self):
  self.first()['data']['tags']=[{'tag':'✅'}];self.sync();self.assertIsNone(read_json(self.v.private/'reading-history.json')['items']['PAPER001']['read_on'])
 def test_multiple_collections_one_unfiled_note(self):
  self.v.api.fixture['collections'].append({'key':'DEMO0003','data':{'name':'Other Topic','parentCollection':'DEMO0001'}})
  self.first()['data']['collections']=['DEMO0002','DEMO0003'];self.sync()
  self.assertTrue((self.root/'zotero-notes/_unfiled/exampleReading2026.md').exists())
 def test_dry_run_no_content_or_history(self):
  with self.v.lock():self.v.sync(True)
  self.assertFalse(self.note().exists());self.assertFalse((self.v.private/'reading-history.json').exists())
 def test_citekey_change_keeps_path(self):
  self.sync();self.first()['data']['citationKey']='renamed2026';self.sync();self.assertTrue(self.note().exists());self.assertIn('renamed2026',self.note().read_text())
 def test_server_change_and_scope_fail_closed(self):
  self.sync();catalog=read_json(self.v.private/'catalog.json');catalog['server']='other';save(self.v.private/'catalog.json',catalog)
  with self.assertRaisesRegex(ValueError,'Different Zotero'):self.sync()
  self.v.config['collection_keys']=['MISSING']
  with self.assertRaises(ValueError):self.sync()
 def test_removed_item_preserved_but_inactive(self):
  self.sync();self.first()['data']['collections']=[];self.sync();self.assertTrue(self.note().exists());self.assertFalse(read_json(self.v.private/'catalog.json')['items']['PAPER001']['active'])
 def test_interrupted_journal_recovery_preserves_latest_local(self):
  self.sync();before=self.v.owned()['PAPER001:annotations'];generated,local=self.note().read_text().split(LOCAL)
  tx={'id':'PAPER001:annotations','path':before['path'],'before':before,'generated':generated.replace('Context for this exercise.','Changed context.')}
  journal=self.v.private/'pending/recovery.json';save(journal,tx)
  self.note().write_text(tx['generated']+LOCAL+local+'\nAdded after interruption\n')
  self.v.recover();self.assertFalse(journal.exists());self.assertIn('Added after interruption',self.note().read_text())
  self.assertEqual(self.v.owned()['PAPER001:annotations']['hash'],sha(tx['generated']))
 def test_scope_and_route_traversal(self):
  self.v.config['routes']['PAPER001']='../../../../outside';self.assertTrue(self.sync()['issues'])
 def test_nested_lock_blocks(self):
  with self.v.lock():
   with self.assertRaises(RuntimeError):
    with Vault(self.root).lock():pass

class EvidenceTests(Base):
 def test_keyword_search_excludes_annotations_and_changed_sources(self):
  item,r=self.source();result=addons.search(self.v,'eight annotations');self.assertEqual(len(result['results']),1)
  self.assertEqual(result['results'][0]['page'],1)
  self.v.path(r['markdown']).write_text('changed');result=addons.search(self.v,'eight');self.assertFalse(result['results']);self.assertTrue(result['issues'])
 def test_pdf_changed(self):
  item,r=self.source();Path(r['pdf']).write_bytes(b'changed')
  with self.assertRaises(ValueError):addons.prepare_summary(self.v,item)
 def test_summary_publish_and_refresh_review(self):
  item,r=self.source();packet=addons.prepare_summary(self.v,item);published=addons.publish_summary(self.v,packet['token'],self.payload());self.assertEqual(published['state'],'published')
  with self.assertRaises(ValueError):addons.prepare_summary(self.v,item)
  packet=addons.prepare_summary(self.v,item,True,'Improve explanation')
  payload=self.payload();payload['overview']='A revised demonstration summary.'
  before=self.v.path(published['path']).read_bytes()
  self.assertEqual(addons.publish_summary(self.v,packet['token'],payload)['state'],'proposed');self.assertEqual(before,self.v.path(published['path']).read_bytes())
  self.assertEqual(addons.publish_summary(self.v,packet['token'],payload,True)['state'],'published')
 def test_publication_rejects_wrong_quote_page_and_stale_base(self):
  item,r=self.source();packet=addons.prepare_summary(self.v,item);p=self.payload();p['evidence'][0]['quote']='A quotation that does not exist.'
  with self.assertRaises(ValueError):addons.publish_summary(self.v,packet['token'],p)
  p=self.payload();p['evidence'][0]['page']=8
  with self.assertRaises(ValueError):addons.publish_summary(self.v,packet['token'],p)
  path=self.root/'notes/exampleReading2026.md';path.parent.mkdir();path.write_text('human work')
  with self.assertRaisesRegex(ValueError,'changed since'):addons.publish_summary(self.v,packet['token'],self.payload())
 def test_summary_edit_excludes_retrieval(self):
  item,r=self.source();packet=addons.prepare_summary(self.v,item);pub=addons.publish_summary(self.v,packet['token'],self.payload())
  self.v.path(pub['path']).write_text('Edited');docs,issues=addons.documents(self.v);self.assertTrue(issues);self.assertEqual([d['kind'] for d in docs],['source'])
 def test_summary_recovery(self):
  item,r=self.source();packet=addons.prepare_summary(self.v,item);addons.publish_summary(self.v,packet['token'],self.payload())
  job=self.v.private/'summary-jobs'/packet['token'];(job/'committed.json').unlink();(self.v.private/'summaries.json').unlink()
  addons.recover_publications(self.v);self.assertTrue((job/'committed.json').exists());self.assertIn(item['key'],read_json(self.v.private/'summaries.json'))
 def test_summary_needs_all_sections_and_main_selection(self):
  item,r=self.source();packet=addons.prepare_summary(self.v,item);p=self.payload();p['evidence']=p['evidence'][:1]
  with self.assertRaises(ValueError):addons.publish_summary(self.v,packet['token'],p)
 def test_scite_missing_doi_failure_and_previous_retained(self):
  self.assertEqual(scite.retrieve('')['status'],'no-doi')
  with patch('urllib.request.urlopen',side_effect=OSError('offline')):self.assertEqual(scite.retrieve('10.1234/example')['status'],'unavailable')
  good={'schema_version':1,'doi':'10.1234/example','report_url':scite.report_url('10.1234/example'),'status':'retrieved','checked_at':'2026-01-01T00:00:00Z','retrieved_at':'2026-01-01T00:00:00Z','counts':{k:0 for k in scite.COUNTS},'reason':None}
  bad=dict(good,status='unavailable',counts=None,retrieved_at=None,checked_at='2026-02-01T00:00:00Z',reason='offline')
  merged=scite.merge(good,bad,good['doi']);self.assertEqual(merged['retrieved_at'],good['retrieved_at']);self.assertIn('last_attempt',merged)
 def test_no_marker_is_actionable(self):
  self.sync()
  with self.assertRaisesRegex(ValueError,'disabled'):addons.convert(self.v,self.v.item('PAPER001'))

class SchedulerTests(Base):
 def test_idle_baseline_no_ai(self):
  with patch.object(addons,'run_summary') as run:
   self.assertEqual(scheduler.tick(self.v)['state'],'idle');run.assert_not_called()
 def test_queue_completion_and_quiet_repeat(self):
  self.sync();scheduler.queue(self.v,self.v.item('PAPER001'))
  with patch.object(addons,'convert') as convert,patch.object(addons,'index'),patch.object(scheduler,'notify'):
   self.assertEqual(scheduler.tick(self.v,True)['state'],'actionable');convert.assert_not_called()
   self.assertEqual(scheduler.tick(self.v)['state'],'complete');self.assertEqual(scheduler.tick(self.v)['state'],'idle');self.assertEqual(convert.call_count,1)
 def test_failed_job_backoff_and_retry(self):
  self.sync();scheduler.queue(self.v,self.v.item('PAPER001'))
  with patch.object(addons,'convert',side_effect=ValueError('no PDF')),patch.object(scheduler,'notify'):
   self.assertEqual(scheduler.tick(self.v)['state'],'failed');self.assertEqual(scheduler.tick(self.v)['state'],'retry-wait')
  scheduler.queue(self.v,self.v.item('PAPER001'));self.assertEqual(scheduler.tick(self.v,True)['state'],'actionable')
 def test_existing_summary_not_overwritten(self):
  item,r=self.source();packet=addons.prepare_summary(self.v,item);addons.publish_summary(self.v,packet['token'],self.payload());scheduler.queue(self.v,item)
  self.v.config['scheduler']['mode']='summary'
  with patch.object(addons,'convert'),patch.object(addons,'run_summary') as run,patch.object(scheduler,'notify'):
   self.assertEqual(scheduler.tick(self.v)['state'],'failed');run.assert_not_called()


class AdditionalRecoveryTests(Base):
 def test_move_back_through_owned_redirect(self):
  self.sync();self.note().write_text(self.note().read_text()+'\nKeep local review')
  self.first()['data']['collections']=['DEMO0001'];self.assertFalse(self.sync()['issues'])
  self.first()['data']['collections']=['DEMO0002'];self.assertFalse(self.sync()['issues']);self.assertIn('Keep local review',self.note().read_text())
 def test_route_cannot_cross_into_other_vault_directory(self):
  self.v.config['routes']['PAPER001']='../notes';self.assertTrue(self.sync()['issues'])
 def test_published_interrupted_job_repairs_index_without_ai(self):
  item,r=self.source();packet=addons.prepare_summary(self.v,item);addons.publish_summary(self.v,packet['token'],self.payload())
  self.v.config['scheduler']['mode']='summary'
  save(self.v.private/'jobs.json',{'PAPER001':{'state':'running','queued':True,'attempts':1,'retry_after':0,'started_at':'2000-01-01T00:00:00+00:00'}})
  with patch.object(addons,'convert'),patch.object(addons,'index'),patch.object(addons,'run_summary') as run,patch.object(scheduler,'notify'):
   self.assertEqual(scheduler.tick(self.v)['state'],'complete');run.assert_not_called()
 def test_existing_child_guard_blocks(self):
  import os,subprocess
  from workflow.core import run_child
  self.v.private.mkdir();identity=subprocess.check_output(['/bin/ps','-p',str(os.getpid()),'-o','lstart=,command='],text=True).strip()
  save(self.v.private/'child-process.json',{'pid':os.getpid(),'identity':identity})
  with tempfile.TemporaryFile(mode='w') as log:
   with self.assertRaisesRegex(ValueError,'still be running'):run_child(self.v,['true'],log,1)

if __name__=='__main__':unittest.main()
