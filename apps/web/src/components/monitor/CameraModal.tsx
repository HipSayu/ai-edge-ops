import { useEffect, useState } from 'react'
import { AlertCircle, Clock, Sparkles } from 'lucide-react'
import type { GridItem, ViolationEvent } from '@/api/types'
import CameraStream from '@/components/monitor/CameraStream'
import { Badge, Modal } from '@/components/ui'
import { VIOLATION_LABEL } from '@/constants/labels'
import { ZoneLayer, ZonePanel, useZoneEditor } from '@/components/monitor/ZoneEditor'
import { useAuth } from '@/contexts/AuthContext'
import AuthImage from '@/components/ui/AuthImage'
import { snapshotUrl } from '@/helpers/media'
import { cameraService } from '@/services/camera.service'
import { formatPercent, formatTime } from '@/utils/format'

export default function CameraModal({ item, onClose }: { item: GridItem; onClose: () => void }) {
  const [events, setEvents] = useState<ViolationEvent[]>([])
  const [isMaximized, setIsMaximized] = useState(false)
  const { canOperate } = useAuth()
  const zones = useZoneEditor(item.camera_id)

  useEffect(() => {
    let alive = true
    const load = () =>
      cameraService
        .events(item.camera_id)
        .then((e) => alive && setEvents(e))
        .catch(() => {})
    load()
    const timer = setInterval(load, 4000)
    return () => {
      alive = false
      clearInterval(timer)
    }
  }, [item.camera_id])

  return (
    <Modal
      title={`${item.name}${item.zone ? ` · ${item.zone}` : ''}`}
      onClose={onClose}
      wide
      isMaximized={isMaximized}
      onToggleMaximize={() => setIsMaximized((prev) => !prev)}
    >
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        {/* Large Stream View */}
        <div className="space-y-3">
          <div className="relative aspect-video w-full overflow-hidden rounded-xl border border-line bg-black shadow-lg">
            <CameraStream cameraId={item.camera_id} className="size-full" />
            <ZoneLayer editor={zones} />
            <div className="absolute left-3 top-3 flex items-center gap-2">
              <span className="flex items-center gap-1 rounded bg-black/70 px-2 py-0.5 text-xs font-bold text-white border border-white/10">
                <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
                LIVE STREAM
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between text-xs text-dim px-1 font-mono">
            <span>Channel ID: {item.camera_id}</span>
            <span>Real-time Edge Inference</span>
          </div>
          <ZonePanel editor={zones} canEdit={canOperate} />
        </div>

        {/* Real-time Violation Event Timeline */}
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between pb-2.5 border-b border-line mb-2.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-ink flex items-center gap-1.5">
              <AlertCircle size={14} className="text-rose-500" />
              Recent Violation Events
            </h3>
            <span className="text-xs font-semibold text-dim">{events.length} detected</span>
          </div>

          <ul className="scroll-thin max-h-[380px] space-y-2 overflow-y-auto pr-1">
            {events.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="grid size-9 place-items-center rounded-lg bg-emerald-500/10 text-emerald-400 mb-2">
                  <Sparkles size={16} />
                </div>
                <p className="text-xs font-medium text-dim">No violations recorded</p>
                <p className="text-[11px] text-dim/70">Compliance standards fully observed in this sector</p>
              </div>
            )}
            {events.map((e) => (
              <li
                key={e.id}
                className="flex items-center gap-2.5 rounded-lg border border-line bg-panel2/40 p-2 transition-all hover:border-line-strong hover:bg-panel2"
              >
                <AuthImage
                  src={snapshotUrl(e.id)}
                  alt=""
                  className="size-11 shrink-0 rounded bg-black object-cover border border-line"
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-bold text-ink">{VIOLATION_LABEL[e.violation_type]}</p>
                  <p className="flex items-center gap-1 text-[11px] text-dim font-mono mt-0.5">
                    <Clock size={11} />
                    {formatTime(e.created_at)}
                  </p>
                </div>
                <Badge tone="danger" dot>
                  {formatPercent(e.confidence)}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Modal>
  )
}
