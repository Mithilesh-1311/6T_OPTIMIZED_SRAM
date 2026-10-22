import {useId,useMemo} from 'react';
import {ResponsiveContainer,LineChart,Line,XAxis,YAxis,CartesianGrid,Tooltip,Legend,Brush,ReferenceLine,ReferenceArea} from 'recharts';
import type {Point,Run} from './api';
export const palette=['#37C991','#36BCE3','#9DAEFF','#D8B7ED','#7DCAA8','#B4C8D9'];
export const signalColor=(name:string)=>({Q:palette[0],QB:palette[1],net2:palette[2],WL_OUT:palette[2],net3:'#7FBCDD',net4:'#B3D8DF'} as Record<string,string>)[name];
export const signalLabel=(name:string)=>({net2:'WL_OUT',net3:'BL',net4:'BLB',net5:'VDD_CELL'} as Record<string,string>)[name]||name;
type MeasurementWindow={start:number;end:number;label:string};
export function measurementWindows(run:Run):MeasurementWindow[]{return Object.entries(run.windows_ns||{}).flatMap(([label,range])=>Array.isArray(range)&&range.length===2&&range.every(v=>typeof v==='number')?[{start:range[0],end:range[1],label:label.replaceAll('_',' ')}]:[]);}
export type Series={name:string;points:Point[];color?:string;dashed?:boolean};
export function Plot({series,xLabel,yLabel,brush=false,markers=[],height=260,windows=[]}:{series:Series[];xLabel:string;yLabel:string;brush?:boolean;markers?:number[];height?:number;windows?:MeasurementWindow[]}){
  const id=useId();
  const rows=useMemo(()=>{
    const map=new Map<number,{x:number;[key:string]:number}>();
    series.forEach((s,i)=>s.points.forEach(p=>{const row=map.get(p.x)||{x:p.x};row['s'+i]=p.y;map.set(p.x,row)}));
    return [...map.values()].sort((a,b)=>a.x-b.x);
  },[series]);
  if(!rows.length)return <p className="empty">No supported measurements for this selection.</p>;
  return <figure aria-labelledby={id} className="plot"><figcaption id={id}>{yLabel} <span>versus {xLabel}</span></figcaption>
    <div style={{height,width:'100%',minWidth:0}}><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{top:20,right:24,bottom:20,left:8}}>
      <CartesianGrid stroke="#23313B" strokeDasharray="2 4"/><XAxis type="number" dataKey="x" domain={['dataMin','dataMax']} stroke="#526572" tick={{fontSize:10,fill:'#9AAAB7',fontFamily:'IBM Plex Mono'}} tickFormatter={v=>Number(v).toPrecision(4)} label={{value:xLabel,position:'insideBottom',offset:-12,fontSize:11,fill:'#9AAAB7'}}/>
      <YAxis domain={['auto','auto']} stroke="#526572" tick={{fontSize:10,fill:'#9AAAB7',fontFamily:'IBM Plex Mono'}} width={58} tickFormatter={v=>Number(v).toPrecision(3)}/>
      <Tooltip contentStyle={{background:'#111920',border:'1px solid #3B5363',borderRadius:2,fontFamily:'IBM Plex Mono',fontSize:11,color:'#E4ECF2'}} labelStyle={{color:'#E4ECF2'}} cursor={{stroke:'#728D9E',strokeDasharray:'3 3'}} formatter={(v)=>typeof v==='number'?v.toPrecision(6):v} labelFormatter={v=>`${Number(v).toPrecision(6)} ${xLabel}`}/><Legend wrapperStyle={{fontSize:11,paddingTop:12,fontFamily:'IBM Plex Mono'}}/>
      {windows.map(w=><ReferenceArea key={w.label} x1={w.start} x2={w.end} fill="#37C991" fillOpacity={.055} strokeOpacity={0} ifOverflow="hidden"/>)}
      {markers.map((x,i)=><ReferenceLine key={i} x={x} stroke="#E5AD38" strokeDasharray="3 4"/>)}
      {series.map((s,i)=><Line key={s.name} name={s.name} dataKey={'s'+i} type="linear" stroke={s.color||palette[i%palette.length]} strokeWidth={2} dot={rows.length<30?{r:3}:false} connectNulls isAnimationActive={false} strokeDasharray={s.dashed?'5 4':undefined}/>)}
      {brush&&<Brush dataKey="x" height={22} stroke="#36BCE3" fill="#111920" tickFormatter={v=>Number(v).toFixed(2)}/>}
    </LineChart></ResponsiveContainer></div>
    {windows.length>0&&<p className="window-key">Measurement windows: {windows.map(w=>`${w.label} ${w.start}–${w.end} ns`).join(' / ')}</p>}
    <details className="chart-table"><summary>Accessible chart data ({rows.length.toLocaleString()} plotted coordinates)</summary><div className="table-wrap"><table><thead><tr><th>{xLabel}</th>{series.map(s=><th key={s.name}>{s.name}</th>)}</tr></thead><tbody>{rows.slice(0,100).map((r,i)=><tr key={i}><td>{r.x.toPrecision(7)}</td>{series.map((s,j)=><td key={s.name}>{r['s'+j]?.toPrecision(7)||'Unavailable'}</td>)}</tr>)}</tbody></table></div><p>First 100 display coordinates. Complete extracted metrics and original provenance are available in Reports.</p></details>
  </figure>
}
