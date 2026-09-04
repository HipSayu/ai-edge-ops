import { useState } from 'react'
import { mockCameras } from '../mock/cameras'
import LiveMonitorPanel from '../components/LiveMonitorPanel'
import CameraListPanel from '../components/CameraListPanel'

const LAYOUTS = [
  { key: '1x1', cols: 1, label: '1×1' },
  { key: '2x2', cols: 2, label: '2×2' },
  { key: '3x3', cols: 3, label: '3×3' },
  { key: '4x4', cols: 4, label: '4×4' },
] as const

const MOCK_STREAM_URL = 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4'

export default function LiveMonitor() {
  const [activeId, setActiveId] = useState(mockCameras[0].id)
  const [layout, setLayout] = useState<(typeof LAYOUTS)[number]>(LAYOUTS[0])
  const activeCamera = mockCameras.find((c) => c.id === activeId) ?? mockCameras[0]

  const slots = layout.cols * layout.cols
  const tiles = Array.from({ length: slots }, (_, i) => mockCameras[i % mockCameras.length])

  return (
    <div>
      <div className="av-layout-toolbar">
        <span className="av-panel-title">Bố cục lưới</span>
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

      {layout.key === '1x1' ? (
        <div className="av-row av-row-live">
          <LiveMonitorPanel camera={activeCamera} />
          <CameraListPanel cameras={mockCameras} activeId={activeId} onSelect={setActiveId} />
        </div>
      ) : (
        <div className={`av-grid-view cols-${layout.cols}`}>
          {tiles.map((cam, i) => (
            <div
              key={`${cam.id}-${i}`}
              className={`av-grid-tile${cam.id === activeId ? ' active' : ''}`}
              onClick={() => setActiveId(cam.id)}
            >
              {cam.online ? (
                <video src={MOCK_STREAM_URL} autoPlay loop muted playsInline />
              ) : (
                <div className="av-video-offline small">Mất tín hiệu</div>
              )}
              <span className="av-grid-tile-label">
                <span className="av-dot critical" /> {cam.id}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
