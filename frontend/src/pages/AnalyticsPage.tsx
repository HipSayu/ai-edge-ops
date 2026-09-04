import { analyticsTimeline } from '../mock/incidents'
import AnalyticsChart from '../components/AnalyticsChart'

export default function AnalyticsPage() {
  return (
    <div>
      <div className="av-section-title">Phân tích phát hiện</div>
      <AnalyticsChart data={analyticsTimeline} />
    </div>
  )
}
