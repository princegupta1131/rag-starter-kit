// Renders a pipeline trace from the backend as a timeline, used by both panels.
// Each bar is the step's time relative to the slowest step, so you see where the time goes.

import type { TraceStep } from '../types'

export default function StepTrace({ steps }: { steps: TraceStep[] }) {
  if (!steps.length) return null
  const total = steps.reduce((sum, s) => sum + s.ms, 0)
  const slowest = Math.max(...steps.map((s) => s.ms), 1)
  return (
    <div className="trace">
      <ol className="trace-steps">
        {steps.map((s, i) => (
          <li key={i} className={s.ok ? '' : 'trace-failed'}>
            <span className="trace-dot" aria-hidden>{s.ok ? i + 1 : '!'}</span>
            <div className="trace-body">
              <div className="trace-line">
                <span className="trace-step">
                  <span className="sr-only">{i + 1}. </span>{s.step.replace('_', ' ')}
                </span>
                <span className="trace-ms">{formatMs(s.ms)}</span>
              </div>
              <span className="trace-detail">{s.detail}</span>
              <span className="trace-bar" aria-hidden>
                <span style={{ width: `${Math.max(3, (s.ms / slowest) * 100)}%` }} />
              </span>
            </div>
          </li>
        ))}
      </ol>
      <div className="trace-total">
        <span className="trace-step">total</span>
        <span className="trace-ms">{formatMs(total)}</span>
      </div>
    </div>
  )
}

const formatMs = (ms: number) => (ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${ms} ms`)
