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
  const [collections, setCollections] = useState<Collection[] | null>(null) // null = still loading
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

  const selected = collections?.find((c) => c.id === selectedId) ?? null

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
        {collections && !healthFailed && (
          <CollectionPicker
            collections={collections}
            selected={selected}
            onSelect={setSelectedId}
            onChanged={refreshCollections}
          />
        )}
        <HealthPills health={health} failed={healthFailed} />
      </header>
      <main className="panels">
        {healthFailed ? (
          <div className="panel state-panel" role="alert">
            <span className="state-icon bad" aria-hidden>!</span>
            <h2>Can't reach the backend</h2>
            <p className="muted">
              The app needs the backend on port 8000. Start it with <code>make run</code> (Windows: Setup Guide,
              Step 6), then reload this page.
            </p>
            <button className="primary" onClick={() => window.location.reload()}>Reload</button>
          </div>
        ) : collections === null ? (
          <div className="panel state-panel" role="status">
            <span className="skeleton w60" />
            <span className="skeleton w40" />
            <span className="sr-only">Loading collections…</span>
          </div>
        ) : selected ? (
          <>
            <IngestionPanel key={`in-${selected.id}`} collection={selected} onChanged={refreshCollections} />
            <ChatPanel key={`chat-${selected.id}`} collection={selected} />
          </>
        ) : (
          <div className="panel state-panel">
            <span className="state-icon" aria-hidden>◆</span>
            <h2>Create a collection to start</h2>
            <p className="muted">
              A collection is one knowledge base, e.g. "HR policies" or "Product docs". Type a name at the top and
              press Create.
            </p>
          </div>
        )}
      </main>
    </div>
  )
}

const PROVIDER_LABELS: Record<string, string> = { gemini: 'Gemini', openai: 'OpenAI' }

function HealthPills({ health, failed }: { health: Health | null; failed: boolean }) {
  if (failed) {
    return (
      <div className="pills">
        <span className="pill bad"><span aria-hidden>✕</span> Backend not reachable</span>
      </div>
    )
  }
  if (!health) return <div className="pills"><span className="pill">Checking…</span></div>
  const dbOk = health.database === 'ok'
  const keyOk = health.api_key === 'set'
  const provider = PROVIDER_LABELS[health.provider] ?? health.provider
  return (
    <div className="pills" aria-label="Connections">
      <span className={`pill ${dbOk ? 'ok' : 'bad'}`} title={dbOk ? 'Database connected' : health.database}>
        <span aria-hidden>{dbOk ? '✓' : '✕'}</span> Postgres
        {!dbOk && <span className="sr-only">: not connected</span>}
      </span>
      <span
        className={`pill ${keyOk ? 'ok' : 'bad'}`}
        title={keyOk ? `${health.chat_model} · ${health.embed_model}` : `${provider} API key missing in backend/.env`}
      >
        <span aria-hidden>{keyOk ? '✓' : '✕'}</span> {provider}
        {!keyOk && <span className="sr-only">: API key missing</span>}
      </span>
    </div>
  )
}
