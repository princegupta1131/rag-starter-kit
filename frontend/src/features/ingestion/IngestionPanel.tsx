// LEFT PANEL (ingestion_service): upload files or paste text into the selected collection.

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { Collection, DocumentInfo, UploadResult } from '../../types'
import DocumentCard from './DocumentCard'

const ACCEPT = '.pdf,.docx,.txt,.md,.csv,.json,.html,.htm,.png,.jpg,.jpeg,.webp'

interface Props {
  collection: Collection
  onChanged: () => void
}

export default function IngestionPanel({ collection, onChanged }: Props) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [notices, setNotices] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [mode, setMode] = useState<'file' | 'text'>('file')
  const [dragging, setDragging] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  const refresh = useCallback(
    () => api.listDocuments(collection.id).then(setDocuments).catch(() => {}),
    [collection.id],
  )
  useEffect(() => { refresh() }, [refresh])

  // Poll while anything is still being ingested; refresh counts when it finishes.
  const working = documents.some((d) => d.status === 'queued' || d.status === 'processing')
  useEffect(() => {
    if (!working) return
    const timer = setInterval(refresh, 1500)
    return () => {
      clearInterval(timer)
      onChanged()
    }
  }, [working, refresh, onChanged])

  async function upload(run: () => Promise<UploadResult[]>) {
    setBusy(true)
    setNotices([])
    try {
      const results = await run()
      setNotices(results.filter((r) => r.status !== 'queued').map((r) => `${r.filename}: ${r.reason}`))
    } catch (e) {
      setNotices([e instanceof Error ? e.message : String(e)])
    } finally {
      setBusy(false)
      refresh()
      onChanged()
    }
  }

  const onFiles = (files: File[]) => {
    if (files.length) upload(async () => (await api.uploadFiles(collection.id, files)).results)
  }

  const onDeleted = () => {
    refresh()
    onChanged()
  }

  return (
    <section className="panel ingestion">
      <div className="panel-head">
        <h2>Upload</h2>
        <span className="muted">into {collection.name}</span>
      </div>

      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={mode === 'file'} onClick={() => setMode('file')}>Files</button>
        <button role="tab" aria-selected={mode === 'text'} onClick={() => setMode('text')}>Paste text</button>
      </div>

      {mode === 'file' ? (
        <button
          type="button"
          className={`dropzone ${dragging ? 'dragging' : ''}`}
          onClick={() => fileInput.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); onFiles([...e.dataTransfer.files]) }}
          disabled={busy}
        >
          <strong>{busy ? 'Uploading…' : 'Drop files or click to choose'}</strong>
          <span>PDF, Word, TXT, Markdown, CSV, JSON, HTML, images</span>
        </button>
      ) : (
        <PasteForm busy={busy} onSubmit={(title, text) => upload(async () => [await api.uploadText(collection.id, title, text)])} />
      )}
      <input
        ref={fileInput}
        type="file"
        multiple
        accept={ACCEPT}
        hidden
        onChange={(e) => { onFiles([...(e.target.files ?? [])]); e.target.value = '' }}
      />
      {notices.map((n, i) => <p key={i} className="notice">{n}</p>)}

      <div className="doc-list-head">
        <h3>Documents</h3>
        <span className="muted">{documents.filter((d) => d.status === 'ready').length} ready</span>
      </div>
      {documents.length === 0 ? (
        <p className="empty">No documents in this collection yet.</p>
      ) : (
        <ul className="doc-list">
          {documents.map((doc) => <DocumentCard key={doc.id} doc={doc} onDeleted={onDeleted} />)}
        </ul>
      )}
    </section>
  )
}

function PasteForm({ busy, onSubmit }: { busy: boolean; onSubmit: (title: string, text: string) => void }) {
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const submit = (e: FormEvent) => {
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
        {busy ? 'Adding…' : 'Add to collection'}
      </button>
    </form>
  )
}
