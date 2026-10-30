// Choose the active category (a collection in the backend, e.g. HR, Finance or Tech), create a new one, or delete it.

import { useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { Collection } from '../../types'

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
    if (!confirm(`Delete the category "${selected.name}"${docs ? ` and its ${docs} document(s)` : ''}? This can't be undone.`)) return
    try {
      await api.deleteCollection(selected.id)
      await onChanged()
    } catch (err) {
      setError(`Couldn't delete: ${err instanceof Error ? err.message : err}`)
    }
  }

  const showForm = creating || collections.length === 0

  return (
    <nav className="collection-picker" aria-label="Category">
      <div className="side-head">
        <label htmlFor="collection" className="side-label">Category</label>
        {!showForm && (
          <button type="button" className="ghost small" onClick={() => setCreating(true)} title="New category">
            + New
          </button>
        )}
      </div>

      {showForm && (
        <form className="new-collection" onSubmit={create}>
          <input
            autoFocus
            placeholder="Category name, e.g. HR, Finance, Tech"
            aria-label="New category name"
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
          <select
            id="collection"
            className="collection-select"
            value={selected?.id ?? ''}
            onChange={(e) => onSelect(e.target.value)}
          >
            {collections.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <div className="side-note">
            <span>The chat answers only from this category's documents.</span>
            <button
              type="button"
              className="link-danger"
              onClick={remove}
              title={selected ? `Delete the "${selected.name}" category and its documents` : undefined}
            >
              Delete
            </button>
          </div>
        </>
      )}
      {error && <span className="error-text" role="alert">{error}</span>}
    </nav>
  )
}
