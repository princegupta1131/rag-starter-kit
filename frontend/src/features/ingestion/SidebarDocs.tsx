// Sidebar: the documents in the selected category, and the button that opens the upload options.

import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { Collection, DocumentInfo } from '../../types'
import { fileType } from './DocumentCard'

const STATUS_TITLE: Record<string, string> = {
  ready: 'Ready to answer from',
  queued: 'Waiting to be processed',
  processing: 'Being processed',
  failed: 'Failed to process',
  stale: 'Needs re-upload (embedding model changed)',
}

interface Props {
  collection: Collection
  active: boolean // the Documents page is open
  onOpen: () => void
}

export default function SidebarDocs({ collection, active, onOpen }: Props) {
  const [docs, setDocs] = useState<DocumentInfo[] | null>(null) // null = still loading

  // the counts change when an upload finishes or a document is deleted, so refetch then too
  useEffect(() => {
    let live = true
    api.listDocuments(collection.id)
      .then((d) => live && setDocs(d))
      .catch(() => live && setDocs([]))
    return () => { live = false }
  }, [collection.id, collection.document_count, collection.ready_count])

  return (
    <section className="side-docs" aria-label="Documents">
      <div className="side-head">
        <span className="side-label">Documents</span>
        <span className="side-count">{collection.document_count}</span>
      </div>

      {docs && docs.length > 0 && (
        <ul className="side-doc-list">
          {docs.map((d) => {
            const state = d.stale ? 'stale' : d.status
            return (
              <li key={d.id}>
                <button type="button" className="side-doc" onClick={onOpen} title={d.filename}>
                  <span className="file-type" aria-hidden>{fileType(d.filename)}</span>
                  <span className="side-doc-name">{d.filename}</span>
                  <span className={`status-dot ${state}`} title={STATUS_TITLE[state]} />
                  <span className="sr-only">{STATUS_TITLE[state]}</span>
                </button>
              </li>
            )
          })}
        </ul>
      )}
      {docs && docs.length === 0 && <p className="side-empty">No documents yet. Upload one to start asking.</p>}

      <button type="button" className="upload-btn" onClick={onOpen} aria-current={active ? 'page' : undefined}>
        <span aria-hidden>↑</span> Upload documents
      </button>
    </section>
  )
}
