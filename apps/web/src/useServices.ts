import {useEffect, useState} from 'react';
import {apiUrl,type Job} from './api';
import type {Connection, ServiceState} from './evidence';

const initial: ServiceState = {api:'checking', ml:'checking', checkedAt:null};

export function useServices(revision: number) {
  const [services, setServices] = useState(initial);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobsError, setJobsError] = useState('');
  useEffect(() => {
    let mounted = true;
    let timer: ReturnType<typeof setTimeout>;
    const controllers = new Set<AbortController>();
    setServices(s => ({...s,api:'checking',ml:'checking'}));
    async function request(path:string) {
      const controller = new AbortController();
      controllers.add(controller);
      const timeout = setTimeout(() => controller.abort(), 5000);
      try {
        const response = await fetch(apiUrl(path),{signal:controller.signal});
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } finally { clearTimeout(timeout); controllers.delete(controller); }
    }
    async function poll() {
      const [node, ml, jobResult] = await Promise.allSettled([
        request('application-health'), request('health'), request('jobs'),
      ]);
      if (!mounted) return;
      const connection = (result: PromiseSettledResult<{status?:string}>): Connection => result.status==='fulfilled'&&result.value?.status==='ok'?'connected':'unavailable';
      setServices({api:connection(node),ml:connection(ml),checkedAt:new Date().toISOString(),processingEnabled:ml.status==='fulfilled'&&ml.value.processing_enabled===true});
      const storedJobs=jobResult.status==='fulfilled'&&Array.isArray(jobResult.value)?jobResult.value as Job[]:null;
      if (storedJobs) {setJobs(storedJobs);setJobsError('');}
      else {setJobs([]);setJobsError('Processing records unavailable. Reconnect to check job state.');}
      const busy = storedJobs?.some(j=>j.state==='running'||j.state==='queued');
      timer=setTimeout(()=>void poll(),busy?1500:15000);
    }
    void poll();
    return () => {mounted=false;clearTimeout(timer);controllers.forEach(c=>c.abort());};
  },[revision]);
  return {services,jobs,jobsError};
}
