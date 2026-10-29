// A sidebar to pick the collection; the main area shows the chat or the Documents page.

import { useCallback, useEffect, useState } from 'react'
import { api } from './api/client'
import CollectionPicker from './features/collections/CollectionPicker'
import IngestionPanel from './features/ingestion/IngestionPanel'
import ChatPanel from './features/retrieval/ChatPanel'
import Logo from './shared/Logo'
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
  const [chatKey, setChatKey] = useState(0) // bump to start a new chat
  const [view, setView] = useState<'chat' | 'documents'>('chat')

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
      <aside className="sidebar">
        <div className="brand">
          <Logo size={32} />
          <div>
            <h1>RAG <span>Starter Kit</span></h1>
            <p>Answers from your documents</p>
          </div>
        </div>

        {selected && (
          <button className="primary new-chat" onClick={() => { setChatKey((k) => k + 1); setView('chat') }}>
            <span aria-hidden>+</span> New chat
          </button>
        )}

        {collections && !healthFailed && (
          <CollectionPicker
            collections={collections}
            selected={selected}
            onSelect={setSelectedId}
            onChanged={refreshCollections}
          />
        )}

        {selected && (
          <button
            className="docs-card"
            onClick={() => setView((v) => (v === 'documents' ? 'chat' : 'documents'))}
            aria-current={view === 'documents' ? 'page' : undefined}
          >
            <span className="docs-icon" aria-hidden>↑</span>
            <span className="docs-text">
              <b>Documents</b>
              <small>Upload and view files</small>
            </span>
            <span className="chev" aria-hidden />
          </button>
        )}
      </aside>

      <main className="main">
        <div className="main-top">
          <HealthPills health={health} failed={healthFailed} />
        </div>
        <div className="main-body">
          {selected && view === 'documents' && !healthFailed && (
            <div className="docs-page">
              <div className="page-head">
                <button className="ghost small" onClick={() => setView('chat')}>← Back to chat</button>
              </div>
              <IngestionPanel key={`in-${selected.id}`} collection={selected} onChanged={refreshCollections} />
            </div>
          )}
          {healthFailed ? (
            <div className="state-panel" role="alert">
              <span className="state-icon bad" aria-hidden>!</span>
              <h2>Can't reach the backend</h2>
              <p className="muted">
                The app needs the backend on port 8000. Start it with <code>make run</code> (Windows: Setup Guide,
                Step 6), then reload this page.
              </p>
              <button className="primary" onClick={() => window.location.reload()}>Reload</button>
            </div>
          ) : collections === null ? (
            <div className="state-panel" role="status">
              <span className="skeleton w60" />
              <span className="skeleton w40" />
              <span className="sr-only">Loading collections…</span>
            </div>
          ) : selected ? (
            // stays mounted on the Documents page, so the conversation is kept
            <div className="chat-wrap" hidden={view === 'documents'}>
              <ChatPanel
                key={`chat-${selected.id}-${chatKey}`}
                collection={selected}
                onUpload={() => setView('documents')}
              />
            </div>
          ) : (
            <div className="state-panel">
              <Logo size={56} />
              <h2>Create a collection to start</h2>
              <p className="muted">
                A collection is one knowledge base, e.g. "HR policies" or "Product docs". Name it in the sidebar and
                press Create.
              </p>
            </div>
          )}
        </div>
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
        <span className="dot" aria-hidden /> Postgres
        {!dbOk && <span className="sr-only">: not connected</span>}
      </span>
      <span
        className={`pill ${keyOk ? 'ok' : 'bad'}`}
        title={keyOk ? `${health.chat_model} · ${health.embed_model}` : `${provider} API key missing in backend/.env`}
      >
        <span className="dot" aria-hidden /> {provider}
        {!keyOk && <span className="sr-only">: API key missing</span>}
      </span>
    </div>
  )
}
