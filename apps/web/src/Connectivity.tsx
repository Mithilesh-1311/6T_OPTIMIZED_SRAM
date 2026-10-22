import type {Run} from './api';

export function Connectivity({run}:{run:Run}) {
  return <div className="connectivity">
    <svg viewBox="0 0 590 320" role="img" aria-labelledby="connectivity-title connectivity-description">
      <title id="connectivity-title">System connectivity</title>
      <desc id="connectivity-description">Wordline selector to control to SRAM WL; write driver and precharge to BL and BLB; active/retention supply controller to VDD_CELL; Q and QB observed outputs. Functional diagram, not transistor schematic or layout.</desc>
      <defs><marker id="connection-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker></defs>
      <g className="connection-paths" fill="none" strokeWidth="1.5" markerEnd="url(#connection-arrow)">
        <path className="connection-wl" d="M137 54 H173 M300 54 H340 V129 H367"/>
        <path className="connection-bl" d="M150 139 H218 V166 H367 M150 150 H205 V181 H367"/>
        <path className="connection-bl" d="M150 214 H244 V166 H367 M150 225 H260 V181 H367"/>
        <path className="connection-supply" d="M349 281 H405 V232"/>
        <path className="connection-q" d="M487 155 H546"/><path className="connection-qb" d="M487 194 H546"/>
      </g>
      <g className="connection-blocks">
        <rect x="18" y="28" width="119" height="53"/><text x="78" y="49">WORDLINE</text><text x="78" y="66">SELECTOR</text>
        <rect x="173" y="28" width="127" height="53"/><text x="237" y="49">WORDLINE</text><text x="237" y="66">CONTROL</text>
        <rect x="18" y="117" width="132" height="54"/><text x="84" y="140">WRITE DRIVER</text><text className="connection-secondary" x="84" y="156">BL / BLB</text>
        <rect x="18" y="193" width="132" height="54"/><text x="84" y="215">PRECHARGE</text><text x="84" y="231">/ EQUALIZER</text>
        <rect x="173" y="255" width="176" height="53"/><text x="261" y="276">ACTIVE / RETENTION</text><text x="261" y="293">CONTROLLER</text>
        <rect className="connection-cell" x="367" y="109" width="120" height="123"/><text className="connection-cell-title" x="427" y="150">6T SRAM</text><text className="connection-secondary" x="427" y="175">OBSERVED CELL</text>
      </g>
      <g className="connection-labels"><text x="319" y="121">WL</text><text x="321" y="160">BL</text><text x="315" y="195">BLB</text><text x="412" y="252">VDD_CELL</text><text className="connection-q" x="552" y="159">Q</text><text className="connection-qb" x="552" y="198">QB</text></g>
    </svg>
    <div className="connection-settings"><span>SEL <b>{run.mode===null?'not exported':run.mode}</b></span><span>MAIN <b>{run.vdd_v} V</b></span><span>RET RAIL <b>{run.vret_v} V</b></span></div>
    <p className="caption">Functional connections from the project record. Static illustration; no electrical simulation or live circuit control.</p>
  </div>;
}
