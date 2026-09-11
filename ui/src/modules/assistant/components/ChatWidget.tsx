import { useState, useRef, useEffect } from 'react'
import { X, Bot, Sparkles } from 'lucide-react'
import ChatInputForm from '@/modules/assistant/components/ChatInputForm'
import { assistantService } from '@/shared/api/services/assistant'

interface Message {
  id: string
  text: string
  sender: 'user' | 'ai'
  timestamp: Date
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300)
    }
  }, [isOpen])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = () => {
    if (!input.trim()) return
    const userMsg: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user',
      timestamp: new Date()
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    assistantService.sendMessage(userMsg.text).then((message) => {
      setMessages((prev) => [...prev, { id: String(message.id), text: message.text, sender: message.role === 'assistant' ? 'ai' : 'user', timestamp: new Date() }])
    }).finally(() => setIsTyping(false))
  }

  return (
    <div className="av-chat-widget-container">
      {isOpen && (
        <div className="av-chat-panel">
          <div className="av-chat-header">
            <div className="av-chat-header-info">
              <div className="av-chat-avatar">
                <Sparkles size={16} />
              </div>
              <div>
                <h4>SOC Copilot</h4>
                <span className="av-chat-status">
                  <span className="av-chat-status-dot"></span> Online
                </span>
              </div>
            </div>
            <button className="av-chat-close" onClick={() => setIsOpen(false)}>
              <X size={20} />
            </button>
          </div>

          <div className="av-chat-body">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`av-chat-msg-row ${
                  msg.sender === 'user' ? 'av-chat-msg-right' : 'av-chat-msg-left'
                }`}
              >
                {msg.sender === 'ai' && (
                  <div className="av-chat-msg-icon">
                    <Bot size={14} />
                  </div>
                )}
                <div
                  className={`av-chat-bubble ${
                    msg.sender === 'user' ? 'av-chat-bubble-user' : 'av-chat-bubble-ai'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="av-chat-msg-row av-chat-msg-left">
                <div className="av-chat-msg-icon">
                  <Bot size={14} />
                </div>
                <div className="av-chat-bubble av-chat-bubble-ai av-chat-typing">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div style={{ padding: 12, background: 'var(--panel-2)', borderTop: '1px solid var(--border)' }}>
            <ChatInputForm 
              input={input}
              setInput={setInput}
              onSend={handleSend}
              compact={true}
            />
          </div>
        </div>
      )}

      <button
        className={`av-chat-toggle-btn ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Đóng trợ lý AI' : 'Mở trợ lý AI'}
        title={isOpen ? 'Đóng trợ lý AI' : 'Mở trợ lý AI'}
      >
        {isOpen ? <X size={23} /> : <Bot size={25} strokeWidth={2.1} />}
      </button>
    </div>
  )
}



