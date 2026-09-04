import { mockCameras } from '../mock/cameras'

export default function Cameras() {
  return (
    <div>
      <div className="av-section-title">Quản lý camera</div>
      <div className="av-cameras-grid">
        {mockCameras.map((cam) => (
          <div key={cam.id} className="av-panel av-camera-card">
            <div className="av-camera-card-thumb" style={{ background: `hsl(${cam.thumbHue} 45% 14%)` }}>
              {!cam.online && <span className="av-camera-thumb-off">✕</span>}
              {cam.online && (
                <span className="av-live-badge overlay">
                  <span className="av-dot critical pulse" /> TRỰC TIẾP
                </span>
              )}
            </div>
            <div className="av-panel-body">
              <div className="av-camera-card-title">
                <span>{cam.id}</span>
                {cam.alertCount > 0 && <span className="av-alert-pill has-alerts">{cam.alertCount} cảnh báo</span>}
              </div>
              <div className="av-camera-card-sub">{cam.name} · {cam.zone}</div>
              <div className="av-camera-card-status">
                {cam.online ? (
                  <>
                    <span className="av-dot good" /> Đang hoạt động
                  </>
                ) : (
                  <>
                    <span className="av-dot critical" /> Mất kết nối
                  </>
                )}
              </div>

              <div className="av-camera-runtime">
                <span className="av-camera-runtime-title">Cấu hình từ Edge Service</span>
                <div className="av-camera-runtime-grid">
                  <RuntimeRow label="Độ phân giải" value={cam.runtime.resolution} />
                  <RuntimeRow label="Giao thức" value={cam.runtime.protocol} />
                  <RuntimeRow label="Mô hình" value={cam.runtime.model} />
                  <RuntimeRow label="FPS suy luận" value={cam.online ? `${cam.runtime.fps}` : '—'} />
                  <RuntimeRow label="Vùng ROI" value={String(cam.runtime.roiZones)} />
                  <RuntimeRow label="Heartbeat cuối" value={cam.runtime.lastHeartbeat} />
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
