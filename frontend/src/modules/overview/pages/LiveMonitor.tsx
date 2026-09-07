import { useEffect, useState } from 'react'
import { LayoutGrid, WifiOff } from 'lucide-react'
import type { Camera } from '@/modules/agent/types'
import { agentService } from '@/shared/api/services/agent'
import LiveMonitorPanel from '@/modules/agent/components/LiveMonitorPanel'
import CameraListPanel from '@/modules/agent/components/CameraListPanel'

const LAYOUTS = [
  { key: '1x1', cols: 1, label: '1×1 Focus' },
  { key: '2x2', cols: 2, label: '2×2 Quad' },
  { key: '3x3', cols: 3, label: '3×3 Matrix' },
  { key: '4x4', cols: 4, label: '4×4 Wall' },
] as const

export default function LiveMonitor() {
  const [cameras, setCameras] = useState<Camera[]>([])
  const [activeId, setActiveId] = useState('')
  const [layout, setLayout] = useState<(typeof LAYOUTS)[number]>(LAYOUTS[0])
  const activeCamera = cameras.find((c) => c.id === activeId) ?? cameras[0]
  useEffect(() => { agentService.listCameras().then((items) => { setCameras(items); setActiveId(items[0]?.id ?? '') }).catch(() => setCameras([])) }, [])

  const slots = layout.cols * layout.cols
  const tiles = cameras.slice(0, slots)

  return (
    <div>
      <div className="av-layout-toolbar">
        <span className="av-panel-title">
          <LayoutGrid size={15} />
          <span>Multiview Grid Matrix</span>
        </span>
        <div className="av-layout-switch">
          {LAYOUTS.map((l) => (
            <button
              key={l.key}
              className={`av-layout-btn${layout.key === l.key ? ' active' : ''}`}
              onClick={() => setLayout(l)}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      {layout.key === '1x1' && activeCamera ? (
        <div className="av-row av-row-live">
          <LiveMonitorPanel camera={activeCamera} />
          <CameraListPanel cameras={cameras} activeId={activeId} onSelect={setActiveId} />
        </div>
      ) : (
        <div className={`av-grid-view cols-${layout.cols}`}>
          {tiles.map((cam, i) => (
            <div
              key={`${cam.id}-${i}`}
              className={`av-grid-tile${cam.id === activeId ? ' active' : ''}`}
              onClick={() => setActiveId(cam.id)}
            >
              {cam.online && cam.runtime.streamUrl ? (
                <video src={cam.runtime.streamUrl} autoPlay loop muted playsInline />
              ) : (
                <div className="av-video-offline small">
                  <WifiOff size={20} />
                  <span>Signal Lost</span>
                </div>
              )}
              <span className="av-grid-tile-label">
                <span className={`av-dot ${cam.online ? 'good pulse' : 'critical'}`} />
                <span>
                  {cam.id} • {cam.name}
                </span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
