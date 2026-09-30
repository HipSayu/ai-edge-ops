import { useEffect, useState } from 'react'
import { Check, ChevronDown, ChevronRight, Loader2, X } from 'lucide-react'
import type { TraceStep } from '@/modules/assistant/types/assistant'

type ToolStep = Extract<TraceStep, { kind: 'tool' }>

const pretty = (value: unknown) => {
  if (typeof value !== 'string') return JSON.stringify(value, null, 2)
  try {
    return JSON.stringify(JSON.parse(value), null, 2)
  } catch {
    return value
  }
}

/** "node_id: 9046…, hours: 24": the call's arguments at a glance */
const argsSummary = (args: Record<string, unknown>) =>
  Object.entries(args)
    .map(([k, v]) => {
      const text = typeof v === 'string' ? v : JSON.stringify(v)
      return `${k}: ${text.length > 14 ? `${text.slice(0, 12)}…` : text}`
    })
    .join(', ')

const seconds = (from?: number, to?: number) => (from ? Math.max(1, Math.round(((to ?? Date.now()) - from) / 1000)) : 0)

/** Light inline markdown: reasoning summaries use **bold** section titles */
function Prose({ text }: { text: string }) {
  return (
    <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-muted-foreground">
      {text.split(/(\*\*[^*]+\*\*)/).map((part, i) =>
        part.startsWith('**') && part.endsWith('**')
          ? <span key={i} className="font-semibold text-foreground/80">{part.slice(2, -2)}</span>
          : part,
      )}
    </p>
  )
}

function ToolRow({ step }: { step: ToolStep }) {
  const [open, setOpen] = useState(false)
  const summary = argsSummary(step.args)
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="group flex w-full items-center gap-2 rounded-md py-1 text-left text-[13px] text-muted-foreground transition-colors hover:text-foreground cursor-pointer"
      >
        <span className="flex size-4 shrink-0 items-center justify-center">
          {step.status === 'running' && <Loader2 size={13} className="animate-spin" />}
          {step.status === 'success' && <Check size={13} className="text-success" />}
          {step.status === 'error' && <X size={13} className="text-destructive" />}
        </span>
        <span className="font-medium">{step.tool}</span>
        {summary && <span className="truncate font-mono text-[11.5px] text-muted-foreground/60">{summary}</span>}
        <span className="ml-auto opacity-0 transition-opacity group-hover:opacity-100">
          {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        </span>
      </button>
      {open && (
        <div className="mb-2 ml-6 overflow-hidden rounded-lg border border-border/60 bg-muted/30 text-[11.5px]">
          <div className="border-b border-border/60 px-3 py-1 font-semibold text-muted-foreground">Request</div>
          <pre className="max-h-48 overflow-auto whitespace-pre-wrap px-3 py-2 font-mono text-foreground/80">{pretty(step.args)}</pre>
          <div className="border-y border-border/60 px-3 py-1 font-semibold text-muted-foreground">Response</div>
          <pre className="max-h-64 overflow-auto whitespace-pre-wrap px-3 py-2 font-mono text-foreground/80">
            {step.output !== undefined ? pretty(step.output) : 'Đang chạy…'}
          </pre>
        </div>
      )}
    </div>
  )
}

/** Claude-style collapsible trace of one answer: the model's reasoning, what it said while working, and its
 *  tool calls with their results. Open while the answer streams, collapsed once it is done. */
export default function ReasoningTrace({ steps, live, startedAt, finishedAt }: {
  steps: TraceStep[]
  live?: boolean
  startedAt?: number
  finishedAt?: number
}) {
  const [open, setOpen] = useState(!!live)
  const [, tick] = useState(0)

  useEffect(() => setOpen(!!live), [live])
  useEffect(() => {
    if (!live) return
    const timer = setInterval(() => tick((n) => n + 1), 1000)
    return () => clearInterval(timer)
  }, [live])

  if (!steps.length && !live) return null
  const tools = steps.filter((s) => s.kind === 'tool').length
  const elapsed = seconds(startedAt, finishedAt)
  const label = live ? 'Đang suy nghĩ' : `Đã suy nghĩ trong ${elapsed}s`

  return (
    <div className="mb-3">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[13px] text-muted-foreground transition-colors hover:text-foreground cursor-pointer"
      >
        <span className={live ? 'animate-pulse' : ''}>{label}{live && elapsed ? ` · ${elapsed}s` : ''}</span>
        {tools > 0 && <span className="text-muted-foreground/60">· {tools} tool</span>}
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {open && steps.length > 0 && (
        <div className="mt-2 ml-1.5 flex flex-col gap-1.5 border-l-2 border-border/70 pl-4">
          {steps.map((step, i) =>
            step.kind === 'tool' ? <ToolRow key={step.id || i} step={step} /> : <Prose key={i} text={step.text} />,
          )}
        </div>
      )}
    </div>
  )
}
