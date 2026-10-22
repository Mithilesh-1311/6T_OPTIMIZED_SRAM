import {createContext, useContext} from 'react';
import type {Audit, Evaluation, Job, Run} from './api';

export type Connection = 'checking' | 'connected' | 'unavailable';
export type ServiceState = {api: Connection; ml: Connection; processingEnabled?:boolean; checkedAt: string | null};
export type InferenceState = {
  state: 'idle' | 'running' | 'completed' | 'failed' | 'unavailable';
  detail: string;
  at?: string;
};
export type Evidence = {
  audit: Audit;
  runs: Run[];
  evaluation: Evaluation;
  reload: () => void;
  services: ServiceState;
  jobs: Job[];
  jobsError: string;
  inference: InferenceState;
  setInference: (state: InferenceState) => void;
};
export const Context = createContext<Evidence | null>(null);
export const useEvidence = () => useContext(Context)!;
