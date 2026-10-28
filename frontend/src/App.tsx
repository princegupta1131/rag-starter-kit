// One page: pick a collection, upload into it (left), chat with it (right).

import { useCallback, useEffect, useState } from 'react'
import { api } from './api/client'
import CollectionPicker from './features/collections/CollectionPicker'
import IngestionPanel from './features/ingestion/IngestionPanel'
import ChatPanel from './features/retrieval/ChatPanel'
import type { Collection, Health } from './types'

const SAVED_COLLECTION = 'rag-starter:collection'

function savedCollection(): string | null {
  try {
    return localStorage.getItem(SAVED_COLLECTION)
  } catch {
    return null
  }
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [healthFailed, setHealthFailed] = useState(false)
  const [collections, setCollections] = useState<Collection[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(savedCollection)

  const refreshCollections = useCallback(async () => {
    const list = await api.listCollections()
    setCollections(list)
    setSelectedId((current) => (list.some((c) => c.id === current) ? current : (list[0]?.id ?? null)))
  }, [])

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealthFailed(true))
    refreshCollections().catch(() => setHealthFailed(true))
  }, [refreshCollections])

  useEffect(() => {
    try {
      if (selectedId) localStorage.setItem(SAVED_COLLECTION, selectedId)
    } catch {
      /* storage unavailable: selection just isn't remembered */
    }
  }, [selectedId])

  const selected = collections.find((c) => c.id === selectedId) ?? null

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden>◆</span>
          <div>
            <h1>RAG Starter Kit</h1>
            <p>Answers grounded in your documents</p>
          </div>
        </div>
        <CollectionPicker
          collections={collections}
          selected={selected}
          onSelect={setSelectedId}
          onChanged={refreshCollections}
        />
        <HealthPills health={health} failed={healthFailed} />
      </header>
      <main className="panels">
        {selected ? (
          <>
            <IngestionPanel key={`in-${selected.id}`} collection={selected} onChanged={refreshCollections} />
            <ChatPanel key={`chat-${selected.id}`} collection={selected} />
          </>
        ) : (
          <div className="panel empty-state">
            <p><strong>Create a collection to start.</strong></p>
            <p className="muted">A collection is one knowledge base, e.g. "HR policies" or "Product docs".</p>
          </div>
        )}
      </main>
    </div>
  )
}

function HealthPills({ health, failed }: { health: Health | null; failed: boolean }) {
  if (failed) return <div className="pills"><span className="pill bad">Backend not reachable</span></div>
  if (!health) return <div className="pills"><span className="pill">checking…</span></div>
  const dbOk = health.database === 'ok'
  const keyOk = health.api_key === 'set'
  return (
    <div className="pills">
      <span className={`pill ${dbOk ? 'ok' : 'bad'}`} title={health.database}>Postgres</span>
      <span className={`pill ${keyOk ? 'ok' : 'bad'}`} title={`${health.chat_model} · ${health.embed_model}`}>
        {health.provider === 'openai' ? 'OpenAI' : 'Gemini'}
      </span>
    </div>
  )
}
