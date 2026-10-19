import {useId,useMemo} from 'react';
import {ResponsiveContainer,LineChart,Line,XAxis,YAxis,CartesianGrid,Tooltip,Legend,Brush,ReferenceLine} from 'recharts';
import type {Point} from './api';
export const palette=['#087f73','#6366b5','#ce782f','#3278b4','#b84d68','#77823a'];
export type Series={name:string;points:Point[];color?:string;dashed?:boolean};
export function Plot({series,xLabel,yLabel,brush=false,markers=[],height=300}:{series:Series[];xLabel:string;yLabel:string;brush?:boolean;markers?:number[];height?:number}){
  const id=useId();
  const rows=useMemo(()=>{
    const map=new Map<number,{x:number;[key:string]:number}>();
    series.forEach((s,i)=>s.points.forEach(p=>{const row=map.get(p.x)||{x:p.x};row['s'+i]=p.y;map.set(p.x,row)}));
    return [...map.values()].sort((a,b)=>a.x-b.x);
  },[series]);
  if(!rows.length)return <p className="empty">No supported measurements for this selection.</p>;
  return <figure aria-labelledby={id} className="plot"><figcaption id={id}>{yLabel} <span>versus {xLabel}</span></figcaption>
    <div style={{height,width:'100%',minWidth:0}}><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{top:20,right:24,bottom:20,left:8}}>
      <CartesianGrid stroke="#e6eaed" vertical={false}/><XAxis type="number" dataKey="x" domain={['dataMin','dataMax']} tick={{fontSize:11}} tickFormatter={v=>Number(v).toPrecision(4)} label={{value:xLabel,position:'insideBottom',offset:-12,fontSize:11}}/>
      <YAxis domain={['auto','auto']} tick={{fontSize:11}} width={58} tickFormatter={v=>Number(v).toPrecision(3)}/>
      <Tooltip formatter={(v)=>typeof v==='number'?v.toPrecision(6):v} labelFormatter={v=>`${Number(v).toPrecision(6)} ${xLabel}`}/><Legend wrapperStyle={{fontSize:12,paddingTop:12}}/>
      {markers.map((x,i)=><ReferenceLine key={i} x={x} stroke="#a65f26" strokeDasharray="3 4"/>)}
      {series.map((s,i)=><Line key={s.name} name={s.name} dataKey={'s'+i} type="linear" stroke={s.color||palette[i%palette.length]} strokeWidth={2} dot={rows.length<30?{r:3}:false} connectNulls isAnimationActive={false} strokeDasharray={s.dashed?'5 4':undefined}/>)}
      {brush&&<Brush dataKey="x" height={22} stroke="#087f73" tickFormatter={v=>Number(v).toFixed(2)}/>}
    </LineChart></ResponsiveContainer></div>
    <details className="chart-table"><summary>Accessible chart data ({rows.length.toLocaleString()} plotted coordinates)</summary><div className="table-wrap"><table><thead><tr><th>{xLabel}</th>{series.map(s=><th key={s.name}>{s.name}</th>)}</tr></thead><tbody>{rows.slice(0,100).map((r,i)=><tr key={i}><td>{r.x.toPrecision(7)}</td>{series.map((s,j)=><td key={s.name}>{r['s'+j]?.toPrecision(7)||'—'}</td>)}</tr>)}</tbody></table></div><p>First 100 display coordinates. Complete extracted metrics and original provenance are available in Reports.</p></details>
  </figure>
}
