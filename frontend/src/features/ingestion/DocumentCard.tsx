// One document: status, chunk count, its ingestion steps, and its chunks on demand.

import { useState } from 'react'
import { api } from '../../api/client'
import StepTrace from '../../shared/StepTrace'
import type { Chunk, DocumentInfo } from '../../types'

export default function DocumentCard({ doc, onDeleted }: { doc: DocumentInfo; onDeleted: () => void }) {
  const [open, setOpen] = useState(false)
  const [chunks, setChunks] = useState<Chunk[] | null>(null)

  async function toggleChunks() {
    setChunks(chunks ? null : await api.listChunks(doc.id))
  }

  async function remove() {
    if (!confirm(`Delete "${doc.filename}"?`)) return
    await api.deleteDocument(doc.id)
    onDeleted()
  }

  return (
    <li className="doc">
      <div className="doc-row">
        <button className="doc-name" onClick={() => setOpen(!open)} aria-expanded={open} title={doc.filename}>
          <span className="chev" aria-hidden>{open ? '▾' : '▸'}</span>
          {doc.filename}
        </button>
        <span className={`badge ${doc.stale ? 'stale' : doc.status}`}>{doc.stale ? 'upload again' : doc.status}</span>
      </div>
      <div className="doc-meta">
        {doc.status === 'ready' && <span>{doc.num_chunks} chunk{doc.num_chunks === 1 ? '' : 's'}</span>}
        {doc.stale && <span className="warn-text"> · embedded with {doc.embed_model}, not searched</span>}
        {doc.error && <span className="error-text">{doc.error}</span>}
      </div>

      {open && (
        <div className="doc-details">
          <StepTrace steps={doc.steps} />
          <div className="doc-actions">
            {doc.status === 'ready' && (
              <button className="link" onClick={toggleChunks}>{chunks ? 'Hide chunks' : 'View chunks'}</button>
            )}
            <button className="link danger" onClick={remove}>Delete</button>
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
