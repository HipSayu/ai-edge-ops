import { ArrowUpRight, Bot, FileText, User } from 'lucide-react'
import ApprovalCard from '@/components/chat/ApprovalCard'
import AuthImage from '@/components/ui/AuthImage'
import Markdown from '@/components/chat/Markdown'
import { downloadWithAuth } from '@/helpers/media'
import type { ChatMessage } from '@/hooks/useChat'

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const mine = message.role === 'user'

  return (
    <div className={`flex items-start gap-2 ${mine ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className={`grid size-6 shrink-0 place-items-center rounded text-xs font-semibold ${
          mine
            ? 'bg-blue-600 text-white'
            : 'bg-panel2 border border-line text-blue-400'
        }`}
      >
        {mine ? <User size={12} /> : <Bot size={13} />}
      </div>

      <div
        className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed shadow-xs ${
          mine
            ? 'bg-blue-600 text-white'
            : message.failed
              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              : 'bg-panel2/90 border border-line text-ink'
        }`}
      >
        {message.images && (
          <div className="mb-1.5 flex flex-wrap gap-1.5">
            {message.images.map((id) => (
              <AuthImage key={id} src={`/api/chat/images/${id}`} className="max-h-40 max-w-full rounded-md border border-white/20 object-contain" />
            ))}
          </div>
        )}
        <div className="break-words">
          {mine ? message.content : <Markdown source={message.content} />}
        </div>

        {/* A pending one is asked below the conversation (ApprovalPrompt), not shown twice here */}
        {message.approvals?.filter((a) => a.state !== 'pending').map((a) => (
          <ApprovalCard key={a.id} approval={a} />
        ))}

        {message.reportUrl && (
          <button
            type="button"
            onClick={() => void downloadWithAuth(message.reportUrl!, 'bao-cao.docx')}
            className="mt-2 flex w-full cursor-pointer items-center justify-between rounded border border-line bg-panel p-2 font-medium text-ink transition-all hover:border-brand/50 hover:bg-panel2"
          >
            <div className="flex items-center gap-1.5">
              <FileText size={13} className="text-blue-400" />
              <span className="text-[11px] font-semibold">Download Safety Report</span>
            </div>
            <ArrowUpRight size={12} className="text-dim" />
          </button>
        )}
      </div>
    </div>
  )
}
