import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { ShieldQuestion } from 'lucide-react'
import { describeProposal } from '@/helpers/proposal'
import type { Approval } from '@/hooks/useChat'

// A change the assistant proposed, asked like a permission prompt: it takes the place of the message box until the user
// answers, so nothing else can be typed meanwhile. Up/Down or 1/2 choose, Enter confirms, Esc rejects.
const OPTIONS = [
  { approve: true, label: 'Yes, apply it' },
  { approve: false, label: 'No, leave it as it is' },
]

export default function ApprovalPrompt({ approval, onDecide }: { approval: Approval; onDecide: (approve: boolean) => void }) {
  const [pick, setPick] = useState(0)
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    box.current?.focus()
  }, [approval.id])

  const { title, details } = describeProposal(approval.tool, approval.args, approval.summary)

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      setPick((i) => (i + 1) % OPTIONS.length)
    } else if (event.key === '1' || event.key === '2') {
      onDecide(OPTIONS[Number(event.key) - 1].approve)
    } else if (event.key === 'Enter') {
      event.preventDefault()
      onDecide(OPTIONS[pick].approve)
    } else if (event.key === 'Escape') {
      onDecide(false)
    }
  }

  return (
    <div
      ref={box}
      tabIndex={0}
      onKeyDown={onKeyDown}
      role="dialog"
      aria-label="Approve a change"
      className="shrink-0 border-t border-amber-500/40 bg-panel p-2 outline-none"
    >
      <div className="rounded-xl border border-amber-500/40 bg-panel2/60">
        <div className="flex items-center gap-1.5 border-b border-amber-500/20 px-3 py-2">
          <ShieldQuestion size={14} className="text-amber-400" />
          <span className="text-xs font-semibold text-ink">Do you want the assistant to make this change?</span>
        </div>
        <div className="space-y-1.5 px-3 py-2">
          <p className="text-xs font-semibold text-ink">{title}</p>
          {details.length > 0 && (
            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-[11px]">
              {details.map(([label, value]) => (
                <div key={label} className="contents">
                  <dt className="text-dim">{label}</dt>
                  <dd className="break-words text-ink">{value}</dd>
                </div>
              ))}
            </dl>
          )}
          {approval.result && <p className="text-[11px] text-rose-400">{approval.result}</p>}
        </div>
        <ul className="space-y-0.5 px-1.5 pb-1.5" role="listbox">
          {OPTIONS.map((option, i) => (
            <li key={option.label} role="option" aria-selected={i === pick}>
              <button
                type="button"
                onMouseEnter={() => setPick(i)}
                onClick={() => onDecide(option.approve)}
                className={`flex w-full cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs transition-colors ${
                  i === pick ? 'bg-panel text-ink ring-1 ring-cyan-500/50' : 'text-dim hover:bg-panel'
                }`}
              >
                <span className={`grid size-4 place-items-center rounded text-[10px] font-mono ${i === pick ? 'bg-cyan-500/20 text-cyan-300' : 'bg-black/30'}`}>
                  {i + 1}
                </span>
                {option.label}
              </button>
            </li>
          ))}
        </ul>
        <p className="border-t border-line/60 px-3 py-1 text-[10px] text-dim">↑↓ to choose · Enter to confirm · Esc to reject</p>
      </div>
    </div>
  )
}
