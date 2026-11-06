const {Plugin,Notice,PluginSettingTab,Setting}=require('obsidian');
const {execFile}=require('child_process');
const {existsSync}=require('fs');
const path=require('path');
module.exports=class ReadingSync extends Plugin{
 async onload(){
  this.settings=Object.assign({automatic:true},await this.loadData());this.running=false;this.lastError='';
  this.addCommand({id:'sync-now',name:'Sync Zotero reading notes now',callback:()=>this.sync(true)});
  this.addSettingTab(new class extends PluginSettingTab{constructor(app,plugin){super(app,plugin);this.plugin=plugin}display(){this.containerEl.empty();new Setting(this.containerEl).setName('Automatic sync').setDesc('Sync on vault opening and every five minutes after setup.').addToggle(t=>t.setValue(this.plugin.settings.automatic).onChange(async v=>{this.plugin.settings.automatic=v;await this.plugin.saveData(this.plugin.settings)}))}}(this.app,this));
  this.app.workspace.onLayoutReady(()=>{if(this.settings.automatic)this.sync(false)});
  this.registerInterval(window.setInterval(()=>{if(this.settings.automatic)this.sync(false)},300000));
 }
 sync(manual){
  if(this.running)return;
  const root=this.app.vault.adapter.getBasePath();
  if(!existsSync(path.join(root,'config.local.json'))){if(manual)new Notice('Complete docs/setup.md before syncing.');return;}
  this.running=true;
  execFile(path.join(root,'.venv/bin/python'),[path.join(root,'tools/workflow.py'),'sync'],{timeout:240000,maxBuffer:4*1024*1024},(error,stdout,stderr)=>{
   this.running=false;let r;
   try{r=JSON.parse(stdout)}catch(_){r={error:stderr||String(error)}}
   const issue=r.error||(r.issues||[]).join('\n')||(error?String(error):'');
   if(issue){if(manual||issue!==this.lastError)new Notice('Zotero sync needs attention: '+issue,12000);this.lastError=issue;return;}
   this.lastError='';const count=(r.created||0)+(r.updated||0)+(r.moved||0);
   if(manual||count)new Notice(`Zotero: ${count} files changed; ${r.unchanged||0} unchanged.`);
  });
 }
};
