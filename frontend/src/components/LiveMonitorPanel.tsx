import { useRef, useState } from 'react'
import type { Camera } from '../mock/cameras'
import { liveTelemetry } from '../mock/incidents'

const MOCK_STREAM_URL = 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4'

interface Props {
  camera: Camera
}

export default function LiveMonitorPanel({ camera }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const frameRef = useRef<HTMLDivElement>(null)
  const [playing, setPlaying] = useState(true)
  const [muted, setMuted] = useState(true)

  function togglePlay() {
    const v = videoRef.current
    if (!v) return
    if (playing) v.pause()
    else v.play()
    setPlaying(!playing)
  }

  function toggleFullscreen() {
    frameRef.current?.requestFullscreen?.()
  }

  return (
    <section className="av-panel av-live-panel">
      <div className="av-panel-header">
        <div className="av-live-title">
          <span className="av-live-cam-name">{camera.id} • {camera.name}</span>
          {camera.online ? (
            <span className="av-live-badge">
              <span className="av-dot critical pulse" /> TRỰC TIẾP
            </span>
          ) : (
            <span className="av-live-badge offline">MẤT KẾT NỐI</span>
          )}
        </div>
        <span className="av-panel-title">{camera.zone}</span>
      </div>

      <div className="av-video-frame" ref={frameRef}>
        {camera.online ? (
          <>
            <video ref={videoRef} src={MOCK_STREAM_URL} autoPlay loop muted={muted} playsInline />
            <div className="av-video-scanlines" />
            <div className="av-video-vignette" />

            <div className="av-overlay-topbar">
              <span className="av-overlay-chip">{camera.id}</span>
              <span className="av-overlay-chip mono">
                {new Date().toLocaleString('vi-VN', { hour12: false })}
              </span>
            </div>

            <div className="av-detect-box" style={{ top: '20%', left: '34%', width: '17%', height: '58%' }}>
              <span className="av-detect-tag person">NGƯỜI 98.7%</span>
              <span className="av-detect-tag violation">KHÔNG MŨ BẢO HỘ 96.2%</span>
            </div>

            <div className="av-detect-box safe" style={{ top: '24%', left: '58%', width: '15%', height: '50%' }}>
              <span className="av-detect-tag safe">MŨ BẢO HỘ 96.4%</span>
              <span className="av-detect-tag safe">ÁO PHẢN QUANG 94.8%</span>
            </div>

            <div className="av-video-controls">
              <button className="av-ctrl-btn" onClick={togglePlay} aria-label="Phát/Tạm dừng">
                {playing ? '⏸' : '▶'}
              </button>
              <button className="av-ctrl-btn" aria-label="Chụp ảnh">
                📷
              </button>
              <button className="av-ctrl-btn" onClick={() => setMuted((m) => !m)} aria-label="Tắt/bật tiếng">
                {muted ? '🔇' : '🔊'}
              </button>
              <span className="av-ctrl-spacer" />
              <button className="av-ctrl-btn" aria-label="Cài đặt camera">
                ⚙
              </button>
              <button className="av-ctrl-btn" onClick={toggleFullscreen} aria-label="Toàn màn hình">
                ⛶
              </button>
            </div>
          </>
        ) : (
          <div className="av-video-offline">Mất tín hiệu — {camera.id}</div>
        )}
      </div>

      <div className="av-telemetry-bar">
        <span>FPS <strong>{liveTelemetry.fps}</strong></span>
        <span>ĐỘ TRỄ <strong>{liveTelemetry.latencyMs}ms</strong></span>
        <span>ĐỐI TƯỢNG <strong>{liveTelemetry.objects}</strong></span>
        <span>ĐỘ TIN CẬY AI <strong>{liveTelemetry.aiConfidence}%</strong></span>
        <span>{liveTelemetry.resolution}</span>
      </div>
    </section>
  )
}
