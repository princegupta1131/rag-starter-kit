// One page, two panels — each panel talks to one backend service.
//   left : features/ingestion  -> ingestion_service  (content in)
//   right: features/retrieval  -> retrieval_service  (answers out)

import { useEffect, useState } from 'react'
import { api } from './api/client.js'
import IngestionPanel from './features/ingestion/IngestionPanel.jsx'
import ChatPanel from './features/retrieval/ChatPanel.jsx'

export default function App() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ database: 'unreachable' }))
  }, [])

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden>◆</span>
          <div>
            <h1>RAG Starter Kit</h1>
            <p>Upload content → ask questions → answers grounded in your documents</p>
          </div>
        </div>
        <HealthPills health={health} />
      </header>
      <main className="panels">
        <IngestionPanel />
        <ChatPanel />
      </main>
    </div>
  )
}

function HealthPills({ health }) {
  if (!health) return <div className="pills"><span className="pill">checking…</span></div>
  const dbOk = health.database === 'ok'
  const keyOk = health.gemini_key === 'set'
  return (
    <div className="pills">
      <span className={`pill ${dbOk ? 'ok' : 'bad'}`} title={health.database}>
        {dbOk ? '●' : '○'} Postgres
      </span>
      <span className={`pill ${keyOk ? 'ok' : 'bad'}`} title={health.chat_model}>
        {keyOk ? '●' : '○'} Gemini
      </span>
    </div>
  )
}
