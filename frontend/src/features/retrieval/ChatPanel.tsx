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
  const list = useRef<HTMLDivElement>(null)

  // Scroll only the message list, never the page.
  useEffect(() => {
    list.current?.scrollTo({ top: list.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  async function ask(e: FormEvent) {
    e.preventDefault()
    const q = question.trim()
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

  return (
    <section className="panel chat">
      <div className="panel-head">
        <h2>Ask</h2>
        <span className="muted">{collection.name}</span>
        {messages.length > 0 && <button className="link push-right" onClick={() => setMessages([])}>New chat</button>}
      </div>

      <div className="messages" ref={list}>
        {messages.length === 0 && (
          <div className="empty chat-empty">
            <p><strong>Ask anything about the documents in {collection.name}.</strong></p>
            <p>Answers cite their sources. Open “How this answer was made” to see each step.</p>
          </div>
        )}
        {messages.map((m, i) =>
          m.role === 'user' ? (
            <div key={i} className="msg user">{m.content}</div>
          ) : (
            <AnswerMessage key={i} id={`m${i}`} text={m.content} response={m.response} error={m.error} />
          ),
        )}
        {thinking && <div className="msg assistant thinking">Searching and writing an answer…</div>}
      </div>

      <form className="ask" onSubmit={ask}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question…"
          aria-label="Question"
        />
        <button className="primary" disabled={!question.trim() || thinking}>Ask</button>
      </form>
    </section>
  )
}
