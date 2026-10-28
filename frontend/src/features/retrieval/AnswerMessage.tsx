// One reply: formatted answer with citation chips, the cited sources, and how it was made.

import { useState } from 'react'
import AnswerText from '../../shared/AnswerText'
import StepTrace from '../../shared/StepTrace'
import type { ChatResponse, ChatStatus } from '../../types'

const STATUS_LABEL: Record<ChatStatus, string | null> = {
  answered: null,
  cached: 'from cache',
  not_found: 'not in documents',
  unverified: 'no source found',
  blocked: 'blocked',
}

interface Props {
  id: string
  text: string
  response?: ChatResponse
  error?: boolean
}

export default function AnswerMessage({ id, text, response, error }: Props) {
  const [showTrace, setShowTrace] = useState(false)
  const label = error ? 'error' : response ? STATUS_LABEL[response.status] : null
  const sourceId = (n: number) => `${id}-source-${n}`

  return (
    <div className={`msg assistant ${error ? 'status-error' : `status-${response?.status}`}`}>
      {label && <span className={`badge ${error ? 'error' : response?.status}`}>{label}</span>}
      <AnswerText text={text} sourceAnchor={response?.sources.length ? sourceId : undefined} />

      {response && response.sources.length > 0 && (
        <div className="sources">
          <h4>Sources</h4>
          <ol>
            {response.sources.map((s) => (
              <li key={s.n} id={sourceId(s.n)}>
                <span className="cite">{s.n}</span>
                <div>
                  <div className="source-title">
                    {s.filename}{s.page ? `, page ${s.page}` : ''}
                    <span className="muted"> · match {Math.round(s.similarity * 100)}%</span>
                  </div>
                  <p className="snippet">{s.snippet}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {response && response.trace.length > 0 && (
        <>
          <button className="link" onClick={() => setShowTrace(!showTrace)} aria-expanded={showTrace}>
            {showTrace ? '▾' : '▸'} How this answer was made
          </button>
          {showTrace && (
            <div className="trace-box">
              {response.search_query && <p className="muted">Search query: <em>{response.search_query}</em></p>}
              <StepTrace steps={response.trace} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
