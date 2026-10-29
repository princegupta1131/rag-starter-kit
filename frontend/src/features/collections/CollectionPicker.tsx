// Choose the active collection, create a new one, or delete the current one.

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
    if (!confirm(`Delete "${selected.name}"${docs ? ` and its ${docs} document(s)` : ''}? This can't be undone.`)) return
    try {
      await api.deleteCollection(selected.id)
      await onChanged()
    } catch (err) {
      setError(`Couldn't delete: ${err instanceof Error ? err.message : err}`)
    }
  }

  if (creating || collections.length === 0) {
    return (
      <form className="collection-picker" onSubmit={create}>
        <input
          autoFocus
          placeholder="New collection name"
          aria-label="New collection name"
          value={name}
          maxLength={80}
          onChange={(e) => setName(e.target.value)}
        />
        <button className="primary" disabled={!name.trim()} title={name.trim() ? undefined : 'Type a name first'}>
          Create
        </button>
        {collections.length > 0 && (
          <button type="button" className="ghost" onClick={() => { setCreating(false); setError(null) }}>Cancel</button>
        )}
        {error && <span className="error-text" role="alert">{error}</span>}
      </form>
    )
  }

  return (
    <div className="collection-picker">
      <label htmlFor="collection" className="field-label">Collection</label>
      <select id="collection" value={selected?.id ?? ''} onChange={(e) => onSelect(e.target.value)}>
        {collections.map((c) => (
          <option key={c.id} value={c.id}>{c.name} · {c.ready_count} ready</option>
        ))}
      </select>
      <button type="button" className="secondary" onClick={() => setCreating(true)}>+ New</button>
      <button
        type="button"
        className="ghost danger"
        onClick={remove}
        title={selected ? `Delete the "${selected.name}" collection` : undefined}
      >
        Delete
      </button>
      {error && <span className="error-text" role="alert">{error}</span>}
    </div>
  )
}
