import { BarChart3 } from 'lucide-react'
import MiniTimeSeries from '@/shared/components/MiniTimeSeries'

type AnalyticsPoint = {
  time: string
  violations: number
  people: number
  complianceRate: number
}

interface Props {
  data: AnalyticsPoint[]
  compact?: boolean
}

export default function AnalyticsChart({ data, compact }: Props) {
  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">
          <BarChart3 size={15} />
          <span>Detection & Compliance Trends</span>
        </span>
        <span className="av-panel-sub av-mono">
          {data.length ? `${data[0].time} → ${data[data.length - 1].time} (2h Window)` : 'No data'}
        </span>
      </div>
      <div className={`av-mini-chart-grid${compact ? ' compact' : ''}`}>
        <MiniTimeSeries
          title="Personnel Detected"
          data={data.map((d) => ({ time: d.time, value: d.people }))}
          color="var(--accent)"
        />
        <MiniTimeSeries
          title="PPE Violations"
          data={data.map((d) => ({ time: d.time, value: d.violations }))}
          color="var(--warning)"
        />
        <MiniTimeSeries
          title="Compliance Rate"
          data={data.map((d) => ({ time: d.time, value: d.complianceRate }))}
          color="var(--good)"
          unit="%"
        />
      </div>
    </section>
  )
}
