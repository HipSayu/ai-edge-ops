import { ShieldQuestion } from 'lucide-react'
import { describeProposal } from '@/helpers/proposal'
import type { Approval } from '@/hooks/useChat'

// A change the assistant proposed, kept in the conversation as a record: what it wanted to do and how it ended. The
// decision itself is asked by ApprovalPrompt, which takes the place of the message box while one is waiting.
export default function ApprovalCard({ approval }: { approval: Approval }) {
  const { title } = describeProposal(approval.tool, approval.args, approval.summary)
  const pending = approval.state === 'pending'

  return (
    <div className="mt-2 overflow-hidden rounded-lg border border-amber-500/40 bg-panel shadow-sm">
      <div className="flex items-center gap-1.5 border-b border-amber-500/20 bg-amber-500/10 px-2.5 py-1.5">
        <ShieldQuestion size={13} className="text-amber-400" />
        <span className="text-[11px] font-semibold text-amber-200">Approval needed</span>
      </div>
      <div className="space-y-1.5 px-2.5 py-2">
        <p className="text-[11px] font-medium text-ink">{title}</p>
        <p className={`text-[11px] ${approval.state === 'approved' ? 'text-emerald-400' : approval.state === 'rejected' ? 'text-dim' : 'text-amber-300'}`}>
          {approval.result ?? (pending ? 'Waiting for your decision' : approval.state)}
        </p>
      </div>
    </div>
  )
}
