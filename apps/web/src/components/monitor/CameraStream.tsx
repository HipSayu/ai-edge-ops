import { useCallback, useState } from 'react'
import { VideoOff } from 'lucide-react'
import LiveCanvas from '@/overlay/LiveCanvas'

export default function CameraStream({
  cameraId,
  className = '',
}: {
  cameraId: number // the video with its detection boxes, drawn together from the same frames
  className?: string
}) {
  const [failed, setFailed] = useState(false)
  const fail = useCallback(() => setFailed(true), [])

  if (failed) {
    return (
      <div
        className={`relative grid place-items-center overflow-hidden bg-slate-950 text-slate-400 ${className}`}
      >
        {/* Subtle scanline effect */}
        <div className="scanline" />
        <div className="absolute inset-0 bg-grid-pattern opacity-10" />

        <div className="relative z-10 flex flex-col items-center gap-2 text-center p-4">
          <div className="grid size-10 place-items-center rounded-xl bg-slate-800/80 text-slate-400 border border-slate-700/50 shadow-inner">
            <VideoOff size={18} />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-300">Signal lost</p>
            <p className="text-[11px] text-slate-500">Check the camera stream connection</p>
          </div>
        </div>

        {/* Tech decorative HUD corners */}
        <div className="pointer-events-none absolute left-2 top-2 size-3 border-l-2 border-t-2 border-slate-700/60" />
        <div className="pointer-events-none absolute right-2 top-2 size-3 border-r-2 border-t-2 border-slate-700/60" />
        <div className="pointer-events-none absolute bottom-2 left-2 size-3 border-b-2 border-l-2 border-slate-700/60" />
        <div className="pointer-events-none absolute bottom-2 right-2 size-3 border-b-2 border-r-2 border-slate-700/60" />
      </div>
    )
  }

  return (
    <div className={`relative overflow-hidden bg-black ${className}`}>
      <LiveCanvas cameraId={cameraId} onFail={fail} />
    </div>
  )
}
