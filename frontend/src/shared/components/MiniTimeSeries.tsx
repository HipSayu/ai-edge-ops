import { useState, useId } from 'react'

interface Point {
  time: string
  value: number
}

interface Props {
  title: string
  data: Point[]
  color: string
  unit?: string
}

const WIDTH = 360
const HEIGHT = 110
const PAD_X = 10
const PAD_Y = 16

export default function MiniTimeSeries({ title, data, color, unit = '' }: Props) {
  const [hovered, setHovered] = useState<number | null>(null)
  const gradId = useId()

  if (data.length === 0) {
    return (
      <div className="av-mini-chart">
        <div className="av-mini-chart-header">
          <span>{title}</span>
          <span className="av-mono av-mini-chart-value" style={{ color }}>
            —{unit}
          </span>
        </div>
        <svg width="100%" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={title} />
        <div className="av-mini-chart-axis">
          <span>—</span>
          <span>—</span>
        </div>
      </div>
    )
  }

  const max = Math.max(...data.map((d) => d.value), 1)
  const min = Math.min(...data.map((d) => d.value), 0)
  const range = Math.max(max - min, 1)
  const stepX = (WIDTH - PAD_X * 2) / (data.length - 1)

  const points = data.map((d, i) => {
    const x = PAD_X + i * stepX
    const y = HEIGHT - PAD_Y - ((d.value - min) / range) * (HEIGHT - PAD_Y * 2)
    return { x, y, ...d }
  })

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  const areaPath = `${linePath} L ${points[points.length - 1].x.toFixed(1)} ${HEIGHT} L ${points[0].x.toFixed(1)} ${HEIGHT} Z`
  const active = hovered !== null ? points[hovered] : points[points.length - 1]

  return (
    <div className="av-mini-chart">
      <div className="av-mini-chart-header">
        <span>{title}</span>
        <span className="av-mono av-mini-chart-value" style={{ color }}>
          {active.value}
          {unit}
        </span>
      </div>
      <svg width="100%" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={title}>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.28} />
            <stop offset="100%" stopColor={color} stopOpacity={0.0} />
          </linearGradient>
        </defs>

        <path d={areaPath} fill={`url(#${gradId})`} stroke="none" />
        <path d={linePath} fill="none" stroke={color} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />

        {points.map((p, i) => (
          <rect
            key={p.time}
            x={p.x - stepX / 2}
            y={0}
            width={stepX}
            height={HEIGHT}
            fill="transparent"
            onMouseEnter={() => setHovered(i)}
            onMouseLeave={() => setHovered(null)}
          />
        ))}

        {hovered !== null && (
          <>
            <line
              x1={active.x}
              y1={0}
              x2={active.x}
              y2={HEIGHT}
              stroke="var(--border-strong)"
              strokeWidth={1}
              strokeDasharray="3 3"
            />
            <circle cx={active.x} cy={active.y} r={4.5} fill={color} stroke="var(--bg-raised)" strokeWidth={2} />
            <title>
              {active.time}: {active.value}
              {unit}
            </title>
          </>
        )}
      </svg>
      <div className="av-mini-chart-axis">
        <span>{data[0].time}</span>
        <span>{data[data.length - 1].time}</span>
      </div>
    </div>
  )
}
