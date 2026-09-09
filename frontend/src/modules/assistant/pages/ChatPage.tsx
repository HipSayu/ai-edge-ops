import { useState, useRef, useEffect } from 'react'
import { Bot, User } from 'lucide-react'
import ChatInputForm from '@/modules/assistant/components/ChatInputForm'
import { assistantService } from '@/shared/api/services/assistant'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    assistantService.listMessages()
      .then((items) => setMessages(items.map((message) => ({
        id: String(message.id),
        role: message.role,
        content: message.text,
        timestamp: message.timestamp ?? '',
      }))))
      .catch(() => setMessages([]))
  }, [])
  
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!input.trim()) return

    if (input.trim() === '/clear') {
      setMessages([])
      setInput('')
      return
    }

    const currentInput = input.trim()
    setInput('')
    setIsTyping(true)
    try {
      const response = await assistantService.sendMessage(currentInput)
      setMessages((prev) => [...prev, {
        id: String(response.id),
        role: response.role,
        content: response.text,
        timestamp: response.timestamp ?? '',
      }])
    } catch {
      setMessages((prev) => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Unable to reach the assistant backend.',
        timestamp: '',
      }])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, marginBottom: -20 }}>
      <div className="av-chat-scroll-area" style={{ flex: 1, overflowY: 'auto', padding: '10px 0 24px', display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 840, margin: '0 auto', width: '100%' }}>
        {messages.map(msg => (
          <div key={msg.id} style={{ display: 'flex', gap: 16, flexDirection: msg.role === 'user' ? 'row-reverse' : 'row', padding: '0 24px' }}>
            <div style={{
              width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: msg.role === 'assistant' ? 'var(--accent-dim)' : 'var(--panel-2)',
              border: '1px solid',
              borderColor: msg.role === 'assistant' ? 'var(--accent)' : 'var(--border)',
              color: msg.role === 'assistant' ? 'var(--accent)' : 'var(--text)'
            }}>
              {msg.role === 'assistant' ? <Bot size={18} /> : <User size={18} />}
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxWidth: '75%', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-main)' }}>{msg.role === 'assistant' ? 'AI Copilot' : 'You'}</span>
                <span className="av-mono" style={{ fontSize: 11, color: 'var(--text-faint)' }}>{msg.timestamp}</span>
              </div>
              <div style={{
                padding: '14px 18px',
                borderRadius: 16,
                background: msg.role === 'user' ? 'var(--accent)' : 'var(--panel)',
                color: msg.role === 'user' ? '#fff' : 'var(--text)',
                border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
                boxShadow: msg.role === 'assistant' ? 'none' : '0 2px 8px rgba(0,0,0,0.04)',
                fontSize: 14,
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap'
              }}>
                {msg.content}
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div style={{ display: 'flex', gap: 16, flexDirection: 'row', padding: '0 24px' }}>
            <div style={{ width: 36, height: 36, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--accent-dim)', border: '1px solid var(--accent)', color: 'var(--accent)' }}>
              <Bot size={18} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-start' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-main)' }}>AI Copilot</span>
              </div>
              <div style={{ padding: '14px 18px', borderRadius: 16, background: 'var(--panel)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 4 }}>
                <span className="av-dot pulse" style={{ background: 'var(--text-faint)' }} />
                <span className="av-dot pulse" style={{ background: 'var(--text-faint)', animationDelay: '0.2s' }} />
                <span className="av-dot pulse" style={{ background: 'var(--text-faint)', animationDelay: '0.4s' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} style={{ height: 20 }} />
      </div>

      <div style={{ padding: '0 24px 24px', maxWidth: 888, margin: '0 auto', width: '100%', position: 'relative' }}>
        <ChatInputForm 
          input={input}
          setInput={setInput}
          onSend={handleSend}
          compact={false}
        />
        <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-faint)', marginTop: 12 }}>
          AI Copilot can make mistakes. Verify critical actions before executing.
        </div>
      </div>
    </div>
  )
}




