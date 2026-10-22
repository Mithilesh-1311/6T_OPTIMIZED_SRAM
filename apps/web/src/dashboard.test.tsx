import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {renderToStaticMarkup} from 'react-dom/server';
import {MemoryRouter} from 'react-router-dom';
import {percentage,units,featureLabels,type Audit,type Evaluation,type Run,type Job} from './api';
import {ValidationCard} from './ValidationCard';
import {condition,selectedMetrics,processingStages} from './dashboard';
import {measurementWindows,signalColor} from './Plot';
import {Context,type Evidence} from './evidence';
import {CommandCentre} from './CommandCentre';

const read=(file:string)=>JSON.parse(readFileSync(new URL(`../../../data/derived/${file}.json`,import.meta.url),'utf8'));
const audit:Audit=read('audit');
const runs:Run[]=read('experiments');
const evaluation:Evaluation={...read('evaluation'),reporting:JSON.parse(readFileSync(new URL('../../../reports/performance.json',import.meta.url),'utf8'))};
const active=runs.find(r=>r.kind==='active')!;
const retention=runs.find(r=>r.kind==='retention')!;
const idle={state:'idle',detail:'No prediction requested'} as const;

test('selected metrics never join active and retention experiments or replace missing values with zero',()=>{
  assert.equal(selectedMetrics(active).delay,active.metrics.write1_ps);
  assert.equal(selectedMetrics(active).power,null);
  assert.equal(selectedMetrics(retention).delay,null);
  assert.equal(selectedMetrics(retention).power,retention.metrics.quiet_power_uw);
  assert.equal(selectedMetrics(retention).energy,retention.metrics.sequence_energy_fj);
  assert.match(condition(active),new RegExp(`${active.temp_c}`));
  assert.match(condition(retention),/retention rail/);
});

test('stored evidence is recorded, inference is not requested, and real jobs alone activate stages',()=>{
  const stored=processingStages(audit,runs,evaluation,[],idle);
  assert.deepEqual(stored.map(s=>s.state),['recorded','recorded','recorded','recorded','idle']);
  const job:Job={id:'fixture',kind:'all',state:'running',stage:'ingestion',detail:'Parsing actual export',started:'2026-10-19T00:00:00Z',ended:null};
  const processing=processingStages(audit,runs,evaluation,[job],idle);
  assert.equal(processing[1].state,'running');
  assert.equal(processing.filter(s=>s.state==='running').length,1);
  assert.equal(processingStages(audit,runs,evaluation,[],{state:'failed',detail:'Service unavailable'})[4].state,'failed');
});

test('chart colors and measurement-window boundaries preserve scientific conventions',()=>{
  assert.equal(signalColor('Q'),'#37C991');
  assert.equal(signalColor('QB'),'#36BCE3');
  assert.equal(signalColor('net2'),signalColor('WL_OUT'));
  assert.deepEqual(measurementWindows(active).map(w=>[w.start,w.end]),[active.windows_ns.active_energy]);
  assert.ok(measurementWindows(retention).every(w=>Number.isFinite(w.start)&&Number.isFinite(w.end)));
});

test('overview renders real provenance, separate conditions and REPLAY without fake live telemetry',()=>{
  const value:Evidence={audit,runs,evaluation,reload:()=>{},services:{api:'connected',ml:'connected',checkedAt:null},jobs:[],jobsError:'',inference:idle,setInference:()=>{}};
  const html=renderToStaticMarkup(<MemoryRouter><Context.Provider value={value}><CommandCentre/></Context.Provider></MemoryRouter>);
  assert.match(html,/SAMS COMMAND CENTRE/);
  assert.match(html,/REPLAY/);
  assert.match(html,new RegExp(active.file.replaceAll('.','\\.')));
  assert.match(html,/System connectivity/);
  assert.match(html,/Unavailable/);
  assert.match(html,/NOT REQUESTED/);
  assert.ok(html.indexOf('Model accuracy')<html.indexOf('Active energy validation'));
  assert.match(html,/94\.798/);
  assert.match(html,/User-provided.*Unverified/);
  assert.match(html,/8 \/ 8 independent cases/);
  assert.match(html,/Independent final test: 0 cases/);
  assert.doesNotMatch(html,/\bLIVE\b/);
  value.services.ml='unavailable';
  const cached=renderToStaticMarkup(<MemoryRouter><Context.Provider value={value}><CommandCentre/></Context.Provider></MemoryRouter>);
  assert.match(cached,/MEASURED \/ CACHED/);
});

test('technical text and status accents remain readable on both panel surfaces',()=>{
  const css=readFileSync(new URL('./style.css',import.meta.url),'utf8');
  const token=(name:string)=>css.match(new RegExp(`--${name}:\\s*(#[0-9a-f]{6})`,'i'))![1];
  const luminance=(hex:string)=>{
    const rgb=hex.slice(1).match(/../g)!.map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
    return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];
  };
  for(const foreground of ['text','muted','green','cyan','amber','red'])for(const background of ['surface','raised']){
    const contrast=(luminance(token(foreground))+.05)/(luminance(token(background))+.05);
    assert.ok(contrast>=4.5,`${foreground} on ${background}: ${contrast}`);
  }
});

test('validation cards agree with stored report and do not round sub-90 scores upward',()=>{
  assert.equal(percentage(89.999999),'89.9999%');
  assert.equal(percentage(undefined),'Not evaluated');
  const html=renderToStaticMarkup(<ValidationCard target="active_energy_fj" evaluation={evaluation}/>);
  const score=evaluation.reporting!.targets.active_energy_fj.models.ridge;
  assert.match(html,new RegExp(`${score.passing} / ${score.evaluated} independent cases`));
  assert.match(html,/100%/);assert.match(html,/0 cases/);assert.match(html,/Not evaluated/);
  assert.match(html,/Constant baseline: 0%/);assert.match(html,/RMSE/);assert.match(html,/Exploratory/);
  assert.match(html,/model-selection validation/);
  const empty=renderToStaticMarkup(<ValidationCard target="active_energy_fj" evaluation={{...evaluation,reporting:undefined,reporting_error:"Artifact mismatch"}}/>);
  assert.match(empty,/Not evaluated/);assert.match(empty,/Artifact mismatch/);assert.doesNotMatch(empty,/100%/);
});

test('scientific unit labels contain correct Unicode symbols',()=>{
  assert.equal(units.quiet_power_uw,'\u00b5W');
  assert.equal(units.active_power_uw,'\u00b5W');
  assert.equal(featureLabels.temp_c,'Temperature (\u00b0C)');
});
