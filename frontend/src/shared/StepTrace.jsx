// Shows a pipeline trace from the backend: [{step, detail, ms, ok}]
// Used by both panels so learners see what every step did.

export default function StepTrace({ steps }) {
  if (!steps?.length) return null
  const total = steps.reduce((sum, s) => sum + s.ms, 0)
  return (
    <ol className="trace">
      {steps.map((s, i) => (
        <li key={i} className={s.ok ? '' : 'trace-failed'}>
          <span className="trace-step">{i + 1}. {s.step.replace('_', ' ')}</span>
          <span className="trace-detail">{s.detail}</span>
          <span className="trace-ms">{formatMs(s.ms)}</span>
        </li>
      ))}
      <li className="trace-total">
        <span className="trace-step">total</span>
        <span className="trace-detail" />
        <span className="trace-ms">{formatMs(total)}</span>
      </li>
    </ol>
  )
}

const formatMs = (ms) => (ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${ms} ms`)
