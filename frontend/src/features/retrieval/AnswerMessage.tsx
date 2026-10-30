// One reply: the formatted answer first, then the cited sources, then how it was made.

import { useState } from 'react'
import AnswerText from '../../shared/AnswerText'
import Logo from '../../shared/Logo'
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
    <article className={`answer-block ${error ? 'status-error' : `status-${response?.status}`}`}>
      <section className="answer-section">
        <h3 className="section-label">
          {error ? <span className="error-mark" aria-hidden>!</span> : <Logo size={18} />}
          Answer
          {label && <span className={`badge ${error ? 'error' : response?.status}`}><span className="dot" aria-hidden />{label}</span>}
        </h3>
        <AnswerText text={text} sourceAnchor={response?.sources.length ? sourceId : undefined} />
        {error && <p className="hint">Check the backend terminal for details, then ask again.</p>}
      </section>

      {response && response.sources.length > 0 && (
        <section className="sources" aria-label="Sources">
          <h3 className="section-label">Sources <span className="count">{response.sources.length}</span></h3>
          <ol>
            {response.sources.map((s) => (
              <li key={s.n} id={sourceId(s.n)}>
                <div className="source-title">
                  <span className="cite">{s.n}</span>
                  <span className="source-name" title={s.filename}>{s.filename}{s.page ? `, page ${s.page}` : ''}</span>
                  <span className="source-match" title="How close this passage is to the question">
                    {Math.round(s.similarity * 100)}%
                  </span>
                </div>
                <p className="snippet">{s.snippet}</p>
              </li>
            ))}
          </ol>
        </section>
      )}

      {response && response.trace.length > 0 && (
        <div className="trace-box">
          <button className="fold" onClick={() => setShowTrace(!showTrace)} aria-expanded={showTrace}>
            <span className="chev" aria-hidden />
            How this answer was made
            <span className="fold-meta">{response.trace.length} steps</span>
          </button>
          {showTrace && (
            <>
              {response.search_query && (
                <p className="query">
                  <span className="field-label">Search query</span>
                  <em>{response.search_query}</em>
                </p>
              )}
              <StepTrace steps={response.trace} />
            </>
          )}
        </div>
      )}
    </article>
  )
}
