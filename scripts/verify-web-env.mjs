if(process.env.VERCEL){
  const value=process.env.VITE_API_BASE_URL;
  let url;
  try{url=new URL(value);}catch{throw new Error('Set VITE_API_BASE_URL to the Render API HTTPS URL ending /api');}
  if(url.protocol!=='https:'||url.username||url.password||url.search||url.hash||url.pathname!=='/api'||['localhost','127.0.0.1'].includes(url.hostname))
    throw new Error('VITE_API_BASE_URL must be a public HTTPS API URL ending /api, without credentials');
}
