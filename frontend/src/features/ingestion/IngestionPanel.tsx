// LEFT PANEL (ingestion_service): upload files or paste text into the selected collection.

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { Collection, DocumentInfo, UploadResult } from '../../types'
import DocumentCard from './DocumentCard'

const ACCEPT = '.pdf,.docx,.txt,.md,.csv,.json,.html,.htm,.png,.jpg,.jpeg,.webp,.mp4,.mov,.webm,.mpeg'

// What happened to a file that wasn't queued: skipped (already here), refused, or a failed request
interface Notice {
  kind: 'duplicate' | 'rejected' | 'error'
  text: string
}
const NOTICE_LABEL: Record<Notice['kind'], string> = { duplicate: 'Already here', rejected: 'Not added', error: 'Failed' }

interface Props {
  collection: Collection
  onChanged: () => void
}

export default function IngestionPanel({ collection, onChanged }: Props) {
  const [documents, setDocuments] = useState<DocumentInfo[] | null>(null) // null = still loading
  const [listError, setListError] = useState<string | null>(null)
  const [notices, setNotices] = useState<Notice[]>([])
  const [busy, setBusy] = useState(false)
  const [mode, setMode] = useState<'file' | 'text'>('file')
  const [dragging, setDragging] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  const refresh = useCallback(
    () =>
      api.listDocuments(collection.id)
        .then((docs) => { setDocuments(docs); setListError(null) })
        .catch((e) => setListError(e instanceof Error ? e.message : String(e))),
    [collection.id],
  )
  useEffect(() => { refresh() }, [refresh])

  // Poll while anything is still being ingested; refresh counts when it finishes.
  const working = documents?.some((d) => d.status === 'queued' || d.status === 'processing') ?? false
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
      setNotices(
        results
          .filter((r) => r.status !== 'queued')
          .map((r) => ({ kind: r.status === 'duplicate' ? 'duplicate' : 'rejected', text: `${r.filename}: ${r.reason}` })),
      )
    } catch (e) {
      setNotices([{ kind: 'error', text: e instanceof Error ? e.message : String(e) }])
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

  const ready = documents?.filter((d) => d.status === 'ready') ?? []
  const chunks = ready.reduce((sum, d) => sum + d.num_chunks, 0)

  return (
    <section className="panel ingestion" aria-labelledby="upload-title">
      <div className="panel-head">
        <span className="panel-icon" aria-hidden>↑</span>
        <div className="panel-title">
          <h2 id="upload-title">Upload</h2>
          <span className="muted">into the {collection.name} category</span>
        </div>
      </div>

      <div className="tabs" role="tablist" aria-label="Add content">
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
          aria-busy={busy}
        >
          <span className={`drop-icon ${busy ? 'spin' : ''}`} aria-hidden>{busy ? '◌' : '↑'}</span>
          <strong>{busy ? 'Uploading…' : 'Drop files or click to choose'}</strong>
          <span>PDF, Word, TXT, Markdown, CSV, JSON, HTML, images and videos (MP4, MOV, WebM)</span>
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

      {notices.length > 0 && (
        <ul className="notices" role="status">
          {notices.map((n, i) => (
            <li key={i} className={`notice ${n.kind}`}>
              <span className="notice-label">{NOTICE_LABEL[n.kind]}</span>
              <span className="notice-text">{n.text}</span>
              <button
                className="icon-button"
                aria-label="Dismiss"
                onClick={() => setNotices((all) => all.filter((_, j) => j !== i))}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="doc-list-head">
        <h3>Documents</h3>
        {documents && documents.length > 0 && (
          <span className="muted">
            {ready.length} ready · {chunks} chunk{chunks === 1 ? '' : 's'}
          </span>
        )}
      </div>

      {listError ? (
        <div className="inline-error" role="alert">
          <span>Couldn't load documents: {listError}</span>
          <button className="secondary small" onClick={refresh}>Retry</button>
        </div>
      ) : documents === null ? (
        <ul className="doc-list" aria-label="Loading documents">
          {[0, 1].map((i) => <li key={i} className="doc skeleton-row"><span className="skeleton w60" /></li>)}
        </ul>
      ) : documents.length === 0 ? (
        <div className="empty-block">
          <strong>No documents yet</strong>
          <span>
            Drop a file above or paste text. To try it out, upload{' '}
            <code>sample-docs/greenleaf-employee-handbook.md</code>.
          </span>
        </div>
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
  const missing = !title.trim() ? 'Add a title first' : !text.trim() ? 'Paste some text first' : null
  return (
    <form className="paste" onSubmit={submit}>
      <label className="field">
        <span className="field-label">Title</span>
        <input placeholder="e.g. Leave policy" value={title} onChange={(e) => setTitle(e.target.value)} required />
      </label>
      <label className="field">
        <span className="field-label">Text</span>
        <textarea placeholder="Paste any text…" rows={6} value={text} onChange={(e) => setText(e.target.value)} required />
      </label>
      <button className="primary" disabled={busy || !!missing} title={missing ?? undefined}>
        {busy ? 'Adding…' : 'Add to collection'}
      </button>
      {missing && <span className="hint">{missing}</span>}
    </form>
  )
}
