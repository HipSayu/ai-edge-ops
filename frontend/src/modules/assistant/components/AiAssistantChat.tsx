import { useState } from 'react'
import { Bot, Send, Sparkles, User } from 'lucide-react'
import { initialChat, suggestedQuestions, type ChatMessage } from '@/mock\incidents'

const CANNED_REPLY =
  'Based on real-time telemetry across the past 30 minutes, CAM-03 (Main Factory Floor) logged the highest violation frequency — primarily missing hard hats and protective gloves in Sector C, Bays 2–4. Facility-wide PPE compliance is currently holding at 90.3%.'

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

      <div className="av-suggested-row">
        {suggestedQuestions.map((q) => (
          <button key={q} className="av-suggested-chip" onClick={() => send(q)}>
            <Sparkles size={12} color="var(--accent)" />
            <span>{q}</span>
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
