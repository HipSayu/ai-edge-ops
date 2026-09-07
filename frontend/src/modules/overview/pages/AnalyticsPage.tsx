import { useEffect, useState } from 'react'
import KpiCard from '@/shared/components/KpiCard'
import { TrendingUp, ShieldCheck, AlertCircle, Clock } from 'lucide-react'
import type { AnalyticsPoint } from '@/modules/observability/types'
import { observabilityService } from '@/shared/api/services/observability'
import AnalyticsChart from '@/shared/components/AnalyticsChart'

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('2h')
  const [timeline, setTimeline] = useState<AnalyticsPoint[]>([])
  const [categories, setCategories] = useState<{ label: string; count: number }[]>([])
  useEffect(() => {
    observabilityService.getViolationTimeseries().then((rows) => setTimeline(rows.map((row) => ({ time: row.bucket, violations: row.count, people: 0, complianceRate: 0 })))).catch(() => setTimeline([]))
    observabilityService.getViolationsByType().then(setCategories).catch(() => setCategories([]))
  }, [])

  return (
    <div className="av-page-layout">
      <div className="av-page-header">
      <div className="av-layout-toolbar">
        
        <div className="av-layout-switch">
          {['2h', '24h', '7d', '30d'].map((range) => (
            <button
              key={range}
              className={`av-layout-btn${timeRange === range ? ' active' : ''}`}
              onClick={() => setTimeRange(range)}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <div className="av-kpi-row" style={{ marginTop: 14 }}>
        <KpiCard
          label="Inference Volume"
          value="1.24M"
          sub="frames"
          icon={<TrendingUp size={22} />}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#2563eb"
          deltaText="99.8% processed on edge"
          isUp={true}
          chartType="bars"
          chartColor="#3b82f6"
        />
        <KpiCard
          label="Mean Triage Latency"
          value="1.4s"
          sub="avg"
          icon={<Clock size={22} />}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
          deltaText="-0.6s vs yesterday"
          isUp={true}
          chartType="sparkline"
          chartColor="#10b981"
        />
        <KpiCard
          label="Overall Safety Score"
          value="94.2"
          sub="/100"
          icon={<ShieldCheck size={22} />}
          iconBg="rgba(139, 92, 246, 0.12)"
          iconColor="#8b5cf6"
          deltaText="+1.8% compliance"
          isUp={true}
          chartType="sparkline"
          chartColor="#8b5cf6"
        />
        <KpiCard
          label="False Positive Rate"
          value="0.4%"
          sub="minimized"
          icon={<AlertCircle size={22} />}
          iconBg="rgba(245, 158, 11, 0.12)"
          iconColor="#d97706"
          deltaText="Filtered by 5-frame persistence"
          isUp={true}
          chartType="bars"
          chartColor="#f59e0b"
        />
      </div>
      </div>

      <div className="av-page-content">
        <AnalyticsChart data={timeline} />

      

      <div className="av-panel" style={{ padding: 22 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {categories.map((category) => (
            <CategoryBar key={category.label} label={category.label} count={category.count} percentage={0} color="var(--accent)" />
          ))}
        </div>
      </div>
      </div>
    </div>
  )
}

function CategoryBar({
  label,
  count,
  percentage,
  color}: {
  label: string
  count: number
  percentage: number
  color: string
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 600 }}>
        <span>{label}</span>
        <span className="av-mono" style={{ color: 'var(--text-dim)' }}>
          {count} incidents ({percentage}%)
        </span>
      </div>
      <div className="av-telemetry-bar-track" style={{ height: 8, borderRadius: 4 }}>
        <div
          style={{
            height: '100%',
            width: `${percentage}%`,
            background: color,
            borderRadius: 4,
            transition: 'width 0.5s ease'}}
        />
      </div>
    </div>
  )
}


