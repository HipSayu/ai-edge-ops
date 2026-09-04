import { useState, useRef, useEffect } from 'react'
import { Bot, User } from 'lucide-react'
import ChatInputForm from '@/components/ChatInputForm'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I am your AI Edge Operations Assistant. I can help you query device telemetry, manage inference pipelines, or troubleshoot fleet health. How can I assist you today?',
      timestamp: '09:00:12'
    },
    {
      id: '2',
      role: 'user',
      content: 'Can you check the thermal status of the Jetson nodes in Sector B?',
      timestamp: '10:15:04'
    },
    {
      id: '3',
      role: 'assistant',
      content: 'I have analyzed the telemetry for the 4 active Jetson nodes in Sector B. Currently, all temperatures are within safe operating limits (average 61°C). However, Node EDG-7041 showed a brief spike to 76°C about 20 minutes ago before stabilizing. Would you like me to increase the cooling fan curve for that node?',
      timestamp: '10:15:22'
    },
    {
      id: '4',
      role: 'user',
      content: 'Yes, please apply the aggressive cooling profile to EDG-7041.',
      timestamp: '10:18:10'
    },
    {
      id: '5',
      role: 'assistant',
      content: 'Done. I have dispatched the profile=aggressive configuration to EDG-7041. The daemon has acknowledged the change and fan speeds are now scaling up.',
      timestamp: '10:18:15'
    }
  ])
  
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!input.trim()) return

    if (input.trim() === '/clear') {
      setMessages([])
      setInput('')
      return
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
    }

    setMessages(prev => [...prev, userMsg])
    const currentInput = input
    setInput('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      let replyContent = "I've analyzed your request regarding '" + currentInput.substring(0, 20) + "...'. All systems are currently operating within normal parameters. Is there a specific edge node you'd like me to investigate?"
      
      if (currentInput.startsWith('/diagnose')) {
        replyContent = 'Initiating full diagnostic sweep... \n\n[ OK ] Network Latency\n[ OK ] Memory Allocation\n[ OK ] Thermal Sensors\n[ OK ] TensorRT Engine Status\n\nNo anomalies detected.'
      } else if (currentInput.startsWith('/deploy')) {
        replyContent = 'Preparing rollout pipeline. Please specify the target group and model version (e.g., group=factory-floor model=yolov8n-v2.1).'
      }

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: replyContent,
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
      }
      setMessages(prev => [...prev, aiMsg])
      setIsTyping(false)
    }, 1200)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)', marginBottom: -20 }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '10px 0 24px', display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 840, margin: '0 auto', width: '100%' }}>
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




