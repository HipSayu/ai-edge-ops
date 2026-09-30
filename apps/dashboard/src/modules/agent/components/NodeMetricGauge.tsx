import type { ReactNode } from 'react'

type Tone = 'ok' | 'warn' | 'crit'

const TONE_BAR: Record<Tone, string> = { ok: 'bg-brand', warn: 'bg-warning', crit: 'bg-destructive' }
const TONE_TEXT: Record<Tone, string> = { ok: 'text-foreground', warn: 'text-warning', crit: 'text-destructive' }

interface NodeMetricGaugeProps {
  icon: ReactNode
  label: string
  /** Main figure, e.g. 42.5 */
  value: number | string
  unit?: string
  /** Secondary text after the unit, e.g. "/ 32 GB" */
  suffix?: string
  /** 0–100 fill of the bar */
  percent: number
  /** Bar turns amber at warnAt and red at critAt (percent) */
  warnAt?: number
  critAt?: number
  /** Fixed bar color class, bypassing thresholds (e.g. for "higher is better" metrics) */
  barClassName?: string
}

/** Compact telemetry tile: label row, large tabular value, threshold-colored bar. */
export default function NodeMetricGauge({
  icon, label, value, unit, suffix, percent, warnAt = 75, critAt = 90, barClassName,
}: NodeMetricGaugeProps) {
  const pct = Math.max(0, Math.min(100, percent))
  const tone: Tone = pct >= critAt ? 'crit' : pct >= warnAt ? 'warn' : 'ok'

  return (
    <div className="flex flex-col gap-2.5 rounded-xl border border-border bg-card p-3.5">
      <div className="flex items-center gap-1.5 text-[11px] font-semibold tracking-wider text-muted-foreground">
        <span className="flex size-5 items-center justify-center rounded-md bg-muted/60">{icon}</span>
        {label}
      </div>
      <div className="flex items-baseline gap-1 font-mono tabular-nums">
        <span className={`text-xl font-bold leading-none ${barClassName ? 'text-foreground' : TONE_TEXT[tone]}`}>{value}</span>
        {unit && <span className="text-xs font-semibold text-muted-foreground">{unit}</span>}
        {suffix && <span className="text-xs text-muted-foreground">{suffix}</span>}
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-[width] duration-700 ease-out ${barClassName ?? TONE_BAR[tone]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
