interface Props {
  label: string
  value: string
  icon: string
  sub?: string
  delta?: number
}

export default function KpiCard({ label, value, icon, sub, delta }: Props) {
  const isUp = (delta ?? 0) >= 0
  return (
    <div className="av-kpi-card">
      <div className="av-kpi-top">
        <span className="av-kpi-label">{label}</span>
        <span className="av-kpi-icon">{icon}</span>
      </div>
      <div className="av-kpi-value-row">
        <span className="av-kpi-value av-mono">{value}</span>
        {sub && <span className="av-kpi-sub">{sub}</span>}
      </div>
      {delta !== undefined && (
        <span className={`av-trend ${isUp ? 'up' : 'down'}`}>
          {isUp ? '▲' : '▼'} {Math.abs(delta)}%
        </span>
      )}
    </div>
  )
}
