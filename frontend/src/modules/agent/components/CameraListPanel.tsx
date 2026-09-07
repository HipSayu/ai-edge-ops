import { Camera as CameraIcon, WifiOff } from 'lucide-react'
import type { Camera } from '@/modules/agent/types'

interface Props {
  cameras: Camera[]
  activeId: string
  onSelect: (id: string) => void
}

export default function CameraListPanel({ cameras, activeId, onSelect }: Props) {
  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">
          <CameraIcon size={15} />
          <span>Camera Feeds</span>
        </span>
        <span className="av-panel-sub">{cameras.length} Nodes</span>
      </div>

      <ul className="av-camera-list">
        {cameras.map((cam) => (
          <li key={cam.id}>
            <button
              className={`av-camera-row${cam.id === activeId ? ' active' : ''}`}
              onClick={() => onSelect(cam.id)}
            >
              <div
                className="av-camera-thumb"
                style={{ background: `hsl(${cam.thumbHue} 40% 16%)` }}
              >
                {!cam.online ? (
                  <WifiOff size={14} className="av-camera-thumb-off" />
                ) : (
                  <CameraIcon size={14} color="rgba(255,255,255,0.7)" />
                )}
              </div>
              <div className="av-camera-row-text">
                <span className="av-camera-row-id">{cam.id}</span>
                <span className="av-camera-row-zone">{cam.name}</span>
                <span className="av-camera-row-status">
                  {cam.online ? (
                    <>
                      <span className="av-dot good" /> LIVE • {cam.runtime.fps} FPS
                    </>
                  ) : (
                    <>
                      <span className="av-dot" /> OFFLINE
                    </>
                  )}
                </span>
              </div>
              {cam.online && (
                <span className={`av-alert-pill${cam.alertCount > 0 ? ' has-alerts' : ''}`}>
                  {cam.alertCount > 0 ? `${cam.alertCount} alerts` : 'Normal'}
                </span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
