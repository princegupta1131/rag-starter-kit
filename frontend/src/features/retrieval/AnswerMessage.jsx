// One assistant reply: answer text with [n] citation chips, cited sources, and the pipeline trace.

import { useState } from 'react'
import StepTrace from '../../shared/StepTrace.jsx'

const STATUS_LABEL = {
  answered: null,
  cached: 'from cache',
  not_found: 'not in documents',
  unverified: 'blocked: no citation',
  blocked: 'blocked by guard',
  error: 'error',
}

export default function AnswerMessage({ message }) {
  const [showTrace, setShowTrace] = useState(false)
  const r = message.response || {}
  const label = STATUS_LABEL[r.status]

  return (
    <div className={`msg assistant status-${r.status}`}>
      {label && <span className={`badge ${r.status}`}>{label}</span>}
      <div className="answer">{renderAnswer(message.content)}</div>

      {r.sources?.length > 0 && (
        <div className="sources">
          <h4>Sources</h4>
          <ol>
            {r.sources.map((s) => (
              <li key={s.n}>
                <span className="cite">{s.n}</span>
                <div>
                  <div className="source-title">
                    {s.filename}{s.page ? `, page ${s.page}` : ''}
                    <span className="muted"> · similarity {s.similarity}</span>
                  </div>
                  <p className="snippet">{s.text.length > 260 ? `${s.text.slice(0, 260)}…` : s.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {r.trace?.length > 0 && (
        <>
          <button className="link" onClick={() => setShowTrace(!showTrace)} aria-expanded={showTrace}>
            {showTrace ? '▾' : '▸'} How this answer was made
          </button>
          {showTrace && (
            <div className="trace-box">
              {r.search_query && <p className="muted">Search query: <em>{r.search_query}</em></p>}
              <StepTrace steps={r.trace} />
            </div>
          )}
        </>
      )}
    </div>
  )
}

// Minimal formatting: line breaks, **bold**, and [n] -> citation chip.
function renderAnswer(text) {
  return text.split('\n').map((line, i) => (
    <p key={i}>
      {line.split(/(\*\*[^*]+\*\*|\[\d+\])/g).map((part, j) => {
        if (/^\[\d+\]$/.test(part)) return <span key={j} className="cite">{part.slice(1, -1)}</span>
        if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={j}>{part.slice(2, -2)}</strong>
        return part
      })}
    </p>
  ))
}
