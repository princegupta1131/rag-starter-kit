// LEFT PANEL — talks to ingestion_service.
// Upload files or paste text, then watch each document go queued → processing → ready.

import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../../api/client.js'
import DocumentCard from './DocumentCard.jsx'

const ACCEPT = '.pdf,.docx,.txt,.md,.csv,.json,.html,.htm,.png,.jpg,.jpeg,.webp'

export default function IngestionPanel() {
  const [documents, setDocuments] = useState([])
  const [notices, setNotices] = useState([])
  const [busy, setBusy] = useState(false)
  const [mode, setMode] = useState('file') // 'file' | 'text'
  const [dragging, setDragging] = useState(false)
  const fileInput = useRef(null)

  const refresh = useCallback(() => api.listDocuments().then(setDocuments).catch(() => {}), [])
  useEffect(() => { refresh() }, [refresh])

  // Poll while anything is still being ingested.
  const working = documents.some((d) => d.status === 'queued' || d.status === 'processing')
  useEffect(() => {
    if (!working) return
    const timer = setInterval(refresh, 1500)
    return () => clearInterval(timer)
  }, [working, refresh])

  async function upload(run) {
    setBusy(true)
    setNotices([])
    try {
      const result = await run()
      const results = result.results || [result]
      setNotices(results.filter((r) => r.status !== 'queued').map((r) => `${r.filename}: ${r.reason}`))
    } catch (e) {
      setNotices([e.message])
    } finally {
      setBusy(false)
      refresh()
    }
  }

  const onFiles = (files) => files.length && upload(() => api.uploadFiles(files))

  return (
    <section className="panel ingestion">
      <div className="panel-head">
        <h2>1 · Ingestion</h2>
        <span className="muted">content in</span>
      </div>

      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={mode === 'file'} onClick={() => setMode('file')}>Upload files</button>
        <button role="tab" aria-selected={mode === 'text'} onClick={() => setMode('text')}>Paste text</button>
      </div>

      {mode === 'file' ? (
        <button
          type="button"
          className={`dropzone ${dragging ? 'dragging' : ''}`}
          onClick={() => fileInput.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); onFiles([...e.dataTransfer.files]) }}
          disabled={busy}
        >
          <strong>{busy ? 'Uploading…' : 'Drop files here or click to choose'}</strong>
          <span>PDF, DOCX, TXT, MD, CSV, JSON, HTML, images</span>
        </button>
      ) : (
        <PasteForm busy={busy} onSubmit={(title, text) => upload(() => api.uploadText(title, text))} />
      )}

      <input
        ref={fileInput}
        type="file"
        multiple
        accept={ACCEPT}
        hidden
        onChange={(e) => { onFiles([...e.target.files]); e.target.value = '' }}
      />
      {notices.map((n, i) => <p key={i} className="notice">{n}</p>)}

      <div className="doc-list-head">
        <h3>Documents</h3>
        <span className="muted">{documents.filter((d) => d.status === 'ready').length} ready</span>
      </div>
      {documents.length === 0 ? (
        <p className="empty">No documents yet. Upload one to get started.</p>
      ) : (
        <ul className="doc-list">
          {documents.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} onDeleted={refresh} />
          ))}
        </ul>
      )}
    </section>
  )
}

function PasteForm({ busy, onSubmit }) {
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const submit = (e) => {
    e.preventDefault()
    onSubmit(title.trim(), text)
    setTitle('')
    setText('')
  }
  return (
    <form className="paste" onSubmit={submit}>
      <input placeholder="Title, e.g. Leave policy" value={title} onChange={(e) => setTitle(e.target.value)} required />
      <textarea placeholder="Paste any text…" rows={6} value={text} onChange={(e) => setText(e.target.value)} required />
      <button className="primary" disabled={busy || !title.trim() || !text.trim()}>
        {busy ? 'Adding…' : 'Add to knowledge base'}
      </button>
    </form>
  )
}
