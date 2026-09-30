import { useId, type ReactNode } from 'react'

export interface KpiCardProps {
  label: string
  value: string
  sub?: string
  badge?: string
  icon?: ReactNode
  iconBg?: string
  iconColor?: string
  deltaText: string
  isUp?: boolean
  chartType?: 'sparkline' | 'bars'
  chartColor: string
  chartData?: number[]
}

export default function KpiCard({
  label,
  value,
  sub,
  badge,
  icon,
  iconBg,
  iconColor,
  deltaText,
  isUp = true,
  chartType = 'sparkline',
  chartColor,
  chartData: chartDataProp = [],
}: KpiCardProps) {
  const gradId = useId()
  const chartData = chartDataProp.length ? chartDataProp : [0, 0]

  const WIDTH = 62
  const HEIGHT = 20

  const max = Math.max(...chartData, 1)
  const min = Math.min(...chartData, 0)
  const range = Math.max(max - min, 1)
  const stepX = WIDTH / Math.max(chartData.length - 1, 1)

  const points = chartData.map((val, i) => {
    const x = i * stepX
    const y = HEIGHT - 3 - ((val - min) / range) * (HEIGHT - 6)
    return { x, y }
  })

  const smoothPath = points.reduce((acc, p, i, arr) => {
    if (i === 0) return `M ${p.x.toFixed(1)} ${p.y.toFixed(1)}`
    const prev = arr[i - 1]
    const cp1x = prev.x + (p.x - prev.x) / 2
    const cp2x = prev.x + (p.x - prev.x) / 2
    return `${acc} C ${cp1x.toFixed(1)} ${prev.y.toFixed(1)}, ${cp2x.toFixed(1)} ${p.y.toFixed(1)}, ${p.x.toFixed(1)} ${p.y.toFixed(1)}`
  }, '')

  const lastPt = points[points.length - 1]
  const firstPt = points[0]
  const areaPath = `${smoothPath} L ${lastPt.x.toFixed(1)} ${HEIGHT} L ${firstPt.x.toFixed(1)} ${HEIGHT} Z`

  const barCount = chartData.length
  const barGap = 2
  const totalBarWidth = Math.max(4, (WIDTH - (barCount - 1) * barGap) / barCount)

  return (
    <div className="flex flex-col justify-between gap-1.5 rounded-lg border border-border bg-card p-2.5 transition-all hover:border-border/80">
      {/* Top row: icon + label + value */}
      <div className="flex items-start gap-2">
        {/* Compact Icon squircle (rendered only if icon is provided) */}
        {icon && (
          <div
            className="flex size-7 shrink-0 items-center justify-center rounded-md [&>svg]:size-3.5"
            style={{ background: iconBg, color: iconColor }}
          >
            {icon}
          </div>
        )}

        {/* Label + value */}
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex items-center justify-between gap-1">
            <span className="truncate text-[10px] font-semibold tracking-wider text-muted-foreground">
              {label}
            </span>
            {badge && (
              <span className="rounded bg-primary/10 px-1 py-0.2 text-[8.5px] font-bold text-primary">
                {badge}
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-base font-bold leading-tight tracking-tight text-foreground">
              {value}
            </span>
          </div>
          {sub && (
            <span className="truncate text-[9.5px] text-muted-foreground/80 leading-none mt-0.5">{sub}</span>
          )}
        </div>
      </div>

      {/* Bottom row: delta indicator + mini sparkline */}
      <div className="flex items-center justify-between gap-1 border-t border-border/40 pt-1.5">
        <div className={`flex items-center gap-0.5 text-[9.5px] font-medium truncate ${isUp ? 'text-success' : 'text-destructive'}`}>
          <span className="font-bold">{isUp ? '↑' : '↓'}</span>
          <span className="truncate text-muted-foreground">{deltaText}</span>
        </div>

        {/* Mini chart */}
        <div className="shrink-0 opacity-85">
          {chartType === 'bars' ? (
            <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="mini bar chart">
              {chartData.map((val, i) => {
                const bH = Math.max(3, ((val - min) / range) * (HEIGHT - 3))
                const bX = i * (totalBarWidth + barGap)
                const bY = HEIGHT - bH
                const opacity = 0.5 + 0.5 * ((i + 1) / barCount)
                return (
                  <rect
                    key={i}
                    x={bX.toFixed(1)}
                    y={bY.toFixed(1)}
                    width={totalBarWidth.toFixed(1)}
                    height={bH.toFixed(1)}
                    rx="1.5"
                    fill={chartColor}
                    opacity={opacity}
                  />
                )
              })}
            </svg>
          ) : (
            <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="mini sparkline">
              <defs>
                <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={chartColor} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={chartColor} stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <path d={areaPath} fill={`url(#${gradId})`} />
              <path
                d={smoothPath}
                fill="none"
                stroke={chartColor}
                strokeWidth={1.5}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </div>
      </div>
    </div>
  )
}
