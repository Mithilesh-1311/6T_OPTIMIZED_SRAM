import type {ReactNode} from 'react';
import {fmt} from './api';
import {motion,useReducedMotion} from 'framer-motion';

export function Panel({title,tag,children,className=''}:{title:string;tag?:ReactNode;children:ReactNode;className?:string}) {
  const reduced=useReducedMotion();
  return <motion.section initial={{opacity:reduced?1:0}} animate={{opacity:1}} transition={{duration:reduced?0:.14}} className={`panel instrument-panel ${className}`}>
    <div className="panel-top"><h2>{title}</h2>{tag}</div>{children}
  </motion.section>;
}

export function Status({state,label}:{state:string;label:string}) {
  return <span className={`status status-${state}`}><i aria-hidden="true"/>{label}</span>;
}

export function Metric({label,value,unit,context,tone='cyan'}:{label:string;value:unknown;unit?:string;context:string;tone?:string}) {
  const missing=value===null||value===undefined;
  return <div className={`metric metric-${tone}`}><span className="metric-label">{label}</span>
    <strong className={missing?'metric-unavailable':typeof value==='string'?'metric-text':''}>{fmt(value)}{!missing&&unit&&<small>{unit}</small>}</strong>
    <span className="metric-context">{context}</span>
  </div>;
}
