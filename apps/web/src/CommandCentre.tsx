import {useEffect,useState} from 'react';
import {NavLink} from 'react-router-dom';
import {ArrowRight,Database,RefreshCw} from 'lucide-react';
import {api,fmt,kinds,type Point} from './api';
import {useEvidence} from './evidence';
import {condition,processingStages,selectedMetrics} from './dashboard';
import {Metric,Panel,Status} from './ui';
import {Plot,measurementWindows,signalColor,signalLabel} from './Plot';
import {Connectivity} from './Connectivity';
import {ValidationCard} from './ValidationCard';

type Replay = {run_id:string;signals:{name:string;unit:string;points:Point[];original_samples:number}[]};

export function CommandCentre() {
  const {audit,runs,evaluation,jobs,jobsError,inference,reload,services}=useEvidence();
  const sources=runs.filter(r=>['active','retention','active_hold'].includes(r.kind));
  const [selectedId,setSelectedId]=useState(sources[0]?.id||'');
  const [range,setRange]=useState('full');
  const [replay,setReplay]=useState<Replay|null>(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const selected=sources.find(r=>r.id===selectedId)||sources[0];
  const [retry,setRetry]=useState(0);
  const event=selected?.events[range];
  const rangeQuery=event?`&start=${event.wl_rise_ns-.2}&end=${event.wl_fall_ns+.2}`:'';
  useEffect(()=>{
    if(!selected)return;
    let mounted=true;
    setReplay(null);setError('');setLoading(true);
    api<Replay>(`waveforms/${selected.id}?signals=Q,QB,net2&points=700${rangeQuery}`)
      .then(data=>{if(mounted)setReplay(data);})
      .catch(e=>{if(mounted)setError(e.message);})
      .finally(()=>{if(mounted)setLoading(false);});
    return()=>{mounted=false;};
  },[selected?.id,rangeQuery,retry]);

  if(!selected)return <Panel title="No transient experiments"><p className="empty">No accepted transient source is available. Inspect Dataset Explorer for quality-control decisions.</p><NavLink to="/dataset" className="text-link">Dataset Explorer <ArrowRight size={14}/></NavLink></Panel>;
  const source=audit.files.find(f=>f.id===selected.id);
  const metrics=selectedMetrics(selected);
  const stages=processingStages(audit,runs,evaluation,jobs,inference);
  const latest=jobs[0];
  const related=runs.filter(r=>r.kind==='active'&&r.vdd_v===selected.vdd_v&&r.temp_c===selected.temp_c);
  const retention=runs.filter(r=>r.kind==='retention'&&r.temp_c===selected.temp_c);
  const cached=services.ml==='unavailable';

  return <div className="command-centre">
    <header className="command-heading"><div><h1>SAMS COMMAND CENTRE</h1><p>Measured SRAM behavior, scientific provenance and exploratory prediction.</p></div><div className="command-heading-actions"><Status state="recorded" label="SCHEMATIC EVIDENCE"/><NavLink to="/prediction" className="button secondary">Prediction workspace <ArrowRight size={14}/></NavLink></div></header>

    <div className="metric-strip">
      <Metric label="Accepted runs" value={new Set(runs.map(r=>r.sha256)).size} context="Unique source cases; paired settings grouped"/>
      <Metric label="Main supply" value={selected.vdd_v} unit="V" context="Selected experiment"/>
      <Metric label="Temperature" value={selected.temp_c} unit="°C" context="Historical setup provenance"/>
      <Metric label="Wordline mode" value={selected.mode===null?null:selected.mode===0?'SHORT':'LONG'} context={selected.mode===null?'Not labeled for this run':'Configured mode; trace-checked pulse width'}/>
      <Metric label="Write 1 delay" value={metrics.delay} unit="ps" context="WL_OUT → Q / 50% supply" tone="green"/>
      <Metric label={metrics.energyLabel} value={metrics.energy} unit="fJ" context={metrics.energyWindow} tone="green"/>
      <Metric label="Model accuracy" value={94.798} unit="%" context="User-provided ? Unverified" tone="green"/>
    </div>

    <ValidationCard target="active_energy_fj" evaluation={evaluation}/>
    <section className="provenance-strip" aria-label="Selected measurement provenance">
      <div className="source-select"><label htmlFor="overview-source">Selected experiment</label><select id="overview-source" value={selected.id} onChange={e=>{setSelectedId(e.target.value);setRange('full');}}>{sources.map(r=><option key={r.id} value={r.id}>{r.file}</option>)}</select></div>
      <div><span className="technical-label">Evidence</span><Status state={cached?'unavailable':'recorded'} label={cached?'MEASURED / CACHED':'MEASURED'}/></div>
      <div className="source-condition"><span className="technical-label">{kinds[selected.kind]}</span><strong>{condition(selected)}</strong></div>
      <div><span className="technical-label">Export sample rows</span><strong>{fmt(source?.rows)}</strong></div>
      <div><span className="technical-label">Quality control</span><Status state={source?.flags.length?'warning':'recorded'} label={source?`${source.decision} / ${source.flags.length} flags`:'Unavailable'}/></div>
    </section>

    <Panel title="Processing / evidence sequence" className="processing-panel" tag={<NavLink to="/reports" className="text-link">Job records <ArrowRight size={13}/></NavLink>}>
      <ol className="processing-stages">{stages.map((stage,i)=><li key={stage.label} className={'stage-'+stage.state}><span className="stage-index">{String(i+1).padStart(2,'0')}</span><div><strong>{stage.label}</strong><Status state={stage.state} label={stage.state==='recorded'?'RECORDED':stage.state==='idle'?'NOT REQUESTED':stage.state}/><small>{stage.detail}</small></div></li>)}</ol>
      <div className="processing-footer">{jobsError?<><span className="error-text">{jobsError}</span><button className="text-link" onClick={reload}>Reconnect <RefreshCw size={12}/></button></>:latest?<><span className="technical-label">Last stored job</span><span>{latest.kind} / {latest.state}</span><time dateTime={latest.ended||latest.started}>{new Date(latest.ended||latest.started).toLocaleString()}</time>{['failed','interrupted'].includes(latest.state)&&<><span className="error-text">{latest.detail}</span><NavLink className="text-link" to="/reports">Review / retry</NavLink></>}</>:<span>No processing job is recorded.</span>}</div>
      <p className="caption">Recorded = stored artifact, not a current operation. Validate includes exploratory model evaluation. Predict describes requests in this browser session.</p>
    </Panel>

    <div className="analytical-row primary-row">
      <Panel title="Storage nodes / wordline" tag={<Status state="replay" label="REPLAY"/>}>
        <div className="chart-toolbar"><span>{condition(selected)}</span><div className="segmented" role="group" aria-label="Replay time range">{['full',...Object.keys(selected.events)].map(key=><button key={key} className={range===key?'selected':''} aria-pressed={range===key} onClick={()=>setRange(key)}>{key==='full'?'FULL TRACE':key==='write1'?'WRITE 1':'WRITE 0'}</button>)}</div></div>
        {loading&&<div className="chart-loading" role="status">Fetching historical signal grids…</div>}
        {error&&<div className="error" role="alert">{error}<button className="button secondary" onClick={()=>setRetry(x=>x+1)}>Retry waveform</button></div>}
        {replay&&replay.run_id===selected.id&&<Plot xLabel="Time (ns)" yLabel="Voltage (V)" height={264} brush series={replay.signals.map(s=>({name:signalLabel(s.name),points:s.points,color:signalColor(s.name)}))} markers={Object.values(selected.events).map(e=>e.wl_rise_ns)} windows={measurementWindows(selected)}/>}
        <div className="panel-footnote"><span>Display decimated / calculations full resolution</span><NavLink className="text-link" to={`/waveforms?run=${selected.id}`}>Signal controls <ArrowRight size={13}/></NavLink></div>
      </Panel>
      <Panel title="System connectivity" tag={<span className="technical-label">FUNCTIONAL VIEW</span>}><Connectivity run={selected}/></Panel>
    </div>

    <div className="analytical-row secondary-row">
      <Panel title="Wordline mode comparison" tag={<Status state="recorded" label="MEASURED"/>}>
        <p className="chart-context">{selected.vdd_v} V main / {selected.temp_c} °C / active workload only</p>
        {related.length?<><div className="comparison-bars">{related.map(r=><div key={r.id}><span>{r.mode===0?'SHORT WL':'LONG WL'}</span><div className="comparison-track"><i style={{width:`${Number(r.metrics.active_energy_fj)/Math.max(...related.map(x=>Number(x.metrics.active_energy_fj)))*100}%`}}/></div><strong>{fmt(r.metrics.active_energy_fj)} <small>fJ</small></strong></div>)}</div><p className="caption">20–60 ns signed DC energy. Bars compare this matched supply and temperature only.</p><div className="compact-measurements">{related.map(r=><div key={r.id}><span>{r.mode===0?'SHORT':'LONG'} / write 1</span><strong>{fmt(r.metrics.write1_ps)} ps</strong></div>)}</div></>:<p className="empty">No matched active mode pair at this condition.</p>}
        <NavLink className="text-link" to="/comparison">Set your constraints <ArrowRight size={13}/></NavLink>
      </Panel>
      <Panel title="Quiet retention power" tag={<Status state="recorded" label="MEASURED"/>}>
        <p className="chart-context">Separate retention experiments / {selected.temp_c} °C / main {Array.from(new Set(retention.map(r=>r.vdd_v))).join(', ')||'Unavailable'} V</p>
        <Plot xLabel="Retention voltage (V)" yLabel="Quiet power (µW)" height={193} series={[0,1].map(bit=>({name:`Bit ${bit}`,points:retention.filter(r=>r.bit===bit).map(r=>({x:r.vret_v,y:Number(r.metrics.quiet_power_uw)})),dashed:bit===1}))}/>
        <p className="caption">25–65 ns. Lines join measured points; no intermediate voltage is validated. Entry/wake energy is separate.</p>
      </Panel>
      <Panel title="Data quality / model coverage" tag={<Database size={14}/>}>
        <div className="quality-counts">{Object.entries(audit.counts).map(([name,count])=><div key={name}><span>{name}</span><strong>{count}</strong></div>)}</div>
        <div className="target-coverage">{Object.entries(evaluation.targets).map(([target,spec])=><div key={target}><span>{target.replaceAll('_',' ')}</span><strong>{spec.n_cases}<small> / {spec.n_groups} groups</small></strong></div>)}</div>
        <p className="caption">Waveform rows are not independent ML cases. Model status: {Array.from(new Set(Object.values(evaluation.targets).map(t=>t.status))).join(', ')}.</p>
      </Panel>
    </div>
    <details className="source"><summary>Selected source / scientific limits</summary><code>{selected.file} / SHA-256 {selected.sha256}</code><p>{source?.flags.length?source.flags.join('; '):'No source-level quality flags recorded.'}</p><p>{audit.provenance_limit}</p><p>Quiet power, static margin and active timing belong to distinct experiments. Historical replay is not live telemetry. No circuit is controlled by this interface.</p></details>
  </div>;
}
