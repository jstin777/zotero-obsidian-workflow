const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');const path=require('node:path');
let commands=[],settingsTab,notices=[],calls=0,exists=true,reply=null;
class Plugin{
 async loadData(){return null} async saveData(data){this.saved=data}
 addCommand(c){commands.push(c)}addSettingTab(t){settingsTab=t}registerInterval(){}
}
class PluginSettingTab{constructor(app){this.app=app;this.containerEl={empty(){}}}}
class Setting{setName(){return this}setDesc(){return this}addToggle(fn){fn({setValue(){return this},onChange(f){this.callback=f;return this}});return this}}
const sandbox={module:{exports:{}},console,window:{setInterval(){}},require(name){
 if(name==='obsidian')return {Plugin,PluginSettingTab,Setting,Notice:class{constructor(s){notices.push(s)}}};
 if(name==='path')return path;
 if(name==='fs')return {existsSync(){return exists}};
 if(name==='child_process')return {execFile(bin,args,opts,done){calls++;reply=()=>done(null,JSON.stringify({created:1,unchanged:2}), '');}};
 throw new Error(name);
}};
vm.runInNewContext(fs.readFileSync('.obsidian/plugins/zotero-reading-sync/main.js','utf8'),sandbox);
(async()=>{
 const plugin=new sandbox.module.exports();plugin.app={vault:{adapter:{getBasePath(){return '/synthetic/vault'}}},workspace:{onLayoutReady(fn){this.ready=fn}}};
 await plugin.onload();assert.equal(commands.length,1);settingsTab.display();
 exists=false;plugin.sync(false);assert.equal(calls,0);plugin.sync(true);assert.match(notices.pop(),/setup/);
 exists=true;plugin.sync(true);plugin.sync(true);assert.equal(calls,1);reply();assert.equal(plugin.running,false);assert.match(notices.pop(),/1 files changed/);
 console.log('Plugin checks passed: settings, missing setup, overlap guard and successful sync.');
})().catch(e=>{console.error(e);process.exitCode=1});
