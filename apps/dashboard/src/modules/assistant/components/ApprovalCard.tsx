import { ShieldAlert } from 'lucide-react'
import type { PendingApproval, ToolDecision } from '@/modules/assistant/types/assistant'

/** Write tool calls waiting for the operator: approve or reject each before the agent runs them. */
export default function ApprovalCard({ approval, onDecide }: { approval: PendingApproval; onDecide: (d: ToolDecision[]) => void }) {
  const all = (decision: ToolDecision['decision']) =>
    onDecide(approval.requests.map((r) => ({ tool_call_id: r.tool_call_id, decision })))

  return (
    <div className="mt-2 rounded-xl border border-warning/50 bg-warning/5 p-3">
      <div className="mb-2 flex items-center gap-2 text-xs font-bold text-foreground">
        <ShieldAlert size={14} className="text-warning" />
        <span>Cần duyệt {approval.requests.length} thao tác thay đổi hệ thống</span>
      </div>
      <div className="flex flex-col gap-1.5">
        {approval.requests.map((r) => (
          <div key={r.tool_call_id} className="rounded-lg border border-border/60 bg-background px-3 py-1.5">
            <code className="text-xs font-mono font-semibold text-foreground">{r.name}</code>
            <pre className="mt-0.5 font-mono text-[11px] text-muted-foreground whitespace-pre-wrap">{JSON.stringify(r.args, null, 2)}</pre>
          </div>
        ))}
      </div>
      <div className="mt-2.5 flex gap-2">
        <button type="button" onClick={() => all('approve')} className="rounded-lg bg-brand px-3 py-1 text-xs font-semibold text-white hover:bg-brand/90 cursor-pointer">
          Duyệt
        </button>
        <button type="button" onClick={() => all('reject')} className="rounded-lg border border-border px-3 py-1 text-xs font-semibold text-foreground hover:bg-muted cursor-pointer">
          Từ chối
        </button>
      </div>
      <p className="mt-2 text-[10.5px] text-muted-foreground">Hoặc nhắn yêu cầu khác trong ô chat để thay đổi thao tác.</p>
    </div>
  )
}
