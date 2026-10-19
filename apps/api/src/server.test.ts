import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createServer,request} from 'node:http';
import {once} from 'node:events';
import {createApp} from './server.js';
test('Node proxies live scientific response, rejects unknown routes and origins',async()=>{
  const scientific=createServer((req,res)=>{res.setHeader('content-type','application/json');res.end(JSON.stringify({status:'ok',path:req.url}))}).listen(0,'127.0.0.1');
  await once(scientific,'listening');const mlPort=(scientific.address() as {port:number}).port;
  const server=createApp(`http://127.0.0.1:${mlPort}`).listen(0,'127.0.0.1');await once(server,'listening');
  const port=(server.address() as {port:number}).port;const url=`http://127.0.0.1:${port}`;
  try{
    assert.equal((await (await fetch(url+'/api/health')).json()).path,'/health');
    assert.equal((await (await fetch(url+'/health')).json()).service,'SAMS application API');
    assert.equal((await (await fetch(url+'/api/reports/MODEL_CARD.md')).json()).path,'/reports/MODEL_CARD.md');
    assert.equal((await fetch(url+'/api/arbitrary')).status,404);
    assert.equal((await fetch(url+'/api/health',{headers:{origin:'https://untrusted.example'}})).status,403);
    const hostStatus=await new Promise<number|undefined>((resolve,reject)=>{const r=request(url+'/api/health',{headers:{host:'untrusted.example'}},res=>{res.resume();resolve(res.statusCode)});r.on('error',reject);r.end()});
    assert.equal(hostStatus,403);
    assert.equal((await fetch(url+'/api/predict',{method:'POST',headers:{'content-type':'application/json'},body:'{'})).status,400);
  }finally{server.closeAllConnections();scientific.closeAllConnections();server.close();scientific.close()}
});
test('Node gives actionable service error',async()=>{
  const server=createApp('http://127.0.0.1:1').listen(0,'127.0.0.1');await once(server,'listening');
  try{const res=await fetch(`http://127.0.0.1:${(server.address() as {port:number}).port}/api/health`);assert.equal(res.status,503);assert.match((await res.json()).detail,/Start FastAPI/)}finally{server.closeAllConnections();server.close()}
});
