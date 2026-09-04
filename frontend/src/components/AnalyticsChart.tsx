import type { AnalyticsPoint } from '../mock/incidents'
import MiniTimeSeries from './MiniTimeSeries'

interface Props {
  data: AnalyticsPoint[]
  compact?: boolean
}

export default function AnalyticsChart({ data, compact }: Props) {
  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">Phân tích phát hiện</span>
        <span className="av-panel-sub av-mono">
          {data[0].time} → {data[data.length - 1].time}
        </span>
      </div>
      <div className={`av-mini-chart-grid${compact ? ' compact' : ''}`}>
        <MiniTimeSeries
          title="Số người phát hiện"
          data={data.map((d) => ({ time: d.time, value: d.people }))}
          color="var(--accent)"
        />
        <MiniTimeSeries
          title="Vi phạm PPE"
          data={data.map((d) => ({ time: d.time, value: d.violations }))}
          color="var(--warning)"
        />
        <MiniTimeSeries
          title="Tỷ lệ tuân thủ"
          data={data.map((d) => ({ time: d.time, value: d.complianceRate }))}
          color="var(--good)"
          unit="%"
        />
      </div>
    </section>
  )
}
