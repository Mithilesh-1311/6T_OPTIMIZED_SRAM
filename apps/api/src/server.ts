import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import {fileURLToPath} from 'node:url';
dotenv.config({path:fileURLToPath(new URL('../.env',import.meta.url))});
export function createApp(ml=process.env.ML_URL || 'http://127.0.0.1:8000') {
  const app=express();
  app.disable('x-powered-by');
  const origin=process.env.WEB_ORIGIN || 'http://127.0.0.1:5173';
  app.use((req,res,next)=>{
    res.setHeader('X-Content-Type-Options','nosniff');
    if(req.headers.origin && req.headers.origin!==origin) {res.status(403).json({detail:'Origin is not allowed'});return;}
    const host=req.hostname;
    if(!['127.0.0.1','localhost','::1'].includes(host)){res.status(403).json({detail:'Local host required'});return;}
    next();
  });
  app.use(cors({origin,methods:['GET','POST']}));
  app.get('/health',(_req,res)=>res.json({status:'ok',service:'SAMS application API'}));
  app.use(express.json({limit:'32kb'}));
  const get=/^\/(health|overview|audit|experiments|evaluation|dictionary|jobs|jobs\/[a-f0-9]{32}|waveforms\/[a-f0-9]{16}|reports\/[A-Za-z0-9_.-]+)$/;
  const post=/^\/(predict|compare|jobs)$/;
  app.use('/api', async(req,res)=>{
    if(!(req.method==='GET' && get.test(req.path)) && !(req.method==='POST' && post.test(req.path)) && !(req.method==='POST' && req.path==='/uploads')){
      res.status(404).json({detail:'Unknown SAMS endpoint'});return;
    }
    try {
      let body: BodyInit | undefined;
      let headers:Record<string,string>={};
      if(req.path==='/uploads') {
        const contentType=req.headers['content-type'] || '';
        if(!contentType.startsWith('multipart/form-data;')){res.status(415).json({detail:'Multipart upload required'});return;}
        const chunks:Buffer[]=[];let bytes=0;
        for await(const chunk of req){bytes+=chunk.length;if(bytes>64*1024*1024+8192){res.status(413).json({detail:'Maximum upload is 64 MiB'});return;}chunks.push(chunk);}
        body=Buffer.concat(chunks);headers={'content-type':contentType};
      }else if(req.method==='POST'){body=JSON.stringify(req.body);headers={'content-type':'application/json'};}
      const response=await fetch(`${ml}${req.url}`,{method:req.method,headers,body,signal:AbortSignal.timeout(120000)});
      res.status(response.status);
      for(const h of ['content-type','content-disposition']){const v=response.headers.get(h);if(v)res.setHeader(h,v);}
      res.send(Buffer.from(await response.arrayBuffer()));
    }catch {res.status(503).json({detail:'Scientific service unavailable. Start FastAPI at 127.0.0.1:8000.'});}
  });
  app.use((err: {status?:number},_req:express.Request,res:express.Response,_next:express.NextFunction)=>{
    res.status(err.status || 500).json({detail:err.status===413?'Request body too large':'Invalid request'});
  });
  return app;
}
if(process.argv[1] && fileURLToPath(import.meta.url)===process.argv[1]){
  const port=Number(process.env.PORT || 3001);
  const server=createApp().listen(port,'127.0.0.1',()=>console.log(`SAMS API http://127.0.0.1:${port}`));
  server.on('error',e=>{console.error(`SAMS API startup failed: ${e.message}`);process.exitCode=1;});
}
