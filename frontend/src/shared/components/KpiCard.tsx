import { useId, type ReactNode } from 'react'

export interface KpiCardProps {
  label: string
  value: string
  sub?: string
  badge?: string
  icon: ReactNode
  iconBg: string
  iconColor: string
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

  const WIDTH = 84
  const HEIGHT = 28

  // Geometry for sparkline
  const max = Math.max(...chartData, 1)
  const min = Math.min(...chartData, 0)
  const range = Math.max(max - min, 1)
  const stepX = WIDTH / Math.max(chartData.length - 1, 1)

  const points = chartData.map((val, i) => {
    const x = i * stepX
    const y = HEIGHT - 4 - ((val - min) / range) * (HEIGHT - 8)
    return { x, y }
  })

  const smoothPath = points.reduce((acc, p, i, arr) => {
    if (i === 0) return `M ${p.x.toFixed(1)} ${p.y.toFixed(1)}`
    const prev = arr[i - 1]
    const cp1x = prev.x + (p.x - prev.x) / 2
    const cp1y = prev.y
    const cp2x = prev.x + (p.x - prev.x) / 2
    const cp2y = p.y
    return `${acc} C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p.x.toFixed(1)} ${p.y.toFixed(1)}`
  }, '')

  const lastPt = points[points.length - 1]
  const firstPt = points[0]
  const areaPath = `${smoothPath} L ${lastPt.x.toFixed(1)} ${HEIGHT} L ${firstPt.x.toFixed(1)} ${HEIGHT} Z`

  // Geometry for vertical bars
  const barCount = chartData.length
  const barGap = 3
  const totalBarWidth = (WIDTH - (barCount - 1) * barGap) / barCount

  return (
    <div className="av-kpi-card">
      <div className="av-kpi-main-row">
        <div
          className="av-kpi-icon-squircle"
          style={{ background: iconBg, color: iconColor }}
        >
          {icon}
        </div>
        <div className="av-kpi-text-block">
          <span className="av-kpi-label">{label}</span>
          <div className="av-kpi-value-wrap">
            <span className="av-kpi-value">{value}</span>
            {badge && <span className="av-kpi-pill-badge">{badge}</span>}
          </div>
          {sub && <span className="av-kpi-sub">{sub}</span>}
        </div>
      </div>

      <div className="av-kpi-footer-row">
        <div className={`av-kpi-delta-text ${isUp ? 'up' : 'down'}`}>
          <span style={{ fontWeight: 800 }}>{isUp ? '↑' : '↓'}</span>
          <span>{deltaText}</span>
        </div>

        <div className="av-kpi-spark-wrap">
          {chartType === 'bars' ? (
            <svg
              width={WIDTH}
              height={HEIGHT}
              viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
              role="img"
              aria-label="mini bar chart"
            >
              {chartData.map((val, i) => {
                const bH = Math.max(5, ((val - min) / range) * (HEIGHT - 4))
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
                    rx="2"
                    fill={chartColor}
                    opacity={opacity}
                  />
                )
              })}
            </svg>
          ) : (
            <svg
              width={WIDTH}
              height={HEIGHT}
              viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
              role="img"
              aria-label="mini sparkline"
            >
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
                strokeWidth={2}
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
