import type { ReactNode } from 'react'

// ── Inline mini sparkline (no external dependency) ───────────────────────────
function Sparkline({ data, color = '#0ea5e9', w = 42, h = 16 }: { data: number[]; color?: string; w?: number; h?: number }) {
  if (!data || data.length < 2) return <div style={{ width: w, height: h }} />
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w
    const y = h - ((v - min) / range) * (h - 4) - 2
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
  return (
    <svg width={w} height={h} className="overflow-visible">
      <polyline fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" points={pts} />
    </svg>
  )
}

export interface StatCardProps {
  /** Label describing the metric (e.g., 'Total Nodes', 'Live Streams') */
  label: string
  /** Main metric value (e.g., 9, '122 FPS', '99.4%') */
  value: string | number
  /** Icon component to render (optional) */
  icon?: ReactNode
  /** Color theme for icon container badge: brand | success | warning | destructive | info | purple */
  variant?: 'brand' | 'success' | 'warning' | 'destructive' | 'info' | 'purple'
  /** Optional secondary subtitle or description below */
  sub?: string
  /** Optional trend data points for sparkline */
  trend?: number[]
  /** Sparkline line color */
  trendColor?: string
  /** Optional action or click handler */
  onClick?: () => void
  /** Custom extra CSS classes */
  className?: string
}

const VARIANT_STYLES: Record<NonNullable<StatCardProps['variant']>, { bg: string; text: string; border: string; ring: string }> = {
  brand:       { bg: 'bg-blue-500/10 dark:bg-blue-500/15',        text: 'text-blue-600 dark:text-blue-400',       border: 'border-blue-500/20',        ring: 'shadow-blue-500/5' },
  success:     { bg: 'bg-emerald-500/10 dark:bg-emerald-500/15',  text: 'text-emerald-600 dark:text-emerald-400', border: 'border-emerald-500/20',     ring: 'shadow-emerald-500/5' },
  warning:     { bg: 'bg-amber-500/10 dark:bg-amber-500/15',      text: 'text-amber-600 dark:text-amber-400',     border: 'border-amber-500/20',       ring: 'shadow-amber-500/5' },
  destructive: { bg: 'bg-rose-500/10 dark:bg-rose-500/15',        text: 'text-rose-600 dark:text-rose-400',       border: 'border-rose-500/20',        ring: 'shadow-rose-500/5' },
  info:        { bg: 'bg-sky-500/10 dark:bg-sky-500/15',          text: 'text-sky-600 dark:text-sky-400',         border: 'border-sky-500/20',         ring: 'shadow-sky-500/5' },
  purple:      { bg: 'bg-purple-500/10 dark:bg-purple-500/15',    text: 'text-purple-600 dark:text-purple-400',   border: 'border-purple-500/20',      ring: 'shadow-purple-500/5' },
}

/**
 * Universal KPI Stat Card used across all Dashboard pages:
 * High-end enterprise design with subtle glow, glassmorphism badge, and sleek icon layout.
 */
export function StatCard({
  label,
  value,
  icon,
  variant = 'info',
  sub,
  trend,
  trendColor,
  onClick,
  className = '',
}: StatCardProps) {
  const styles = VARIANT_STYLES[variant] || VARIANT_STYLES.info

  return (
    <div
      onClick={onClick}
      className={`group relative flex flex-col justify-between rounded-xl border border-border/80 bg-card/90 p-3.5 backdrop-blur-sm transition-all duration-200 hover:border-border hover:shadow-lg ${styles.ring} ${
        onClick ? 'cursor-pointer' : ''
      } ${className}`}
    >
      {/* Top Section: Header with Label & Professional Icon Badge */}
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs font-semibold tracking-wide text-muted-foreground group-hover:text-foreground/80 transition-colors">
          {label}
        </span>
        {icon && (
          <div
            className={`flex size-7 shrink-0 items-center justify-center rounded-lg border ${styles.border} ${styles.bg} ${styles.text} transition-transform duration-200 group-hover:scale-105`}
          >
            {icon}
          </div>
        )}
      </div>

      {/* Main Metric & Sparkline */}
      <div className="mt-2.5 flex items-baseline justify-between gap-2">
        <div className="text-xl font-extrabold font-mono tracking-tight text-foreground">
          {value}
        </div>
        {trend && trend.length > 0 && (
          <div className="shrink-0 opacity-80 group-hover:opacity-100 transition-opacity">
            <Sparkline data={trend} color={trendColor || '#0ea5e9'} w={46} h={18} />
          </div>
        )}
      </div>

      {/* Subtitle / Context Note */}
      {sub && (
        <div className="mt-1 flex items-center gap-1.5 truncate text-[10.5px] font-medium text-muted-foreground/70">
          <span className="truncate">{sub}</span>
        </div>
      )}
    </div>
  )
}

export default StatCard
