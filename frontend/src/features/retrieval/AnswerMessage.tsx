// One reply: formatted answer with citation chips, the cited sources, and how it was made.

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
    <div className="turn">
      {error ? <span className="avatar bad" aria-hidden>!</span> : <Logo size={30} className="avatar" />}
      <div className={`msg assistant ${error ? 'status-error' : `status-${response?.status}`}`}>
        {label && <span className={`badge ${error ? 'error' : response?.status}`}><span className="dot" aria-hidden />{label}</span>}
        <AnswerText text={text} sourceAnchor={response?.sources.length ? sourceId : undefined} />
        {error && <p className="hint">Check the backend terminal for details, then ask again.</p>}

        {response && response.sources.length > 0 && (
          <div className="sources">
            <h4>Sources <span className="count">{response.sources.length}</span></h4>
            <ol>
              {response.sources.map((s) => {
                const match = Math.round(s.similarity * 100)
                return (
                  <li key={s.n} id={sourceId(s.n)}>
                    <div className="source-title">
                      <span className="cite">{s.n}</span>
                      <span className="source-name" title={s.filename}>{s.filename}{s.page ? `, page ${s.page}` : ''}</span>
                    </div>
                    <p className="snippet">{s.snippet}</p>
                    <div className="source-match">
                      <span className="meter" aria-hidden><span style={{ width: `${match}%` }} /></span>
                      match {match}%
                    </div>
                  </li>
                )
              })}
            </ol>
          </div>
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
      </div>
    </div>
  )
}
