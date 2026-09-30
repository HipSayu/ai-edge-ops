import { useState, useRef, useEffect } from 'react'
import { X, Bot, Sparkles } from 'lucide-react'
import ChatInputForm from '@/modules/assistant/components/ChatInputForm'
import { assistantService } from '@/modules/assistant/services/assistant'

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
    <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-3">
      {isOpen && (
        <div className="flex h-[480px] max-h-[calc(100vh-7rem)] w-[360px] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-xl border border-border bg-card">
          <div className="flex shrink-0 items-center justify-between border-b border-border px-4 py-3">
            <div className="flex items-center gap-2.5">
              <div className="flex size-8 items-center justify-center rounded-lg bg-brand/10 text-brand">
                <Sparkles size={16} />
              </div>
              <div className="leading-tight">
                <h4 className="text-sm font-semibold text-foreground">SOC Copilot</h4>
                <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                  <span className="size-1.5 rounded-full bg-success" /> Online
                </span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="flex size-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <X size={18} />
            </button>
          </div>

          <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex items-start gap-2 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                {msg.sender === 'ai' && (
                  <div className="flex size-6 shrink-0 items-center justify-center rounded-md bg-brand/10 text-brand">
                    <Bot size={14} />
                  </div>
                )}
                <div
                  className={`max-w-[80%] whitespace-pre-wrap rounded-xl px-3 py-2 text-sm ${
                    msg.sender === 'user' ? 'bg-brand text-brand-foreground' : 'bg-muted text-foreground'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex items-start gap-2">
                <div className="flex size-6 shrink-0 items-center justify-center rounded-md bg-brand/10 text-brand">
                  <Bot size={14} />
                </div>
                <div className="flex items-center gap-1 rounded-xl bg-muted px-3 py-3">
                  <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground" />
                  <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0.2s]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0.4s]" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="shrink-0 p-3">
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
        className="flex size-12 cursor-pointer items-center justify-center rounded-full bg-brand text-brand-foreground transition-opacity hover:opacity-90"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close AI Assistant' : 'Open AI Assistant'}
        title={isOpen ? 'Close AI Assistant' : 'Open AI Assistant'}
      >
        {isOpen ? <X size={22} /> : <Bot size={24} strokeWidth={2.1} />}
      </button>
    </div>
  )
}
