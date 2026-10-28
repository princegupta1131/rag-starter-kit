// RIGHT PANEL — talks to retrieval_service.
// Sends the question + recent conversation, shows the grounded answer.

import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client.js'
import AnswerMessage from './AnswerMessage.jsx'

export default function ChatPanel() {
  const [messages, setMessages] = useState([]) // {role, content, response?}
  const [question, setQuestion] = useState('')
  const [thinking, setThinking] = useState(false)
  const bottom = useRef(null)

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, thinking])

  async function ask(e) {
    e.preventDefault()
    const q = question.trim()
    if (!q || thinking) return
    const history = messages.map(({ role, content }) => ({ role, content }))
    setMessages((m) => [...m, { role: 'user', content: q }])
    setQuestion('')
    setThinking(true)
    try {
      const response = await api.chat(q, history)
      setMessages((m) => [...m, { role: 'assistant', content: response.answer, response }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: `Error: ${err.message}`, response: { status: 'error' } }])
    } finally {
      setThinking(false)
    }
  }

  return (
    <section className="panel chat">
      <div className="panel-head">
        <h2>2 · Retrieval</h2>
        <span className="muted">answers out</span>
        {messages.length > 0 && <button className="link push-right" onClick={() => setMessages([])}>New chat</button>}
      </div>

      <div className="messages">
        {messages.length === 0 && (
          <div className="empty chat-empty">
            <p><strong>Ask anything about your documents.</strong></p>
            <p>Every answer cites its sources. Open “How this answer was made” to see each pipeline step.</p>
          </div>
        )}
        {messages.map((m, i) =>
          m.role === 'user'
            ? <div key={i} className="msg user">{m.content}</div>
            : <AnswerMessage key={i} message={m} />,
        )}
        {thinking && <div className="msg assistant thinking">Searching documents and writing an answer…</div>}
        <div ref={bottom} />
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
