import { useState } from 'react'
import { Bot, Send, User } from 'lucide-react'
import { assistantService } from '@/modules/assistant/services/assistant'

type ChatMessage = {
  id: number
  role: 'user' | 'assistant'
  text: string
  timestamp?: string
}

export default function AiAssistantChat({ floating }: { floating?: boolean }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')

  function send(text: string) {
    if (!text.trim()) return
    setMessages((prev) => [...prev, { id: Date.now(), role: 'user', text }])
    assistantService.sendMessage(text).then((message) => setMessages((prev) => [...prev, message])).catch(() => undefined)
    setInput('')
  }

  return (
    <section className={`av-panel av-assistant${floating ? ' floating' : ''}`}>
      <div className="av-panel-header">
        <span className="av-panel-title">
          <Bot size={16} color="var(--accent)" />
          <span>AI Vision Operations Copilot</span>
        </span>
        <span className="av-panel-sub">Context: 5 Cameras • YOLOv11</span>
      </div>

      <div className="av-chat-log">
        {messages.map((m) => (
          <div key={m.id} className={`av-chat-msg ${m.role}`}>
            <span className="av-chat-role">
              {m.role === 'user' ? (
                <>
                  <User size={13} />
                  <span>Operator</span>
                </>
              ) : (
                <>
                  <Bot size={13} />
                  <span>Copilot</span>
                </>
              )}
            </span>
            <p>{m.text}</p>
          </div>
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
          placeholder="Ask about camera feeds, incident triage, or safety compliance..."
        />
        <button type="submit" className="av-btn-primary" disabled={!input.trim()}>
          <Send size={15} />
          <span>Send</span>
        </button>
      </form>
    </section>
  )
}
