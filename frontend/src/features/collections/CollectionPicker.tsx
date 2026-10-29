// Choose the active collection, create a new one, or delete the current one.

import { useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { Collection } from '../../types'

// "2 documents, all ready" / "1 of 2 ready" / "No documents yet"
function docCount(c: Collection): string {
  if (c.document_count === 0) return 'No documents yet'
  const docs = `${c.document_count} document${c.document_count === 1 ? '' : 's'}`
  return c.ready_count === c.document_count ? `${docs}, all ready` : `${c.ready_count} of ${docs} ready`
}

interface Props {
  collections: Collection[]
  selected: Collection | null
  onSelect: (id: string) => void
  onChanged: () => Promise<void>
}

export default function CollectionPicker({ collections, selected, onSelect, onChanged }: Props) {
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function create(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const created = await api.createCollection(name.trim())
      await onChanged()
      onSelect(created.id)
      setName('')
      setCreating(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  async function remove() {
    if (!selected) return
    setError(null)
    const docs = selected.document_count
    if (!confirm(`Delete "${selected.name}"${docs ? ` and its ${docs} document(s)` : ''}? This can't be undone.`)) return
    try {
      await api.deleteCollection(selected.id)
      await onChanged()
    } catch (err) {
      setError(`Couldn't delete: ${err instanceof Error ? err.message : err}`)
    }
  }

  const showForm = creating || collections.length === 0

  // Sidebar list on wide screens; the same choice as a dropdown on phones (CSS shows one of them)
  return (
    <nav className="collection-picker" aria-label="Collections">
      <div className="nav-head">
        <span className="field-label">Collections</span>
        {!showForm && (
          <button type="button" className="ghost small" onClick={() => setCreating(true)} title="New collection">
            + New
          </button>
        )}
      </div>
      <p className="nav-help">Each collection is its own set of documents. The chat answers only from the selected one.</p>

      {showForm && (
        <form className="new-collection" onSubmit={create}>
          <input
            autoFocus
            placeholder="New collection name"
            aria-label="New collection name"
            value={name}
            maxLength={80}
            onChange={(e) => setName(e.target.value)}
          />
          <div className="form-actions">
            <button className="primary small" disabled={!name.trim()} title={name.trim() ? undefined : 'Type a name first'}>
              Create
            </button>
            {collections.length > 0 && (
              <button type="button" className="ghost small" onClick={() => { setCreating(false); setError(null) }}>
                Cancel
              </button>
            )}
          </div>
        </form>
      )}

      {collections.length > 0 && (
        <>
          <ul className="nav-list">
            {collections.map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  className="nav-item"
                  aria-current={c.id === selected?.id ? 'true' : undefined}
                  onClick={() => onSelect(c.id)}
                  title={c.name}
                >
                  <span className="nav-name">{c.name}</span>
                  <span className="nav-meta">{docCount(c)}</span>
                </button>
              </li>
            ))}
          </ul>
          <label htmlFor="collection" className="sr-only">Collection</label>
          <select
            id="collection"
            className="collection-select"
            value={selected?.id ?? ''}
            onChange={(e) => onSelect(e.target.value)}
          >
            {collections.map((c) => (
              <option key={c.id} value={c.id}>{c.name} · {docCount(c)}</option>
            ))}
          </select>
          <button
            type="button"
            className="ghost danger small nav-delete"
            onClick={remove}
            title={selected ? `Delete the "${selected.name}" collection and its documents` : undefined}
          >
            Delete collection
          </button>
        </>
      )}
      {error && <span className="error-text" role="alert">{error}</span>}
    </nav>
  )
}
