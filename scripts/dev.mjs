import {spawn} from 'node:child_process';
const python = process.env.SAMS_PYTHON || (process.platform==='win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
const npm = process.platform==='win32' ? 'npm.cmd' : 'npm';
const children=[];
function launch(command,args,shell=false){
  const child=spawn(command,args,{stdio:'inherit',shell,windowsHide:true}); children.push(child);
  child.on('error',e=>{console.error(`SAMS startup failed: ${command}: ${e.message}. Complete README setup first.`);stop(1)});
  child.on('exit',code=>{if(code && !stopping)stop(code)});
}
let stopping=false;
function stop(code=0){if(stopping)return;stopping=true;for(const c of children)c.kill();process.exitCode=code;}
process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop());
launch(python,['-m','uvicorn','services.ml.app:app','--host','127.0.0.1','--port','8000']);
launch(npm,['run','dev','--workspace','apps/api'],process.platform==='win32');
launch(npm,['run','dev','--workspace','apps/web'],process.platform==='win32');
