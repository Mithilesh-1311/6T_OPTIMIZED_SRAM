import type {Audit, Evaluation, Job, Run} from './api';
import type {InferenceState} from './evidence';

export function condition(run: Run): string {
  const settings = [`${run.vdd_v} V main`, `${run.temp_c} °C`];
  if (run.mode !== null) settings.push(`${run.mode === 0 ? 'short' : 'long'} WL`);
  if (run.bit !== null) settings.push(`bit ${run.bit}`, `${run.vret_v} V retention rail`);
  return settings.join(' / ');
}

export function selectedMetrics(run: Run) {
  const active = run.kind === 'active';
  return {
    delay: typeof run.metrics.write1_ps === 'number' ? run.metrics.write1_ps : null,
    energy: run.metrics[active ? 'active_energy_fj' : 'sequence_energy_fj'] ?? null,
    energyLabel: active ? 'Active energy' : 'Sequence energy',
    energyWindow: active ? '20–60 ns / two DC rails' : '19–75 ns / entry, hold, wake',
    power: run.metrics.quiet_power_uw ?? null,
    powerLabel: run.kind === 'retention' ? 'Retention power' : 'Quiet hold power',
  };
}

export function processingStages(audit: Audit, runs: Run[], evaluation: Evaluation, jobs: Job[], inference: InferenceState) {
  const job = jobs.find(j => j.state === 'running' || j.state === 'queued');
  const recorded = [audit.files.length > 0, audit.files.some(f => f.signals.length > 0), runs.length > 0, Object.keys(evaluation.targets).length > 0];
  const activeStage = job?.kind === 'all' ? ({hashing: 0, ingestion: 1, extraction: 2, training: 3} as Record<string, number>)[job.stage] : job?.stage === 'training' ? 3 : undefined;
  return ['Import', 'Parse', 'Extract', 'Validate', 'Predict'].map((label, i) => ({
    label,
    state: i === 4 ? inference.state : activeStage === i ? 'running' : recorded[i] ? 'recorded' : 'unavailable',
    detail: i === 4 ? inference.detail : activeStage === i ? job!.detail : [
      'Stored original manifest', 'Stored signal inventory', 'Stored measured labels', 'Stored exploratory evaluation',
    ][i],
  }));
}
