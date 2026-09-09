import { useEffect, useState } from 'react'
import { Activity, Zap, CheckCircle2, Shield, Camera, LayoutGrid, Grid2X2, Grid3X3, AlertTriangle, Check, X } from 'lucide-react'
import type { InferenceSample } from '@/modules/ai/types'
import { aiService } from '@/shared/api/services/ai'
import KpiCard from '@/shared/components/KpiCard'
import type { Camera as CameraType } from '@/modules/agent/types'
import { agentService } from '@/shared/api/services/agent'
import LiveMonitorPanel from '@/modules/agent/components/LiveMonitorPanel'

type ViewMode = 'single' | 'grid4' | 'grid9'

// Dummy events to match the requested layout style
const FAKE_EVENTS = [
  {
    id: 1,
    worker: 'Worker #16',
    cam: 'Cam 1',
    time: '20:38:51',
    status: 'UNSAFE',
    aiImage: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=150&fit=crop',
    regImage: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop',
    equipment: { hardHat: false, safetyVest: false, safetyStrap: false, safetyWand: false, wireHook: true }
  },
  {
    id: 2,
    worker: 'Worker #16',
    cam: 'Cam 1',
    time: '20:38:51',
    status: 'UNSAFE',
    aiImage: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&h=150&fit=crop',
    regImage: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=80&h=80&fit=crop',
    equipment: { hardHat: false, safetyVest: false, safetyStrap: false, safetyWand: false, wireHook: true }
  },
  {
    id: 3,
    worker: 'Worker #10',
    cam: 'Cam 1',
    time: '20:38:51',
    status: 'UNSAFE',
    aiImage: 'https://images.unsplash.com/photo-1521119989659-a83eee488004?w=100&h=150&fit=crop',
    regImage: 'https://images.unsplash.com/photo-1521119989659-a83eee488004?w=80&h=80&fit=crop',
    equipment: { hardHat: false, safetyVest: false, safetyStrap: false, safetyWand: false, wireHook: true }
  },
  {
    id: 4,
    worker: 'Worker #2',
    cam: 'Cam 1',
    time: '20:38:51',
    status: 'UNSAFE',
    aiImage: 'https://images.unsplash.com/photo-1543132220-4bf3de6e10ae?w=100&h=150&fit=crop',
    regImage: 'https://images.unsplash.com/photo-1543132220-4bf3de6e10ae?w=80&h=80&fit=crop',
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

  if (!activeCamera) return <div className="av-panel">No camera data available.</div>

  const displayLimit = viewMode === 'single' ? 1 : viewMode === 'grid4' ? 4 : 9
  const displayedCameras = viewMode === 'single' ? [activeCamera] : cameras.slice(0, displayLimit)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 16 }}>
      {/* Top Layout Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Live AI Inference</h2>
        <div style={{ display: 'flex', gap: 8, background: 'var(--panel-2)', padding: 4, borderRadius: 8, border: '1px solid var(--border)' }}>
          <button className={`av-icon-btn ${viewMode === 'single' ? 'active' : ''}`} onClick={() => setViewMode('single')} title="Single View">
            <LayoutGrid size={16} />
          </button>
          <button className={`av-icon-btn ${viewMode === 'grid4' ? 'active' : ''}`} onClick={() => setViewMode('grid4')} title="2x2 Grid">
            <Grid2X2 size={16} />
          </button>
          <button className={`av-icon-btn ${viewMode === 'grid9' ? 'active' : ''}`} onClick={() => setViewMode('grid9')} title="3x3 Grid">
            <Grid3X3 size={16} />
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0 }}>
        {/* Left Side: Camera Grid */}
        <div style={{ 
          flex: 1, 
          display: 'grid', 
          gridTemplateColumns: viewMode === 'single' ? '1fr' : viewMode === 'grid4' ? 'repeat(2, 1fr)' : 'repeat(3, 1fr)', 
          gap: 16,
          alignContent: 'start'
        }}>
          {displayedCameras.map((cam) => (
            <div key={cam.id} style={{ display: 'flex', flexDirection: 'column', minHeight: viewMode === 'single' ? '60vh' : '300px' }}>
              <LiveMonitorPanel camera={cam} />
            </div>
          ))}
        </div>

        {/* Right Side: Logs Event Sidebar */}
        <section className="av-panel" style={{ width: 380, flexShrink: 0, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
          <div className="av-panel-header" style={{ borderBottom: '1px solid var(--border)', padding: '12px 16px', background: 'var(--panel-2)' }}>
            <span className="av-panel-title" style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.5px' }}>
              LOGS EVENT
            </span>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 12, background: '#1a1a1a' }}>
            {FAKE_EVENTS.map((ev) => (
              <div key={ev.id} style={{ 
                display: 'flex', 
                background: '#242424', 
                border: '1px solid #333', 
                borderRadius: 8,
                padding: 12,
                gap: 12
              }}>
                {/* Images Column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: 80 }}>
                  <div style={{ position: 'relative' }}>
                    <img src={ev.aiImage} alt="AI Overlay" style={{ width: 80, height: 100, objectFit: 'cover', borderRadius: 4, border: '1px solid #444' }} />
                    <div style={{ position: 'absolute', bottom: 2, left: 0, right: 0, textAlign: 'center', fontSize: 9, background: 'rgba(0,0,0,0.6)', color: '#ccc' }}>AI Overlay</div>
                  </div>
                  <div style={{ position: 'relative' }}>
                    <img src={ev.regImage} alt="Registered" style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 4, border: '1px solid #444' }} />
                    <div style={{ position: 'absolute', bottom: 2, left: 0, right: 0, textAlign: 'center', fontSize: 9, background: 'rgba(0,0,0,0.6)', color: '#ccc' }}>Registered</div>
                  </div>
                </div>

                {/* Info Column */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#ef4444', fontWeight: 800, fontSize: 14 }}>
                    <AlertTriangle size={16} /> {ev.status}
                  </div>
                  <div style={{ color: '#fff', fontWeight: 600, fontSize: 13, marginTop: 4 }}>
                    {ev.worker}
                  </div>
                  <div style={{ color: '#888', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4, marginTop: 2, marginBottom: 8 }}>
                    <Camera size={11} /> {ev.cam} • {ev.time}
                  </div>
                  
                  <div style={{ fontSize: 11, fontWeight: 600, color: '#aaa', marginBottom: 6 }}>
                    Safety Equipment:
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12, fontWeight: 500 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: ev.equipment.hardHat ? '#10b981' : '#ef4444' }}>
                      {ev.equipment.hardHat ? <Check size={14} /> : <X size={14} />} Hard Hat
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: ev.equipment.safetyVest ? '#10b981' : '#ef4444' }}>
                      {ev.equipment.safetyVest ? <Check size={14} /> : <X size={14} />} Safety Vest
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: ev.equipment.safetyStrap ? '#10b981' : '#ef4444' }}>
                      {ev.equipment.safetyStrap ? <Check size={14} /> : <X size={14} />} Safety Strap
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: ev.equipment.safetyWand ? '#10b981' : '#ef4444' }}>
                      {ev.equipment.safetyWand ? <Check size={14} /> : <X size={14} />} Safety Wand
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: ev.equipment.wireHook ? '#10b981' : '#ef4444' }}>
                      {ev.equipment.wireHook ? <Check size={14} /> : <X size={14} />} Wire Hook
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}


