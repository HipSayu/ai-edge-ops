import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Bot, Sparkles } from 'lucide-react'
import ChatInputForm from '@/components\ChatInputForm'

interface Message {
  id: string
  text: string
  sender: 'user' | 'ai'
  timestamp: Date
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Xin chào! Tôi là Edge AI SOC Agent. Tôi có thể giúp gì cho bạn trong việc giám sát hệ thống hôm nay?',
      sender: 'ai',
      timestamp: new Date()
    }
  ])
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

    // Mock AI response
    setTimeout(() => {
      setIsTyping(false)
      
      const responses = [
        'Hệ thống Camera đang hoạt động ổn định. Băng thông hiện tại là 1.2 GB/s.',
        'Tôi đã phân tích 4 node. Node số 2 đang có tải GPU hơi cao (85%), bạn có muốn xem chi tiết không?',
        'Dữ liệu real-time telemetry cho thấy không có sự cố bảo mật nào trong 24h qua.',
        'Đã cập nhật biểu đồ giám sát thành công. Bạn cần tôi kiểm tra luồng video nào nữa không?'
      ]
      
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: responses[Math.floor(Math.random() * responses.length)],
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages((prev) => [...prev, aiMsg])
    }, 1500)
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
        title="Trợ lý AI"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>
    </div>
  )
}



