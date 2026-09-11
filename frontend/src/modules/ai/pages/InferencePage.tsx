import { useEffect, useState } from 'react'
import { Activity, Zap, CheckCircle2, Shield, LayoutGrid, Grid2X2, Grid3X3, Settings2 } from 'lucide-react'
import type { InferenceSample } from '@/modules/ai/types'
import { aiService } from '@/shared/api/services/ai'
import KpiCard from '@/shared/components/KpiCard'
import type { Camera as CameraType } from '@/modules/agent/types'
import { agentService } from '@/shared/api/services/agent'
import LiveMonitorPanel from '@/modules/agent/components/LiveMonitorPanel'
import PageLayout from '@/shared/components/PageLayout'
import LogsEventSidebar, { type EventLog } from '@/shared/components/LogsEventSidebar'

type ViewMode = 'single' | 'grid4' | 'grid9'

// Dummy events mapped to the new EventLog type
const FAKE_EVENTS: EventLog[] = [
  {
    id: 1,
    worker: 'Worker #16',
    cam: 'Cam 1',
    time: '20:38:51',
    status: 'UNSAFE',
    aiImage: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&h=160&fit=crop',
    regImage: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
    equipment: { hardHat: false, safetyVest: false, safetyStrap: false, safetyWand: false, wireHook: true }
  },
  {
    id: 2,
    worker: 'Worker #16',
    cam: 'Cam 1',
    time: '20:38:51',
    status: 'UNSAFE',
    aiImage: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=120&h=160&fit=crop',
    regImage: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&h=100&fit=crop',
    equipment: { hardHat: false, safetyVest: false, safetyStrap: false, safetyWand: false, wireHook: true }
  },
  {
    id: 3,
    worker: 'Worker #10',
    cam: 'Cam 1',
    time: '20:38:51',
    status: 'UNSAFE',
    aiImage: 'https://images.unsplash.com/photo-1521119989659-a83eee488004?w=120&h=160&fit=crop',
    regImage: 'https://images.unsplash.com/photo-1521119989659-a83eee488004?w=100&h=100&fit=crop',
    equipment: { hardHat: false, safetyVest: false, safetyStrap: false, safetyWand: false, wireHook: true }
  }
]

export default function InferencePage() {
  const [viewMode, setViewMode] = useState<ViewMode>('single')
  const [selectedCamId, setSelectedCamId] = useState('')
  const [cameras, setCameras] = useState<CameraType[]>([])
  const [samples, setSamples] = useState<InferenceSample[]>([])

  useEffect(() => { agentService.listCameras().then((items) => { setCameras(items); setSelectedCamId(items[0]?.id ?? '') }).catch(() => setCameras([])) }, [])
  useEffect(() => { aiService.listInferenceSamples().then(setSamples).catch(() => setSamples([])) }, [])

  const activeCamera = cameras.find((c) => c.id === selectedCamId) ?? cameras[0]
  const objectCount = samples.reduce((total, sample) => total + sample.objects.length, 0)
  const confidenceValues = samples.flatMap((sample) => sample.objects.map((object) => object.confidence))
  const meanConfidence = confidenceValues.length
    ? confidenceValues.reduce((sum, confidence) => sum + confidence, 0) / confidenceValues.length
    : null

  if (!activeCamera) return <div className="av-panel" style={{ margin: 24 }}>No camera data available.</div>

  const displayLimit = viewMode === 'single' ? 1 : viewMode === 'grid4' ? 4 : 9
  const displayedCameras = viewMode === 'single' ? [activeCamera] : cameras.slice(0, displayLimit)

  const header = (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>Live AI Inference</h2>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <button className="av-btn-secondary">
          <Settings2 size={16} /> Inference Settings
        </button>
        <div style={{ display: 'flex', gap: 4, background: 'var(--panel-2)', padding: 4, borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
          <button className={`av-icon-btn ${viewMode === 'single' ? 'active' : ''}`} onClick={() => setViewMode('single')} title="Single View" style={viewMode === 'single' ? { background: 'var(--panel)', color: 'var(--text)', borderColor: 'var(--border-strong)' } : {}}>
            <LayoutGrid size={16} />
          </button>
          <button className={`av-icon-btn ${viewMode === 'grid4' ? 'active' : ''}`} onClick={() => setViewMode('grid4')} title="2x2 Grid" style={viewMode === 'grid4' ? { background: 'var(--panel)', color: 'var(--text)', borderColor: 'var(--border-strong)' } : {}}>
            <Grid2X2 size={16} />
          </button>
          <button className={`av-icon-btn ${viewMode === 'grid9' ? 'active' : ''}`} onClick={() => setViewMode('grid9')} title="3x3 Grid" style={viewMode === 'grid9' ? { background: 'var(--panel)', color: 'var(--text)', borderColor: 'var(--border-strong)' } : {}}>
            <Grid3X3 size={16} />
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <PageLayout header={header}>
      {/* Inference Top KPIs */}
      <div className="av-kpi-row" style={{ marginBottom: 20 }}>
        <KpiCard
          label="Inference FPS"
          value="—"
          sub="fps"
          icon={<Zap size={22} />}
          iconBg="rgba(245, 158, 11, 0.12)"
          iconColor="#d97706"
          deltaText="Not provided by backend"
          isUp={true}
          chartType="sparkline"
          chartColor="#f59e0b"
          chartData={[]}
        />
        <KpiCard
          label="Mean Latency"
          value="—"
          sub="ms"
          icon={<Activity size={22} />}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#2563eb"
          deltaText="Not provided by backend"
          isUp={true}
          chartType="bars"
          chartColor="#3b82f6"
          chartData={[]}
        />
        <KpiCard
          label="Mean Confidence"
          value={meanConfidence == null ? '—' : `${meanConfidence.toFixed(1)}%`}
          sub="avg"
          icon={<CheckCircle2 size={22} />}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
          deltaText="From detection feed"
          isUp={true}
          chartType="sparkline"
          chartColor="#10b981"
          chartData={confidenceValues}
        />
        <KpiCard
          label="Detected Objects"
          value={String(objectCount)}
          sub="in view"
          icon={<Shield size={22} />}
          iconBg="rgba(168, 85, 247, 0.12)"
          iconColor="#9333ea"
          deltaText="From detection feed"
          isUp={true}
          chartType="bars"
          chartColor="#a855f7"
          chartData={samples.map((sample) => sample.objects.length)}
        />
      </div>

      <div style={{ display: 'flex', gap: 20, height: 'calc(100vh - 280px)', minHeight: 600 }}>
        {/* Left Side: Camera Grid */}
        <div style={{ 
          flex: 1, 
          display: 'grid', 
          gridTemplateColumns: viewMode === 'single' ? '1fr' : viewMode === 'grid4' ? 'repeat(2, 1fr)' : 'repeat(3, 1fr)', 
          gap: 20,
          alignContent: 'start',
          height: '100%',
          overflowY: 'auto',
          paddingRight: 4
        }}>
          {displayedCameras.map((cam) => (
            <div key={cam.id} style={{ display: 'flex', flexDirection: 'column', height: viewMode === 'single' ? '100%' : '320px' }}>
              <LiveMonitorPanel camera={cam} />
            </div>
          ))}
        </div>

        {/* Right Side: Logs Event Sidebar (Shared Component) */}
        <LogsEventSidebar events={FAKE_EVENTS} />
      </div>
    </PageLayout>
  )
}
