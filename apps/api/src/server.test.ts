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
  try{const res=await fetch(`http://127.0.0.1:${(server.address() as {port:number}).port}/api/health`);assert.equal(res.status,503);assert.match((await res.json()).detail,/Check ML_URL/)}finally{server.closeAllConnections();server.close()}
});

test('hosted API validates configuration, blocks writes and forwards server-only token',async()=>{
  const keys=['SAMS_DEPLOYMENT','ML_SERVICE_TOKEN','WEB_ORIGIN','RENDER_EXTERNAL_HOSTNAME'];
  const previous=Object.fromEntries(keys.map(k=>[k,process.env[k]]));
  const originalFetch=globalThis.fetch;
  let server:ReturnType<typeof createServer>|undefined;
  try{
    process.env.SAMS_DEPLOYMENT='production';
    process.env.WEB_ORIGIN='https://sams.example';
    process.env.ML_SERVICE_TOKEN='x'.repeat(32);
    process.env.RENDER_EXTERNAL_HOSTNAME='sams-api.onrender.com';
    assert.throws(()=>createApp('http://127.0.0.1:8000'),/HTTPS ML_URL/);
    let forwarded=0;
    globalThis.fetch=(async(input,init)=>{
      if(String(input).startsWith('https://sams-ml.example')){
        forwarded++;
        assert.equal((init?.headers as Record<string,string>)['x-sams-service-token'],'x'.repeat(32));
        return new Response(JSON.stringify({status:'ok'}),{headers:{'content-type':'application/json'}});
      }
      return originalFetch(input,init);
    }) as typeof fetch;
    server=createApp('https://sams-ml.example').listen(0,'127.0.0.1');await once(server,'listening');
    const url=`http://127.0.0.1:${(server.address() as {port:number}).port}`;
    assert.equal((await fetch(url+'/api/performance',{headers:{origin:'https://sams.example'}})).status,200);
    assert.equal((await fetch(url+'/api/application-health')).status,200);
    assert.equal((await fetch(url+'/api/jobs',{method:'POST',headers:{'content-type':'application/json'},body:'{"kind":"train"}'})).status,403);
    assert.equal((await fetch(url+'/api/uploads',{method:'POST'})).status,403);
    assert.equal((await fetch(url+'/api/ready',{headers:{origin:'https://wrong.example'}})).status,403);
    assert.equal(forwarded,1);
  }finally{
    globalThis.fetch=originalFetch;
    server?.closeAllConnections();server?.close();
    for(const k of keys){if(previous[k]===undefined)delete process.env[k];else process.env[k]=previous[k];}
  }
});
