// MAIN AREA (retrieval_service): ask questions about the selected collection.

import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { ChatResponse, Collection, Turn } from '../../types'
import Logo from '../../shared/Logo'
import AnswerMessage from './AnswerMessage'

type Message = Turn & { response?: ChatResponse; error?: boolean }

interface Props {
  collection: Collection
  onUpload?: () => void // opens the documents drawer
}

export default function ChatPanel({ collection, onUpload }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [thinking, setThinking] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const list = useRef<HTMLDivElement>(null)
  const hasDocuments = collection.ready_count > 0
  const empty = messages.length === 0

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

  const composer = (
    <form className="composer" onSubmit={submit}>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder={hasDocuments ? `Ask about the documents in ${collection.name}…` : 'Upload a document first'}
        aria-label="Question"
        disabled={!hasDocuments}
      />
      <button
        className="send"
        disabled={!!blocked || !question.trim()}
        title={blocked ?? 'Ask'}
        aria-label="Ask"
      >
        <span aria-hidden>↑</span>
      </button>
    </form>
  )

  return (
    <section className={`chat ${empty ? 'is-empty' : ''}`} aria-label={`Ask ${collection.name}`}>
      <div className="messages" ref={list} aria-live="polite">
        {empty && (
          <div className="chat-empty">
            <Logo size={56} className="hero-icon" />
            {hasDocuments ? (
              <>
                <h2>Ask anything about the documents in {collection.name}.</h2>
                <p>Answers cite their sources. Open “How this answer was made” to see each step.</p>
                {composer}
                {suggestions.length > 0 && (
                  <div className="suggestions">
                    {suggestions.map((s) => (
                      <button key={s} className="chip" onClick={() => ask(s)}>{s}</button>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <>
                <h2>No documents to ask yet.</h2>
                <p>Answers only come from the documents in {collection.name}. Upload one to get started.</p>
                {onUpload && <button className="primary big" onClick={onUpload}>Upload documents</button>}
              </>
            )}
          </div>
        )}
        {!empty && (
          <div className="thread">
            {messages.map((m, i) =>
              m.role === 'user' ? (
                <div key={i} className="msg user">{m.content}</div>
              ) : (
                <AnswerMessage key={i} id={`m${i}`} text={m.content} response={m.response} error={m.error} />
              ),
            )}
            {thinking && (
              <div className="turn" role="status">
                <Logo size={30} className="avatar thinking-avatar" />
                <div className="msg assistant thinking">
                  <span className="thinking-label">Searching your documents and writing an answer…</span>
                  <span className="skeleton w80" />
                  <span className="skeleton w60" />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      {!empty && <div className="composer-dock">{composer}</div>}
    </section>
  )
}
