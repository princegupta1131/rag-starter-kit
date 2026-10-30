// One document: status, chunk count, its ingestion steps, and its chunks on demand.

import { useState } from 'react'
import { api } from '../../api/client'
import StepTrace from '../../shared/StepTrace'
import type { Chunk, DocumentInfo } from '../../types'

// "handbook.md" -> "MD"; pasted text has no extension -> "TEXT"
export const fileType = (name: string) => (name.includes('.') ? name.split('.').pop()!.slice(0, 4).toUpperCase() : 'TEXT')

export default function DocumentCard({ doc, onDeleted }: { doc: DocumentInfo; onDeleted: () => void }) {
  const [open, setOpen] = useState(false)
  const [chunks, setChunks] = useState<Chunk[] | null>(null)
  const [loadingChunks, setLoadingChunks] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function toggleChunks() {
    if (chunks) return setChunks(null)
    setError(null)
    setLoadingChunks(true)
    try {
      setChunks(await api.listChunks(doc.id))
    } catch (err) {
      setError(`Couldn't load chunks: ${err instanceof Error ? err.message : err}`)
    } finally {
      setLoadingChunks(false)
    }
  }

  async function remove() {
    if (!confirm(`Delete "${doc.filename}"? This can't be undone.`)) return
    setError(null)
    try {
      await api.deleteDocument(doc.id)
      onDeleted()
    } catch (err) {
      setError(`Couldn't delete: ${err instanceof Error ? err.message : err}`)
    }
  }

  const working = doc.status === 'queued' || doc.status === 'processing'
  const status = doc.stale ? 'stale' : doc.status

  return (
    <li className={`doc ${open ? 'open' : ''}`}>
      <button className="doc-row" onClick={() => setOpen(!open)} aria-expanded={open} title={doc.filename}>
        <span className="file-type" aria-hidden>{fileType(doc.filename)}</span>
        <span className="doc-main">
          <span className="doc-name">{doc.filename}</span>
          <span className="doc-meta">
            {doc.stale ? (
              <span className="warn-text">Embedded with {doc.embed_model}, not searched. Upload it again.</span>
            ) : doc.status === 'ready' ? (
              `${doc.num_chunks} chunk${doc.num_chunks === 1 ? '' : 's'}`
            ) : working ? (
              'Reading, chunking and embedding…'
            ) : (
              doc.error && <span className="error-text">{doc.error}</span>
            )}
          </span>
        </span>
        <span className={`badge ${status}`}>
          <span className={`dot ${working ? 'pulse' : ''}`} aria-hidden />
          {doc.stale ? 'upload again' : doc.status}
        </span>
        <span className="chev" aria-hidden />
      </button>

      {open && (
        <div className="doc-details">
          {doc.steps.length > 0 ? (
            <StepTrace steps={doc.steps} />
          ) : (
            <p className="muted">{working ? 'The steps appear here when it finishes.' : 'No steps recorded.'}</p>
          )}
          {error && <p className="error-text" role="alert">{error}</p>}
          <div className="doc-actions">
            {doc.status === 'ready' && (
              <button className="secondary small" onClick={toggleChunks} disabled={loadingChunks}>
                {loadingChunks ? 'Loading…' : chunks ? 'Hide chunks' : 'View chunks'}
              </button>
            )}
            <button className="ghost danger small push-right" onClick={remove}>Delete</button>
          </div>
          {chunks && (
            <ol className="chunks">
              {chunks.map((c) => (
                <li key={c.index}>
                  <span className="chunk-meta">
                    #{c.index + 1}{c.page ? ` · page ${c.page}` : ''} · {c.text.split(/\s+/).length} words
                  </span>
                  {c.text}
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </li>
  )
}
