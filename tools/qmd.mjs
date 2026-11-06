import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {join} from 'node:path';
const r=JSON.parse(readFileSync(0,'utf8'));
console.log=(...a)=>console.error(...a);
const {createStore}=await import(pathToFileURL(join(r.runtime,'sdk/dist/index.js')));
const store=await createStore({dbPath:join(r.root,'index.sqlite'),config:{collections:{evidence:{path:join(r.root,'projections'),pattern:'*.md'}}}});
try {
  if(r.reindex){await store.update();await store.embed();const h=await store.getIndexHealth();if(h.needsEmbedding>0)throw new Error('Some passages could not be embedded');}
  let results=[];
  if(r.command==='semantic')results=await store.searchVector(r.query,{limit:30,collection:'evidence'});
  if(r.command==='hybrid')results=await store.search({query:r.query,limit:30,collections:['evidence']});
  process.stdout.write(JSON.stringify({results}));
}finally{await store.close();}
