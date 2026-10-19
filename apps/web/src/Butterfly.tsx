import type {Run} from './api';
import {fmt} from './api';
export function Butterfly({run}:{run:Run}){
  const result=run.butterfly!;const v=run.vdd_v;const scale=400/v;
  const points=(pairs:number[][])=>pairs.map(([x,y])=>`${55+x*scale},${435-y*scale}`).join(' ');
  return <figure className="square-plot"><svg className="butterfly-svg" viewBox="0 0 500 495" role="img" aria-label={`Equal-scale butterfly plot with largest squares. SNM ${fmt(result.snm_mv)} millivolts.`}>
    {[0,.2,.4,.6,.8,1].map(t=><g key={t}><line x1="55" x2="455" y1={435-t*400} y2={435-t*400} stroke="#e5ebee"/><line x1={55+t*400} x2={55+t*400} y1="35" y2="435" stroke="#e5ebee"/><text x={55+t*400} y="455" textAnchor="middle">{fmt(t*v,2)}</text><text x="46" y={439-t*400} textAnchor="end">{fmt(t*v,2)}</text></g>)}
    <line x1="55" x2="455" y1="435" y2="35" stroke="#c6d1d5" strokeDasharray="3 5"/>
    <polyline points={points(result.curves.a)} stroke="#087f73" strokeWidth="2.2" fill="none"/><polyline points={points(result.curves.b)} stroke="#6366b5" strokeWidth="2.2" fill="none"/>
    {result.lobes.map((l,i)=><polyline key={i} points={points(l.square)} stroke="#ce782f" strokeWidth="1.5" strokeDasharray="5 4" fill="#ce782f0c"/>)}
    <text x="255" y="485" textAnchor="middle">Input / mirrored output (V)</text><text transform="translate(14 235) rotate(-90)" textAnchor="middle">Output / mirrored input (V)</text>
  </svg><div className="butterfly-key"><span><i/>VIN, Q</span><span><i style={{background:'#6366b5'}}/>QB, VIN</span><span><i style={{background:'#ce782f'}}/>Largest squares</span></div><details className="chart-table"><summary>Accessible butterfly data</summary><div className="table-wrap"><table><thead><tr><th>VIN (V)</th><th>Q (V)</th><th>QB (V)</th></tr></thead><tbody>{result.curves.a.slice(0,100).map(([x,y],i)=><tr key={i}><td>{fmt(x,6)}</td><td>{fmt(y,6)}</td><td>{fmt(result.curves.b[i]?.[0],6)}</td></tr>)}</tbody></table></div><p>First 100 coordinates. Complete curves and square vertices are in experiments.json.</p></details></figure>
}
