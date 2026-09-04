import type { Camera } from '../mock/cameras'

interface Props {
  cameras: Camera[]
  activeId: string
  onSelect: (id: string) => void
}

export default function CameraListPanel({ cameras, activeId, onSelect }: Props) {
  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">Camera</span>
      </div>
      <ul className="av-camera-list">
        {cameras.map((cam) => (
          <li key={cam.id}>
            <button
              className={`av-camera-row${cam.id === activeId ? ' active' : ''}`}
              onClick={() => onSelect(cam.id)}
            >
              <div className="av-camera-thumb" style={{ background: `hsl(${cam.thumbHue} 45% 14%)` }}>
                {!cam.online && <span className="av-camera-thumb-off">✕</span>}
              </div>
              <div className="av-camera-row-text">
                <span className="av-camera-row-id">{cam.id}</span>
                <span className="av-camera-row-zone">{cam.name}</span>
                <span className="av-camera-row-status">
                  {cam.online ? (
                    <>
                      <span className="av-dot critical" /> TRỰC TIẾP
                    </>
                  ) : (
                    <>
                      <span className="av-dot" /> MẤT KẾT NỐI
                    </>
                  )}
                </span>
              </div>
              {cam.online && (
                <span className={`av-alert-pill${cam.alertCount > 0 ? ' has-alerts' : ''}`}>
                  {cam.alertCount > 0 ? `${cam.alertCount} cảnh báo` : 'Bình thường'}
                </span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
