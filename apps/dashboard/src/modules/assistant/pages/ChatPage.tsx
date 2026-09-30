import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Bot, User, Copy, Check, Cpu, Camera, Loader2, ShieldCheck, Zap, SidebarClose, SidebarOpen } from 'lucide-react'
import ChatInputForm from '@/modules/assistant/components/ChatInputForm'
import ReasoningTrace from '@/modules/assistant/components/ReasoningTrace'
import ApprovalCard from '@/modules/assistant/components/ApprovalCard'
import ConversationList from '@/modules/assistant/components/ConversationList'
import { conversationService } from '@/modules/assistant/services/conversations'
import type { Conversation } from '@/modules/assistant/types/assistant'
import { useChatStream } from '@/modules/assistant/hooks/useChatStream'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'

// ─── Suggestion chips (welcome screen) ────────────────────────────────────────
const QUICK_ACTIONS = [
  { label: 'Cluster Diagnostics', query: '/diagnose', icon: Cpu, desc: 'Analyze health of all edge clusters' },
  { label: 'Camera RTSP Feeds', query: '/cameras', icon: Camera, desc: 'Check live streams & FPS stats' },
  { label: 'Model Deployments', query: '/deploy', icon: Zap, desc: 'Review active YOLOv8 / YOLOv9 pipelines' },
  { label: 'Safety Violations', query: '/safety', icon: ShieldCheck, desc: 'Scan recent PPE & zone events' },
]

// ─── Simple inline markdown renderer ─────────────────────────────────────────
function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i} className="font-semibold text-foreground">{part.slice(2, -2)}</strong>
    if (part.startsWith('*') && part.endsWith('*'))
      return <em key={i}>{part.slice(1, -1)}</em>
    if (part.startsWith('`') && part.endsWith('`'))
      return <code key={i} className="rounded bg-muted px-1 py-0.5 text-[11px] font-mono text-foreground">{part.slice(1, -1)}</code>
    return part
  })
}

function renderMarkdown(text: string) {
  const lines = text.split('\n')
  return lines.map((line, i) => {
    if (line.startsWith('### '))
      return <p key={i} className="mt-3 mb-0.5 text-sm font-bold text-foreground first:mt-0">{renderInline(line.slice(4))}</p>
    if (line.startsWith('## '))
      return <p key={i} className="mt-3 mb-0.5 text-base font-bold text-foreground first:mt-0">{renderInline(line.slice(3))}</p>
    if (line.startsWith('- ') || line.startsWith('* '))
      return <div key={i} className="flex gap-2 my-0.5 text-sm"><span className="mt-0.5 shrink-0 text-muted-foreground">•</span><span>{renderInline(line.slice(2))}</span></div>
    const numMatch = line.match(/^(\d+)\.\s(.+)/)
    if (numMatch)
      return <div key={i} className="flex gap-2 my-0.5 text-sm"><span className="shrink-0 text-muted-foreground">{numMatch[1]}.</span><span>{renderInline(numMatch[2])}</span></div>
    if (line.trim() === '')
      return <div key={i} className="h-2" />
    return <p key={i} className="text-sm leading-relaxed">{renderInline(line)}</p>
  })
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ChatPage() {
  const { clusters } = useEdgeOps()
  const { conversationId } = useParams<{ conversationId?: string }>()
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const refresh = useCallback(() => {
    conversationService.list().then(setConversations).catch(() => undefined)
  }, [])
  useEffect(refresh, [refresh])

  const onCreated = useCallback((id: string) => navigate(`/chat/${id}`, { replace: true }), [navigate])
  const { messages, busy, loading, send, decide } = useChatStream(conversationId, { onCreated, onChanged: refresh })
  const [input, setInput] = useState('')
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const hasConversation = messages.length > 0

  // Auto-scroll as messages and streamed tokens arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const copyMessage = (id: string, text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 1800)
  }

  const handleSend = () => {
    const text = input.trim()
    if (!text) return
    setInput('')
    if (text === '/clear') {
      navigate('/chat')
      return
    }
    void send(text)
  }

  const renameConversation = async (id: string, title: string) => {
    await conversationService.rename(id, title).catch(() => undefined)
    refresh()
  }

  const deleteConversation = async (id: string) => {
    await conversationService.remove(id).catch(() => undefined)
    if (id === conversationId) navigate('/chat')
    refresh()
  }

  const activeConversation = conversationId ? conversations.find(c => c.id === conversationId) : undefined

  return (
    <div className="flex h-full bg-background">
      <ConversationList
        conversations={conversations}
        activeId={conversationId}
        onSelect={(id) => navigate(`/chat/${id}`)}
        onNew={() => navigate('/chat')}
        onRename={renameConversation}
        onDelete={deleteConversation}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((prev) => !prev)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        {/* ── Toolbar ──────────────────────────────────────────────── */}
        <header className="flex h-11 shrink-0 items-center gap-2 border-b border-border/50 bg-background/95 px-3 backdrop-blur-sm">
          {/* Left: sidebar toggle */}
          <button
            type="button"
            onClick={() => setSidebarOpen((prev) => !prev)}
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            className="flex size-7 shrink-0 items-center justify-center rounded-md text-muted-foreground/70 hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
          >
            {sidebarOpen ? <SidebarClose size={15} /> : <SidebarOpen size={15} />}
          </button>

          {/* Center: breadcrumb */}
          <div className="flex min-w-0 flex-1 items-center gap-1.5 text-[13px]">
            <span className="shrink-0 text-muted-foreground/50">AI Copilot</span>
            {activeConversation && (
              <>
                <span className="shrink-0 text-muted-foreground/30">/</span>
                <span className="truncate font-medium text-foreground">
                  {activeConversation.title || 'Untitled'}
                </span>
              </>
            )}
          </div>
        </header>

      {/* ── Content: welcome or messages ────────────────────────────── */}
      <div className="min-h-0 flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            <Loader2 size={20} className="animate-spin" />
          </div>
        ) : !hasConversation ? (

          /* Welcome screen — Claude-style */
          <div className="flex h-full flex-col items-center justify-center gap-8 px-4 py-16">
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="flex size-16 items-center justify-center rounded-2xl bg-brand/10 text-brand ring-1 ring-brand/20">
                <Bot size={30} />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">How can I help you today?</h1>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  Edge Vision AI Copilot · Connected to{' '}
                  <span className="font-semibold text-foreground">{clusters.length}</span> edge clusters
                </p>
              </div>
            </div>

            {/* Suggestion cards — 2×2 grid */}
            <div className="grid w-full max-w-lg grid-cols-2 gap-3">
              {QUICK_ACTIONS.map((action, idx) => {
                const Icon = action.icon
                return (
                  <button
                    key={idx}
                    onClick={() => setInput(action.query)}
                    className="flex flex-col gap-2.5 rounded-xl border border-border bg-card p-4 text-left transition-all hover:border-brand/40 hover:bg-card cursor-pointer"
                  >
                    <div className="flex size-8 items-center justify-center rounded-lg bg-brand/10 text-brand">
                      <Icon size={15} />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-foreground">{action.label}</div>
                      <div className="mt-0.5 text-[11px] leading-snug text-muted-foreground">{action.desc}</div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

        ) : (

          /* Message thread */
          <div className="mx-auto w-full max-w-3xl px-4 py-8 space-y-6">
            {messages.map((msg) => {
              const isAssistant = msg.role === 'assistant'
              return (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 ${isAssistant ? 'items-start' : 'flex-row-reverse items-start'}`}
                >
                  {/* Avatar */}
                  {isAssistant ? (
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand ring-1 ring-brand/20 mt-0.5">
                      <Bot size={15} />
                    </div>
                  ) : (
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-foreground text-background mt-0.5">
                      <User size={15} />
                    </div>
                  )}

                  {/* Message content */}
                  <div className={`group flex max-w-[80%] flex-col gap-1 ${isAssistant ? '' : 'items-end'}`}>
                    {/* Bubble */}
                    <div
                      className={`relative rounded-2xl px-4 py-3 ${
                        isAssistant
                          ? 'bg-transparent text-foreground'
                          : 'bg-muted/70 text-foreground'
                      }`}
                    >
                      {isAssistant && <ReasoningTrace steps={msg.trace} live={msg.streaming} startedAt={msg.startedAt} finishedAt={msg.finishedAt} />}
                      <div className={isAssistant ? `space-y-0.5${msg.error ? ' text-destructive' : ''}` : 'text-sm leading-relaxed whitespace-pre-wrap'}>
                        {isAssistant ? renderMarkdown(msg.content) : msg.content}
                        {msg.streaming && msg.content && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-brand/70 align-middle" />}
                      </div>
                      {msg.approval && <ApprovalCard approval={msg.approval} onDecide={(d) => void decide(msg.id, d)} />}

                      {/* Copy button — assistant only */}
                      {isAssistant && !msg.streaming && (
                        <button
                          onClick={() => copyMessage(msg.id, msg.content)}
                          title="Copy response"
                          className="absolute -bottom-2 right-2 flex size-6 items-center justify-center rounded-md border border-border bg-card text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity hover:bg-muted hover:text-foreground"
                        >
                          {copiedId === msg.id
                            ? <Check size={11} className="text-success" />
                            : <Copy size={11} />
                          }
                        </button>
                      )}
                    </div>

                    {/* Timestamp */}
                    <span className="px-1 text-[10px] text-muted-foreground/60">{msg.timestamp}</span>
                  </div>
                </div>
              )
            })}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ── Input bar ───────────────────────────────────────────────── */}
      <div className="shrink-0 bg-background px-4 pb-4 pt-3">
        <div className="mx-auto max-w-3xl">
          <ChatInputForm
            input={input}
            setInput={setInput}
            onSend={handleSend}
            disabled={busy}
          />
        </div>
        <p className="mt-2 text-center text-[11px] text-muted-foreground/50">
          AI Copilot can make mistakes. Verify critical edge node decisions independently.
        </p>
      </div>
    </div>
    </div>
  )
}
