// RIGHT PANEL (retrieval_service): ask questions about the selected collection.

import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { ChatResponse, Collection, Turn } from '../../types'
import AnswerMessage from './AnswerMessage'

type Message = Turn & { response?: ChatResponse; error?: boolean }

export default function ChatPanel({ collection }: { collection: Collection }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [thinking, setThinking] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const list = useRef<HTMLDivElement>(null)
  const hasDocuments = collection.ready_count > 0

  // Scroll only the message list, never the page.
  useEffect(() => {
    list.current?.scrollTo({ top: list.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  // Starter questions built from the real document names
  useEffect(() => {
    if (!hasDocuments) return setSuggestions([])
    api.listDocuments(collection.id)
      .then((docs) =>
        setSuggestions(
          docs.filter((d) => d.status === 'ready' && !d.stale).slice(0, 2).map((d) => `What is ${d.filename} about?`),
        ),
      )
      .catch(() => setSuggestions([]))
  }, [collection.id, hasDocuments])

  async function ask(q: string) {
    if (!q || thinking) return
    const history: Turn[] = messages.filter((m) => !m.error).map(({ role, content }) => ({ role, content }))
    setMessages((m) => [...m, { role: 'user', content: q }])
    setQuestion('')
    setThinking(true)
    try {
      const response = await api.chat(q, history, collection.id)
      setMessages((m) => [...m, { role: 'assistant', content: response.answer, response }])
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setMessages((m) => [...m, { role: 'assistant', content: message, error: true }])
    } finally {
      setThinking(false)
    }
  }

  const submit = (e: FormEvent) => {
    e.preventDefault()
    ask(question.trim())
  }

  const blocked = !hasDocuments ? 'Upload a document first' : thinking ? 'Wait for the answer' : null

  return (
    <section className="panel chat" aria-labelledby="ask-title">
      <div className="panel-head">
        <span className="panel-icon ai" aria-hidden>✦</span>
        <div className="panel-title">
          <h2 id="ask-title">Ask</h2>
          <span className="muted">{collection.name}</span>
        </div>
        {messages.length > 0 && (
          <button className="secondary small push-right" onClick={() => setMessages([])}>New chat</button>
        )}
      </div>

      <div className="messages" ref={list} aria-live="polite">
        {messages.length === 0 && (
          <div className="chat-empty">
            <span className="hero-icon" aria-hidden>✦</span>
            {hasDocuments ? (
              <>
                <strong>Ask anything about the documents in {collection.name}.</strong>
                <p>Answers cite their sources. Open “How this answer was made” to see each step.</p>
                <ol className="flow" aria-label="How an answer is made">
                  <li>Your question</li>
                  <li>Search by meaning + keywords</li>
                  <li>Answer with sources</li>
                </ol>
                {suggestions.length > 0 && (
                  <div className="suggestions">
                    <span className="field-label">Try</span>
                    {suggestions.map((s) => (
                      <button key={s} className="chip" onClick={() => ask(s)}>{s}</button>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <>
                <strong>No documents to ask yet.</strong>
                <p>Answers only come from the documents in {collection.name}. Three steps to your first answer:</p>
                <ol className="getting-started">
                  <li className="current"><b>Upload a document</b><span>Drop a file or paste text in Upload</span></li>
                  <li><b>Wait for READY</b><span>It's split into chunks and embedded</span></li>
                  <li><b>Ask a question</b><span>The answer cites where it found each fact</span></li>
                </ol>
              </>
            )}
          </div>
        )}
        {messages.map((m, i) =>
          m.role === 'user' ? (
            <div key={i} className="msg user">{m.content}</div>
          ) : (
            <AnswerMessage key={i} id={`m${i}`} text={m.content} response={m.response} error={m.error} />
          ),
        )}
        {thinking && (
          <div className="turn" role="status">
            <span className="avatar thinking-avatar" aria-hidden>◆</span>
            <div className="msg assistant thinking">
              <span className="thinking-label">Searching your documents and writing an answer…</span>
              <span className="skeleton w80" />
              <span className="skeleton w60" />
            </div>
          </div>
        )}
      </div>

      <form className="composer" onSubmit={submit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={hasDocuments ? 'Ask a question…' : 'Upload a document first'}
          aria-label="Question"
          disabled={!hasDocuments}
        />
        <button className="primary send" disabled={!!blocked || !question.trim()} title={blocked ?? undefined}>
          Ask <span aria-hidden>↑</span>
        </button>
      </form>
    </section>
  )
}
