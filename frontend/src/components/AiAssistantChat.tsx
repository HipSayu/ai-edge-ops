import { useState } from 'react'
import { initialChat, suggestedQuestions, type ChatMessage } from '../mock/incidents'

const CANNED_REPLY =
  'Dựa trên dữ liệu 30 phút gần nhất, CAM-03 (Sàn nhà máy) có tỷ lệ sự cố cao nhất — chủ yếu là thiếu mũ bảo hộ và găng tay. Tỷ lệ tuân thủ chung toàn bộ khu vực đang duy trì ở mức 90.3%.'

export default function AiAssistantChat({ floating }: { floating?: boolean }) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialChat)
  const [input, setInput] = useState('')

  function send(text: string) {
    if (!text.trim()) return
    const userMsg: ChatMessage = { id: Date.now(), role: 'user', text }
    const aiMsg: ChatMessage = { id: Date.now() + 1, role: 'assistant', text: CANNED_REPLY }
    setMessages((prev) => [...prev, userMsg, aiMsg])
    setInput('')
  }

  return (
    <section className={`av-panel av-assistant${floating ? ' floating' : ''}`}>
      <div className="av-panel-header">
        <span className="av-panel-title">Trợ lý giám sát AI</span>
      </div>

      <div className="av-chat-log">
        {messages.map((m) => (
          <div key={m.id} className={`av-chat-msg ${m.role}`}>
            <span className="av-chat-role">{m.role === 'user' ? 'Bạn' : 'AI'}</span>
            <p>{m.text}</p>
          </div>
        ))}
      </div>

      <div className="av-suggested-row">
        {suggestedQuestions.map((q) => (
          <button key={q} className="av-suggested-chip" onClick={() => send(q)}>
            {q}
          </button>
        ))}
      </div>

      <form
        className="av-chat-input-row"
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Hỏi về camera, sự cố, hoặc mức độ tuân thủ…"
        />
        <button type="submit" className="av-btn-primary">
          Gửi
        </button>
      </form>
    </section>
  )
}
