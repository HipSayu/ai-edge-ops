import { useState } from 'react'
import { mockCameras } from '../mock/cameras'
import { analyticsTimeline, kpi } from '../mock/incidents'
import { useIncidents } from '../hooks/useIncidents'
import KpiCard from '../components/KpiCard'
import LiveMonitorPanel from '../components/LiveMonitorPanel'
import CameraListPanel from '../components/CameraListPanel'
import AlertsPanel from '../components/AlertsPanel'
import AnalyticsChart from '../components/AnalyticsChart'
import EdgeDeviceCard from '../components/EdgeDeviceCard'
import IncidentModal from '../components/IncidentModal'

export default function Overview() {
  const [activeId, setActiveId] = useState(mockCameras[0].id)
  const activeCamera = mockCameras.find((c) => c.id === activeId) ?? mockCameras[0]
  const { incidents, selected, setSelected, markReviewed, escalate } = useIncidents()

  return (
    <div>
      <div className="av-kpi-row">
        <KpiCard label="Tổng số người" value={String(kpi.totalPeople.value)} icon="👤" delta={kpi.totalPeople.delta} />
        <KpiCard
          label="Tuân thủ PPE"
          value={String(kpi.compliant.value)}
          sub={`${kpi.compliant.rate}%`}
          icon="🪖"
          delta={kpi.compliant.delta}
        />
        <KpiCard label="Vi phạm" value={String(kpi.violations.value)} icon="⚠️" delta={kpi.violations.delta} />
        <KpiCard label="Cảnh báo nghiêm trọng" value={String(kpi.critical.value)} icon="🚨" delta={kpi.critical.delta} />
      </div>

      <div className="av-section-title">Giám sát camera trực tiếp</div>
      <div className="av-row av-row-live">
        <LiveMonitorPanel camera={activeCamera} />
        <CameraListPanel cameras={mockCameras} activeId={activeId} onSelect={setActiveId} />
      </div>

      <div className="av-section-title">Cảnh báo trực tiếp</div>
      <AlertsPanel data={incidents.slice(0, 5)} onSelect={setSelected} />

      <div className="av-section-title">Phân tích phát hiện</div>
      <AnalyticsChart data={analyticsTimeline} />

      <div className="av-section-title">Thiết bị Edge</div>
      <EdgeDeviceCard compact />

      {selected && (
        <IncidentModal
          incident={selected}
          onClose={() => setSelected(null)}
          onMarkReviewed={markReviewed}
          onEscalate={escalate}
        />
      )}
    </div>
  )
}
