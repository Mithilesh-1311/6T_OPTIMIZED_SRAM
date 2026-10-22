import {fmt,labels,percentage,units,type Evaluation} from './api';

export function ValidationCard({target,evaluation}:{target:string;evaluation:Evaluation}) {
  const report=evaluation.reporting;
  const spec=report?.targets[target];
  const score=spec?.models?.[spec.deployed_model];
  const baseline=spec?.models?.constant;
  const tooltip=`Tolerance: max(10% of absolute measurement, ${fmt(spec?.absolute_tolerance_floor)} ${units[target]}). ${report?.method||'Not evaluated'}. ${fmt(score?.evaluated)} independent cases in ${fmt(spec?.groups)} groups. Exploratory model-selection validation; ${fmt(spec?.final_test_cases)} independent final-test cases. Tiny coverage and prior development use limit generalization.`;
  return <section className="validation-card" aria-label={`${labels[target]} validation`}>
    <span className="technical-label">{labels[target]} validation</span>
    <strong className="validation-value" title={tooltip}>{percentage(score?.percentage)} <small>{score?'within tolerance':''}</small></strong>
    <span>{score?`${score.passing} / ${score.evaluated} independent cases · ${spec.groups} groups`:'No verified OOF evidence available'}</span>
    {evaluation.reporting_error&&<p role="status" className="error-text">Evaluation unavailable: {evaluation.reporting_error}</p>}
    <span>Grouped cross-validation · Exploratory</span>
    <span>MAE {fmt(score?.mae,6)} / RMSE {fmt(score?.rmse,6)} {units[target]}</span>
    <span>Constant baseline: {percentage(baseline?.percentage)}{baseline?` (${baseline.passing}/${baseline.evaluated}); MAE ${fmt(baseline.mae,6)}, RMSE ${fmt(baseline.rmse,6)} ${units[target]}`:''}</span>
    <span>Independent final test: {fmt(spec?.final_test_cases)} cases · {spec?.final_test_status||'Not evaluated'}</span>
    <details><summary aria-label={`Tolerance and evaluation limitations for ${labels[target]}`}>Tolerance / method / limits</summary><p>Predictions within ±10% of measurement: 100 × passing / eligible OOF cases. Absolute tolerance = max(10% × |measurement|, {fmt(spec?.absolute_tolerance_floor)} {units[target]}). The floor was recorded before fitting. {report?.method}. Scalers fit on training folds. {report?.status}. Existing OOF results were available during development; no untouched final test is claimed. Constant baselines already pass both SNM targets. {report?.policy}</p></details>
  </section>;
}
