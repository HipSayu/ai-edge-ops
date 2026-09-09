import { useRef, useState } from 'react'
import {
  Play,
  Pause,
  Camera as CameraIcon,
  Volume2,
  VolumeX,
  Maximize2,
  Sliders,
  Radio,
  WifiOff,
  Zap,
} from 'lucide-react'
import type { Camera } from '@/modules/agent/types'

interface Props {
  camera: Camera
}

export default function LiveMonitorPanel({ camera }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const frameRef = useRef<HTMLDivElement>(null)
  const [playing, setPlaying] = useState(true)
  const [muted, setMuted] = useState(true)
  const [snapshotTaken, setSnapshotTaken] = useState(false)

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

  function handleSnapshot() {
    setSnapshotTaken(true)
    setTimeout(() => setSnapshotTaken(false), 800)
  }

  return (
    <section className="av-panel av-live-panel">
      <div className="av-panel-header">
        <div className="av-live-title">
          <span className="av-live-cam-name">
            {camera.id} • {camera.name}
          </span>
          {camera.online ? (
            <span className="av-live-badge">
              <Radio size={12} className="av-dot pulse" /> LIVE STREAM
            </span>
          ) : (
            <span className="av-live-badge offline">
              <WifiOff size={12} /> SIGNAL LOST
            </span>
          )}
        </div>
        <span className="av-panel-sub">{camera.zone}</span>
      </div>

      <div className="av-video-frame" ref={frameRef}>
        {camera.online ? (
          <>
            {camera.runtime.streamUrl ? (
              <video ref={videoRef} src={camera.runtime.streamUrl} autoPlay loop muted={muted} playsInline />
            ) : (
              <div className="av-video-offline"><WifiOff size={32} /><span>Stream URL unavailable</span></div>
            )}
            <div className="av-video-scanlines" />
            <div className="av-video-vignette" />

            {snapshotTaken && (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  background: 'rgba(255, 255, 255, 0.65)',
                  zIndex: 10,
                  pointerEvents: 'none',
                  animation: 'av-fade-in 0.15s ease-out',
                }}
              />
            )}

            <div className="av-overlay-topbar">
              <span className="av-overlay-chip">
                <Radio size={12} color="var(--critical)" />
                <span>REC • {camera.id}</span>
              </span>
              <span className="av-overlay-chip mono">
                {new Date().toLocaleTimeString('en-US', { hour12: false })} · {camera.runtime.resolution}
              </span>
            </div>

            {/* Video Controls */}
            <div className="av-video-controls">
              <button
                className="av-ctrl-btn"
                onClick={togglePlay}
                aria-label={playing ? 'Pause stream' : 'Play stream'}
                title={playing ? 'Pause' : 'Play'}
              >
                {playing ? <Pause size={15} /> : <Play size={15} />}
              </button>

              <button
                className="av-ctrl-btn"
                onClick={handleSnapshot}
                aria-label="Capture snapshot"
                title="Capture Snapshot"
              >
                <CameraIcon size={15} />
              </button>

              <button
                className="av-ctrl-btn"
                onClick={() => setMuted((m) => !m)}
                aria-label={muted ? 'Unmute' : 'Mute'}
                title={muted ? 'Unmute' : 'Mute'}
              >
                {muted ? <VolumeX size={15} /> : <Volume2 size={15} />}
              </button>

              <span className="av-ctrl-spacer" />

              <button
                className="av-ctrl-btn"
                aria-label="Stream parameters"
                title="Stream Settings"
              >
                <Sliders size={15} />
              </button>

              <button
                className="av-ctrl-btn"
                onClick={toggleFullscreen}
                aria-label="Toggle fullscreen"
                title="Fullscreen"
              >
                <Maximize2 size={15} />
              </button>
            </div>
          </>
        ) : (
          <div className="av-video-offline">
            <WifiOff size={32} />
            <span>Telemetry Disconnected — Feed offline for {camera.id}</span>
          </div>
        )}
      </div>

      <div className="av-telemetry-bar">
        <span>
          FPS <strong>{camera.runtime.fps || 'N/A'}</strong>
        </span>
        <span>
          LATENCY <strong>N/A</strong>
        </span>
        <span>
          OBJECTS <strong>N/A</strong>
        </span>
        <span>
          AI CONFIDENCE <strong>N/A</strong>
        </span>
        <span>
          <Zap size={13} color="var(--accent)" />
          {camera.runtime.resolution}
        </span>
      </div>
    </section>
  )
}
