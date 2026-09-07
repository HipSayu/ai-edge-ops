import { useEffect, useState } from 'react'
import { Activity, Zap, CheckCircle2, Shield, Camera } from 'lucide-react'
import type { InferenceSample } from '@/modules/ai/types'
import { aiService } from '@/shared/api/services/ai'
import KpiCard from '@/shared/components/KpiCard'
import type { Camera as CameraType } from '@/modules/agent/types'
import { agentService } from '@/shared/api/services/agent'
import LiveMonitorPanel from '@/modules/agent/components/LiveMonitorPanel'

export default function InferencePage() {
  const [selectedCamId, setSelectedCamId] = useState('')
  const [cameras, setCameras] = useState<CameraType[]>([])
  const [samples, setSamples] = useState<InferenceSample[]>([])
  useEffect(() => { agentService.listCameras().then((items) => { setCameras(items); setSelectedCamId(items[0]?.id ?? '') }).catch(() => setCameras([])) }, [])
  useEffect(() => { aiService.listInferenceSamples().then(setSamples).catch(() => setSamples([])) }, [])
  const activeCamera = cameras.find((c) => c.id === selectedCamId) ?? cameras[0]
  if (!activeCamera) return <div className="av-panel">No camera data available.</div>

  return (
    <div>
      

      {/* Inference Top KPIs */}
      <div className="av-kpi-row">
        <KpiCard
          label="Inference FPS"
          value="29.4"
          sub="fps"
          icon={<Zap size={22} />}
          iconBg="rgba(245, 158, 11, 0.12)"
          iconColor="#d97706"
          deltaText="Real-time throughput"
          isUp={true}
          chartType="sparkline"
          chartColor="#f59e0b"
          chartData={[25, 27, 26, 29, 28, 30, 29, 29.4]}
        />
        <KpiCard
          label="Mean Latency"
          value="14.2"
          sub="ms"
          icon={<Activity size={22} />}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#2563eb"
          deltaText="TensorRT FP16 engine"
          isUp={true}
          chartType="bars"
          chartColor="#3b82f6"
          chartData={[15, 14, 16, 13, 14, 15, 14, 14.2]}
        />
        <KpiCard
          label="Mean Confidence"
          value="96.8%"
          sub="avg"
          icon={<CheckCircle2 size={22} />}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
          deltaText="> 65% threshold"
          isUp={true}
          chartType="sparkline"
          chartColor="#10b981"
          chartData={[92, 94, 93, 95, 96, 95, 96, 96.8]}
        />
        <KpiCard
          label="Detected Objects"
          value="8"
          sub="in view"
          icon={<Shield size={22} />}
          iconBg="rgba(168, 85, 247, 0.12)"
          iconColor="#9333ea"
          deltaText="Tracking active"
          isUp={true}
          chartType="bars"
          chartColor="#a855f7"
          chartData={[4, 5, 4, 7, 6, 8, 7, 8]}
        />
      </div>

      {/* Main Live Inference View */}
      <div className="av-row av-row-live" style={{ marginBottom: 20 }}>
        <div>
          <LiveMonitorPanel camera={activeCamera} />
        </div>

        {/* Live Detected Objects Inspector */}
        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Camera size={14} />
              <span>Camera Select</span>
            </span>
            <select
              value={selectedCamId}
              onChange={(e) => setSelectedCamId(e.target.value)}
              style={{
                fontSize: 12,
                fontWeight: 600,
                padding: '4px 8px',
                borderRadius: 6,
                border: '1px solid var(--border-strong)',
                background: 'var(--panel-2)',
                color: 'var(--text)'}}
            >
              {cameras.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} — {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="av-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-faint)' }}>
              Recent Detections Feed
            </span>

            {samples.map((sample) => (
              <div
                key={sample.id}
                style={{
                  background: 'var(--panel-2)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 12,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8}}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                  <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{sample.camera}</span>
                  <span className="av-mono" style={{ color: 'var(--text-faint)' }}>{sample.timestamp}</span>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {sample.objects.map((obj, oIdx) => (
                    <span
                      key={oIdx}
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        padding: '3px 8px',
                        borderRadius: 4,
                        background: 'var(--panel)',
                        border: '1px solid var(--border)',
                        color: obj.color,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4}}
                    >
                      <span>{obj.label}</span>
                      <span className="av-mono" style={{ opacity: 0.85 }}>{obj.confidence}%</span>
                    </span>
                  ))}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10.5, color: 'var(--text-faint)' }}>
                  <span>FPS: {sample.fps}</span>
                  <span>Latency: {sample.latencyMs}ms</span>
                  <span>{sample.resolution}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

