import { useCallback, useEffect, useState } from 'react'
import { Wifi, WifiOff, Radio, Play } from 'lucide-react'
import type { Camera, EdgeDevice } from '@/modules/agent/types'
import { agentService } from '@/shared/api/services/agent'
import WhepVideo, { type WhepStats } from '@/shared/streaming/WhepVideo'

interface Props {
  camera: Camera
  onOpen: (camera: Camera) => void
}

/** One camera tile: live WHEP thumbnail + real stream/pipeline stats. */
export default function CameraCard({ camera, onOpen }: Props) {
  const [stats, setStats] = useState<WhepStats | null>(null)
  const [live, setLive] = useState(false)
  const [device, setDevice] = useState<EdgeDevice | null>(null)

  useEffect(() => {
    if (!camera.deviceId) return
    let active = true
    agentService
      .getDevice(camera.deviceId)
      .then((d) => active && setDevice(d))
      .catch(() => {})
    return () => {
      active = false
    }
  }, [camera.deviceId])

  const handleStats = useCallback((s: WhepStats) => setStats(s), [])
  const handleStatus = useCallback((s: 'connecting' | 'live' | 'error') => setLive(s === 'live'), [])

  const resolution = stats?.width ? `${stats.width}×${stats.height}` : '—'
  const fps = stats?.fps ?? 0
  const model = device?.modelRunning && device.modelRunning !== 'No model reported'
    ? device.modelRunning
    : '—'
  const heartbeat = device?.lastHeartbeat ?? '—'

  return (
    <div className="av-panel av-camera-card">
      <div className="av-camera-card-thumb" style={{ background: '#000', overflow: 'hidden' }}>
        {camera.online ? (
          <WhepVideo cameraId={camera.id} muted onStats={handleStats} onStatusChange={handleStatus} />
        ) : (
          <WifiOff size={28} className="av-camera-thumb-off" />
        )}
        {camera.online && (
          <span className="av-live-badge overlay">
            <Radio size={12} className="av-dot pulse" /> {live ? 'LIVE' : '…'}
          </span>
        )}
      </div>

      <div className="av-panel-body">
        <div className="av-camera-card-title">
          <span>{camera.id}</span>
          {camera.alertCount > 0 ? (
            <span className="av-alert-pill has-alerts">{camera.alertCount} alerts</span>
          ) : (
            <span className="av-alert-pill">Normal</span>
          )}
        </div>
        <div className="av-camera-card-sub">
          {camera.name} · {camera.zone}
        </div>
        <div className="av-camera-card-status">
          {camera.online ? (
            <>
              <Wifi size={13} color="var(--good)" />
              <span style={{ color: 'var(--good)', fontWeight: 600 }}>
                {live ? 'Streaming' : 'Connecting'} • {fps} FPS
              </span>
            </>
          ) : (
            <>
              <WifiOff size={13} color="var(--critical)" />
              <span style={{ color: 'var(--critical)', fontWeight: 600 }}>Connection Lost</span>
            </>
          )}
        </div>

        <div className="av-camera-runtime">
          <span className="av-camera-runtime-title">Inference &amp; Streaming Pipeline</span>
          <div className="av-camera-runtime-grid">
            <div className="av-camera-runtime-row">
              <span>Assigned Model</span>
              <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{model}</span>
            </div>
            <div className="av-camera-runtime-row">
              <span>Resolution</span>
              <span className="av-mono">{resolution}</span>
            </div>
            <div className="av-camera-runtime-row">
              <span>Protocol</span>
              <span className="av-mono">{live ? 'WebRTC / WHEP' : camera.runtime.protocol}</span>
            </div>
            <div className="av-camera-runtime-row">
              <span>Bitrate</span>
              <span className="av-mono">{stats?.bitrateKbps ? `${stats.bitrateKbps} kbps` : '—'}</span>
            </div>
            <div className="av-camera-runtime-row">
              <span>Heartbeat</span>
              <span className="av-mono">{heartbeat}</span>
            </div>
          </div>
        </div>

        <button
          className="av-btn-primary"
          style={{ width: '100%', marginTop: 14, justifyContent: 'center' }}
          onClick={() => onOpen(camera)}
        >
          <Play size={14} />
          <span>View Stream &amp; HUD</span>
        </button>
      </div>
    </div>
  )
}
