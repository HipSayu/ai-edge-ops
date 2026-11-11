import { useEffect, useRef, useState, type CSSProperties } from 'react'
import {
  BookOpen,
  Camera,
  ClipboardList,
  Eraser,
  FileText,
  History,
  MessageSquare,
  Plus,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react'
import ApprovalPrompt from '@/components/chat/ApprovalPrompt'
import ChatComposer, { type SlashCommand } from '@/components/chat/ChatComposer'
import MessageBubble from '@/components/chat/MessageBubble'
import { storage } from '@/helpers/storage'
import { useAuth } from '@/contexts/AuthContext'
import { PanelFrame } from '@/components/ui'
import { activityLabel } from '@/constants/labels'
import { useChat, type ChatSession } from '@/hooks/useChat'

export default function ChatPanel({
  onClose,
  collapsed,
  onToggleCollapse,
  className,
  style,
}: {
  onClose?: () => void
  collapsed: boolean
  onToggleCollapse: () => void
  className?: string
  style?: CSSProperties
}) {
  const { canOperate } = useAuth()
  const { messages, activity, busy, send, decide, reset, loadSession, currentSessionId } = useChat()
  const [showHistory, setShowHistory] = useState(false)
  const [historyList, setHistoryList] = useState<ChatSession[]>([])
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!showHistory) {
      bottom.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, activity, showHistory])

  // Sync history list when toggling history drawer
  const toggleHistory = () => {
    if (!showHistory) {
      try {
        const raw = storage.get('ppe_chat_sessions_history')
        setHistoryList(raw ? JSON.parse(raw) : [])
      } catch {
        setHistoryList([])
      }
    }
    setShowHistory(!showHistory)
  }

  const deleteSession = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    const updated = historyList.filter((s) => s.id !== id)
    setHistoryList(updated)
    storage.set('ppe_chat_sessions_history', JSON.stringify(updated))
  }

  // A proposal waiting for the user's decision takes the place of the message box
  const pending = messages.flatMap((m) => (m.approvals ?? []).filter((a) => a.state === 'pending').map((approval) => ({ messageId: m.id, approval })))[0]

  // What "/" offers in the message box: actions, and ready-made questions
  const commands: SlashCommand[] = [
    { name: 'new', title: 'New chat', hint: 'Start a fresh conversation', icon: <Plus size={14} />, run: reset },
    { name: 'history', title: 'Past chats', hint: 'Open your earlier conversations', icon: <History size={14} />, run: toggleHistory },
    { name: 'summary', title: 'Violations this hour', hint: 'A summary of the past hour', icon: <ClipboardList size={14} />, prompt: 'Tóm tắt vi phạm trong 1 giờ qua' },
    { name: 'worst', title: 'Most violations', hint: 'Which camera has the most', icon: <Camera size={14} />, prompt: 'Camera nào có nhiều vi phạm an toàn nhất?' },
    { name: 'rules', title: 'Safety rules', hint: 'Look up the regulations', icon: <BookOpen size={14} />, prompt: 'Quy định về mũ bảo hộ là gì?' },
    ...(canOperate
      ? [{ name: 'report', title: 'Safety report', hint: 'Write a report for the past hour', icon: <FileText size={14} />, prompt: 'Xuất báo cáo an toàn trong 1 giờ qua' }]
      : []),
  ]

  const actions = (
    <>
      <button
        onClick={toggleHistory}
        title={showHistory ? 'Return to Chat' : 'Conversation History'}
        className={`rounded p-1 transition-colors cursor-pointer ${
          showHistory ? 'bg-cyan-600 text-white' : 'text-dim hover:bg-panel hover:text-ink'
        }`}
      >
        <History size={12} />
      </button>
      <button
        onClick={reset}
        title="New Conversation"
        disabled={messages.length === 0}
        className="rounded p-1 text-dim hover:bg-panel hover:text-ink disabled:opacity-30 disabled:pointer-events-none cursor-pointer transition-colors"
      >
        <Eraser size={12} />
      </button>
      {onClose && (
        <button
          onClick={onClose}
          title="Close"
          className="rounded p-1 text-dim hover:bg-panel hover:text-ink cursor-pointer transition-colors"
        >
          <X size={12} />
        </button>
      )}
    </>
  )

  return (
    <PanelFrame
      title="PPE AI Assistant"
      icon={
        <div className="grid size-4 place-items-center rounded bg-cyan-500/15 text-cyan-400">
          <Sparkles size={11} />
        </div>
      }
      badge={<span className="ml-0.5 size-1.5 shrink-0 animate-pulse rounded-full bg-emerald-400" />}
      actions={actions}
      collapsed={collapsed}
      onToggleCollapse={onToggleCollapse}
      className={className}
      style={style}
    >
      {/* Main Body: Sliding History Overlay OR Direct Chat Stream */}
      {showHistory ? (
        /* History Sliding Overlay View */
        <div className="scroll-thin min-h-0 flex-1 overflow-y-auto divide-y divide-line/60 p-2 animate-in fade-in duration-150">
          <div className="flex items-center justify-between pb-1.5 mb-1 px-1">
            <span className="font-bold text-[10px] text-dim uppercase tracking-wider">
              Past Conversations ({historyList.length})
            </span>
            <button
              onClick={() => setShowHistory(false)}
              className="text-[10px] text-cyan-400 hover:underline cursor-pointer"
            >
              Back to chat
            </button>
          </div>

          {historyList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center text-dim">
              <History size={24} className="mb-2 text-dim/50" />
              <p className="font-semibold text-xs text-ink">No conversation records</p>
              <p className="text-[10px] text-dim mt-0.5">
                Past conversations with AI Assistant will automatically archive here.
              </p>
            </div>
          ) : (
            historyList.map((s) => (
              <div
                key={s.id}
                onClick={() => {
                  loadSession(s)
                  setShowHistory(false)
                }}
                className={`group flex items-start justify-between gap-2 p-2 rounded hover:bg-panel2/80 transition-colors cursor-pointer ${
                  currentSessionId === s.id ? 'bg-cyan-500/10 border border-cyan-500/30' : ''
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <MessageSquare size={12} className="text-cyan-400 shrink-0" />
                    <p className="font-semibold text-ink text-xs truncate">{s.title}</p>
                  </div>
                  <div className="flex items-center gap-2.5 text-[10px] text-dim font-mono mt-0.5">
                    <span>{s.messages.length} msgs</span>
                    <span>{new Date(s.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <button
                  onClick={(e) => deleteSession(e, s.id)}
                  title="Delete record"
                  className="rounded p-1 text-dim hover:text-rose-400 hover:bg-panel opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                >
                  <Trash2 size={11} />
                </button>
              </div>
            ))
          )}
        </div>
      ) : (
        /* Regular Active Chat Stream View */
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <div className="scroll-thin min-h-0 flex-1 space-y-2.5 overflow-y-auto p-2.5">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-4 text-center">
                <div className="grid size-8 place-items-center rounded-lg bg-cyan-500/10 text-cyan-400 mb-2 border border-cyan-500/20">
                  <Sparkles size={16} />
                </div>
                <h4 className="font-semibold text-ink text-xs">PPE AI Assistant</h4>
                <p className="mt-0.5 text-[10px] text-dim max-w-[220px]">
                  Ask about violations, safety regulations or reports, or attach a photo to check it. Type / for shortcuts.
                </p>

              </div>
            )}

            {messages.map((m, idx) => {
              const isLastAssistant = idx === messages.length - 1 && m.role === 'assistant'
              return (
                <div key={m.id} className="space-y-1.5">
                  {/* A plain status above the reply being prepared; it goes once the text starts to flow */}
                  {isLastAssistant && busy && !m.content && (
                    <div className="flex items-center gap-2 pl-8 text-[11px] text-dim">
                      <span className="flex gap-0.5" aria-hidden>
                        {[0, 1, 2].map((i) => (
                          <span key={i} className="size-1 animate-bounce rounded-full bg-cyan-400" style={{ animationDelay: `${i * 150}ms` }} />
                        ))}
                      </span>
                      <span>{activityLabel(activity)}</span>
                    </div>
                  )}

                  {/* Message Bubble - only show if there's content or it has finished */}
                  {(!isLastAssistant || m.content || !busy) && (
                    <MessageBubble message={m} />
                  )}
                </div>
              )
            })}

            <div ref={bottom} />
          </div>

          {pending ? (
            <ApprovalPrompt approval={pending.approval} onDecide={(approve) => decide(pending.messageId, pending.approval.id, approve)} />
          ) : (
            <ChatComposer busy={busy} commands={commands} onSend={(text, options) => void send(text, options)} />
          )}
        </div>
      )}
    </PanelFrame>
  )
}
