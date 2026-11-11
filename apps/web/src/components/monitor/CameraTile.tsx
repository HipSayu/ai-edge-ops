import { Maximize2, ShieldAlert, TriangleAlert, Users } from 'lucide-react'
import type { GridItem } from '@/api/types'
import CameraStream from '@/components/monitor/CameraStream'
import ZoneOverlay from '@/components/monitor/ZoneOverlay'

export default function CameraTile({ item, onOpen }: { item: GridItem; onOpen: () => void }) {
  const alert = item.violation_count_recent > 0

  return (
    <div
      onClick={onOpen}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onOpen()
      }}
      className={`group relative flex flex-col overflow-hidden rounded-2xl border bg-panel transition-all duration-300 cursor-pointer shadow-xs hover:shadow-xl hover:-translate-y-0.5 ${
        alert
          ? 'alert-ring border-danger/60 hover:border-danger'
          : 'border-line hover:border-brand/60'
      }`}
    >
      {/* Video Container */}
      <div className="relative aspect-video w-full overflow-hidden bg-black">
        <CameraStream cameraId={item.camera_id} className="size-full" />
        <ZoneOverlay cameraId={item.camera_id} />

        {/* Live overlay badges */}
        <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between p-3 bg-gradient-to-b from-black/80 via-black/40 to-transparent">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 rounded-sm bg-black/70 px-2 py-0.5 text-[11px] font-bold tracking-wider text-white backdrop-blur-md border border-white/10">
              <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
              LIVE
            </span>
            {alert && (
              <span className="flex items-center gap-1 rounded-sm bg-rose-600 px-2 py-0.5 text-[11px] font-bold text-white backdrop-blur-md shadow-sm shadow-rose-500/30">
                <TriangleAlert size={12} />
                CẢNH BÁO
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            <span className="flex items-center gap-1.5 rounded-sm bg-black/70 px-2.5 py-0.5 text-xs font-semibold text-white backdrop-blur-md border border-white/10">
              <Users size={12} className="text-blue-400" />
              <span>{item.person_count}</span>
            </span>
          </div>
        </div>

        {/* Hover Action overlay */}
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-brand/10 opacity-0 backdrop-blur-[2px] transition-opacity duration-200 group-hover:opacity-100">
          <span className="flex items-center gap-1.5 rounded-xl bg-black/70 px-3 py-1.5 text-xs font-semibold text-white shadow-lg border border-white/20">
            <Maximize2 size={13} />
            Xem chi tiết & sự kiện
          </span>
        </div>
      </div>

      {/* Card Footer Info */}
      <div className="flex items-center justify-between border-t border-line/60 bg-panel px-3.5 py-3">
        <div className="min-w-0 pr-2">
          <p className="truncate text-sm font-semibold text-ink group-hover:text-brand transition-colors">
            {item.name}
          </p>
          <p className="truncate text-xs text-dim">
            {item.zone ? item.zone : 'No zone'}
          </p>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {item.violation_count_recent > 0 ? (
            <span className="flex items-center gap-1 rounded-lg bg-rose-500/10 px-2 py-1 text-xs font-bold text-rose-500 border border-rose-500/20">
              <ShieldAlert size={13} />
              {item.violation_count_recent} vi phạm
            </span>
          ) : (
            <span className="rounded-lg bg-emerald-500/10 px-2 py-1 text-[11px] font-medium text-emerald-500 border border-emerald-500/20">
              Chuẩn an toàn
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
