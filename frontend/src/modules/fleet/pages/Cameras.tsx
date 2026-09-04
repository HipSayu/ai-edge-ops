import { Camera as CameraIcon, Wifi, WifiOff, Radio } from 'lucide-react'
import { mockCameras } from '@/mock\cameras'

export default function Cameras() {
  return (
    <div>
      

      <div className="av-cameras-grid">
        {mockCameras.map((cam) => (
          <div key={cam.id} className="av-panel av-camera-card">
            <div
              className="av-camera-card-thumb"
              style={{ background: `hsl(${cam.thumbHue} 40% 16%)` }}
            >
              {!cam.online ? (
                <WifiOff size={28} className="av-camera-thumb-off" />
              ) : (
                <CameraIcon size={28} color="rgba(255,255,255,0.6)" />
              )}
              {cam.online && (
                <span className="av-live-badge overlay">
                  <Radio size={12} className="av-dot pulse" /> LIVE
                </span>
              )}
            </div>

            <div className="av-panel-body">
              <div className="av-camera-card-title">
                <span>{cam.id}</span>
                {cam.alertCount > 0 ? (
                  <span className="av-alert-pill has-alerts">{cam.alertCount} alerts</span>
                ) : (
                  <span className="av-alert-pill">Normal</span>
                )}
              </div>
              <div className="av-camera-card-sub">
                {cam.name} · {cam.zone}
              </div>
              <div className="av-camera-card-status">
                {cam.online ? (
                  <>
                    <Wifi size={13} color="var(--good)" />
                    <span style={{ color: 'var(--good)', fontWeight: 600 }}>
                      Connected & Streaming
                    </span>
                  </>
                ) : (
                  <>
                    <WifiOff size={13} color="var(--critical)" />
                    <span style={{ color: 'var(--critical)', fontWeight: 600 }}>
                      Connection Lost
                    </span>
                  </>
                )}
              </div>

              <div className="av-camera-runtime">
                <span className="av-camera-runtime-title">Edge Service Pipeline</span>
                <div className="av-camera-runtime-grid">
                  <RuntimeRow label="Resolution" value={cam.runtime.resolution} />
                  <RuntimeRow label="Streaming Protocol" value={cam.runtime.protocol} />
                  <RuntimeRow label="Inference Model" value={cam.runtime.model} />
                  <RuntimeRow
                    label="Inference FPS"
                    value={cam.online ? `${cam.runtime.fps} FPS` : '—'}
                  />
                  <RuntimeRow label="Active ROI Zones" value={String(cam.runtime.roiZones)} />
                  <RuntimeRow label="Heartbeat Sync" value={cam.runtime.lastHeartbeat} />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function RuntimeRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="av-camera-runtime-row">
      <span>{label}</span>
      <span className="av-mono">{value}</span>
    </div>
  )
}
