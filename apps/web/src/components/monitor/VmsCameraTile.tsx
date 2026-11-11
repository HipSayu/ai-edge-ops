import { useState } from 'react'
import { Camera, Loader2, Maximize2, Minimize2, Pause, Play, Users, ZoomIn, ZoomOut } from 'lucide-react'
import type { GridItem } from '@/api/types'
import CameraStream from '@/components/monitor/CameraStream'
import ZoneOverlay from '@/components/monitor/ZoneOverlay'
import { downloadBlob } from '@/helpers/media'
import { setPaused, snapshotTile } from '@/overlay/liveWall'

interface VmsCameraTileProps {
  item: GridItem
  isSelected: boolean
  isMaximized?: boolean
  onSelect: () => void
  onMaximize: () => void
  nowStr: string
}

const ZOOM_STEPS = [1, 1.5, 2, 3]

export default function VmsCameraTile({
  item,
  isSelected,
  isMaximized = false,
  onSelect,
  onMaximize,
  nowStr,
}: VmsCameraTileProps) {
  const alert = item.violation_count_recent > 0
  const [paused, setPausedState] = useState(false)
  const [zoomStep, setZoomStep] = useState(0)
  const [taking, setTaking] = useState(false)

  const togglePause = () => {
    const next = !paused
    setPausedState(next)
    setPaused(item.camera_id, next)
  }

  const takeSnapshot = async () => {
    setTaking(true)
    const blob = await snapshotTile(item.camera_id)
    setTaking(false)
    if (blob) downloadBlob(blob, `${item.name}-${new Date().toISOString().replace(/[:.]/g, '-')}.png`)
  }

  return (
    <div
      onClick={onSelect}
      className={`group relative flex h-full w-full min-h-0 flex-col overflow-hidden bg-black text-left transition-all select-none cursor-pointer border ${
        isSelected
          ? 'vms-selected border-cyan-400'
          : alert
            ? 'vms-alert border-rose-500'
            : 'border-line hover:border-line-strong'
      }`}
    >
      {/* Top Header Bar of the Camera View (Compact HUD style) */}
      <div className="flex h-5.5 shrink-0 items-center justify-between bg-black/85 backdrop-blur-xs px-2 text-[10px] text-white/90 border-b border-white/[0.08] z-10 font-mono">
        <div className="flex items-center gap-1.5 truncate">
          <span className={`size-1.5 rounded-full ${alert ? 'bg-rose-500 animate-ping' : 'bg-emerald-400'}`} />
          <span className="font-bold tracking-wider text-ink text-[10px]">{item.name}</span>
          {item.zone && (
            <span className="text-dim text-[9px] font-normal truncate max-w-[90px]">({item.zone})</span>
          )}
        </div>

        <div className="flex items-center gap-2 text-[9px] text-white/70 shrink-0">
          <span className="hidden sm:inline font-mono opacity-80">{nowStr}</span>
          {paused && (
            <span className="flex items-center gap-0.5 rounded bg-amber-500/15 px-1 py-0.2 text-amber-400 font-bold border border-amber-500/25 uppercase">
              Paused
            </span>
          )}
          {item.person_count > 0 && (
            <span className="flex items-center gap-0.5 rounded bg-cyan-500/15 px-1 py-0.2 text-cyan-400 font-bold border border-cyan-500/25">
              <Users size={9} />
              {item.person_count}
            </span>
          )}
          {alert && (
            <span className="rounded bg-rose-600/90 px-1 py-0.2 font-bold text-white uppercase text-[8px] tracking-wide animate-pulse">
              {item.violation_count_recent} VIOLATION
            </span>
          )}
        </div>
      </div>

      {/* Video Content - fills cell perfectly */}
      <div className="relative h-full w-full min-h-0 flex-1 overflow-hidden bg-black">
        <div
          className="absolute inset-0 transition-transform duration-150"
          style={{ transform: `scale(${ZOOM_STEPS[zoomStep]})` }}
        >
          <CameraStream cameraId={item.camera_id} className="size-full" />
          <ZoneOverlay cameraId={item.camera_id} />
        </div>

        {/* Hover / Quick Overlay control bar */}
        <div className="pointer-events-auto absolute inset-x-0 bottom-0 flex h-6.5 items-center justify-between bg-gradient-to-t from-black/90 via-black/60 to-transparent px-2 text-white/80 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onMaximize()
              }}
              title={isMaximized ? 'Minimize' : 'Maximize'}
              className="hover:text-cyan-400 cursor-pointer transition-colors"
            >
              {isMaximized ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                void takeSnapshot()
              }}
              disabled={taking}
              title="Snapshot"
              className="hover:text-cyan-400 cursor-pointer transition-colors disabled:opacity-50"
            >
              {taking ? <Loader2 size={12} className="animate-spin" /> : <Camera size={12} />}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                togglePause()
              }}
              title={paused ? 'Resume' : 'Pause'}
              className="hover:text-white cursor-pointer transition-colors"
            >
              {paused ? <Play size={12} /> : <Pause size={12} />}
            </button>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={(e) => {
                e.stopPropagation()
                setZoomStep((z) => Math.max(0, z - 1))
              }}
              disabled={zoomStep === 0}
              title="Zoom Out"
              className="hover:text-white cursor-pointer transition-colors disabled:opacity-30"
            >
              <ZoomOut size={11} />
            </button>
            <span className="font-mono text-[9px] text-white/60 w-7 text-center">{ZOOM_STEPS[zoomStep]}x</span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                setZoomStep((z) => Math.min(ZOOM_STEPS.length - 1, z + 1))
              }}
              disabled={zoomStep === ZOOM_STEPS.length - 1}
              title="Zoom In"
              className="hover:text-white cursor-pointer transition-colors disabled:opacity-30"
            >
              <ZoomIn size={11} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
