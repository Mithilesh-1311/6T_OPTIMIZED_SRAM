export type Point={x:number;y:number};
export type RawFile={id:string;file:string;sha256:string;bytes:number;decision:string;reason:string;rows?:number;flags:string[];signals:{name:string;unit:string;axis_unit:string;samples:number;flags:string[]}[]};
export type Run={id:string;file:string;sha256:string;kind:string;vdd_v:number;temp_c:number;mode:number|null;bit:number|null;vret_v:number;group:string;metrics:Record<string,number|boolean>;flags:string[];events:Record<string,{wl_rise_ns:number;q_cross_ns:number;wl_fall_ns:number;delay_ps:number}>;windows_ns:Record<string,unknown>;butterfly?:{snm_mv:number;lobes:{side_mv:number;square:number[][]}[];curves:{a:number[][];b:number[][]}}};
export type ModelScore={mae:number;rmse:number;r2:number|null;within_10pct:number;individual:{id:string;measured:number;predicted:number;error:number;group:string}[]};
export type Target={n_cases:number;n_groups:number;final_test_cases?:number;status:string;features:string[];models:Record<string,ModelScore>;deployed_model?:string;domain?:Record<string,number[]>;residual_envelope?:number;reason?:string;validation:string;uncertainty?:string;interpolation_baseline?:{supported_cases:number;total_cases:number;status:string}};
export type Evaluation={model_version:string;dataset_version:string;metric_policy:string;selection_policy:string;targets:Record<string,Target>;target_90_established:boolean;reporting?:Performance;reporting_error?:string};
export type Audit={dataset_version:string;files:RawFile[];counts:Record<string,number>;accepted_waveform_rows:number;provenance_limit:string;exact_duplicates:string[][];shared_signal_groups:unknown[]};
export type Job={id:string;kind:string;state:string;stage:string;detail:string;started:string;ended:string|null};
export const labels:Record<string,string>={write0_ps:'Write 0 delay',write1_ps:'Write 1 delay',active_energy_fj:'Active energy',quiet_power_uw:'Quiet retention power',hold_snm_mv:'Hold SNM',read_snm_mv:'Read SNM',active_power_uw:'Active mean power',sequence_energy_fj:'Entry / hold / wake energy',transition_excess_fj:'Excess over quiet baseline',state_survived:'State survived'};
export const units:Record<string,string>={write0_ps:'ps',write1_ps:'ps',active_energy_fj:'fJ',quiet_power_uw:'µW',hold_snm_mv:'mV',read_snm_mv:'mV',active_power_uw:'µW',sequence_energy_fj:'fJ',transition_excess_fj:'fJ'};
export const featureLabels:Record<string,string>={vdd_v:'Main / cell supply (V)',vret_v:'Retention supply (V)',temp_c:'Temperature (°C)',mode:'Wordline mode',bit:'Stored state'};
export const kinds:Record<string,string>={active:'Active operation',active_hold:'Active hold',retention:'Retention',hold_snm:'Hold SNM',read_snm:'Read SNM'};
export function fmt(value:unknown,digits=3):string{if(value===null || value===undefined)return 'Unavailable';if(typeof value==='boolean')return value?'Pass':'Fail';return typeof value==='number'?value.toLocaleString(undefined,{maximumFractionDigits:digits}):String(value);}
export async function api<T>(path:string,body?:unknown):Promise<T>{
  const r=await fetch(apiUrl(path),body===undefined?{}:{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));return data;
}

export type PerformanceScore={passing:number;evaluated:number;percentage:number;mae:number;rmse:number};
export type Performance={method:string;status:string;policy:string;model_version:string;dataset_version:string;targets:Record<string,{status:string;groups:number;absolute_tolerance_floor:number;final_test_cases:number;final_test_status:string;deployed_model:string;models:Record<string,PerformanceScore>}>};
// Display never rounds a value below 90 upward across the threshold.
export function percentage(value:number|undefined):string{return value===undefined?'Not evaluated':`${Math.floor(value*10000)/10000}%`;}
export function apiUrl(path:string){return `${import.meta.env.VITE_API_BASE_URL || '/api'}/${path}`;}
