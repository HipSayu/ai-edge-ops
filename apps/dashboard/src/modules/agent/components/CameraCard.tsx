import { useCallback, useEffect, useState } from 'react'
import { Wifi, WifiOff, Play, Activity } from 'lucide-react'
import type { Camera, EdgeDevice } from '@/modules/agent/types'
import { agentService } from '@/modules/agent/services/agent'
import WhepVideo, { type WhepStats } from '@/modules/agent/components/WhepVideo'
import { Card } from '@/shared/components/Card'
import { Badge } from '@/shared/components/Badge'
import { Button } from '@/shared/components/Button'

interface Props {
  camera: Camera
  onOpen: (camera: Camera) => void
}

/** One camera tile: live WHEP thumbnail + real stream/pipeline stats. */
export default function CameraCard({ camera, onOpen }: Props) {
  const [stats, setStats] = useState<WhepStats | null>(null)
  const [live, setLive] = useState(false)
  const [device, setDevice] = useState<EdgeDevice | null>(null)

  useEffect(() => {
    if (!camera.deviceId) return
    let active = true
    agentService
      .getDevice(camera.deviceId)
      .then((d) => active && setDevice(d))
      .catch(() => {})
    return () => {
      active = false
    }
  }, [camera.deviceId])

  const handleStats = useCallback((s: WhepStats) => setStats(s), [])
  const handleStatus = useCallback((s: 'connecting' | 'live' | 'error') => setLive(s === 'live'), [])

  const resolution = stats?.width ? `${stats.width}×${stats.height}` : '—'
  const fps = stats?.fps ?? 0
  const model = device?.modelRunning && device.modelRunning !== 'No model reported'
    ? device.modelRunning
    : '—'

  return (
    <Card className="flex flex-col overflow-hidden p-0 transition-all hover:shadow-lg hover:border-border/90">
      {/* Video Thumbnail Header */}
      <div className="relative aspect-video w-full bg-slate-950 overflow-hidden group">
        {camera.online ? (
          <WhepVideo cameraId={camera.id} muted onStats={handleStats} onStatusChange={handleStatus} />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-slate-500">
            <WifiOff size={32} />
            <span className="text-xs font-semibold">Feed Disconnected</span>
          </div>
        )}
        {camera.online && (
          <div className="absolute top-2.5 left-2.5 z-10">
            <Badge variant={live ? 'healthy' : 'warning'} dot size="sm" className="backdrop-blur-md bg-slate-900/80">
              {live ? 'LIVE' : 'CONNECTING'}
            </Badge>
          </div>
        )}
      </div>

      {/* Card Body */}
      <div className="flex flex-col flex-1 p-4 space-y-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="font-bold text-sm text-foreground tracking-tight">{camera.id}</h3>
            <p className="text-xs text-muted-foreground mt-0.5">{camera.name} · {camera.zone}</p>
          </div>
          {camera.alertCount > 0 ? (
            <Badge variant="critical" size="sm">{camera.alertCount} ALERTS</Badge>
          ) : (
            <Badge variant="neutral" size="sm">NORMAL</Badge>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs font-medium border-t border-b border-border/50 py-2">
          {camera.online ? (
            <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
              <Wifi size={14} />
              <span>{live ? 'Streaming' : 'Connecting'} • {fps} FPS</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-rose-600 dark:text-rose-400">
              <WifiOff size={14} />
              <span>Connection Lost</span>
            </div>
          )}
        </div>

        {/* Runtime & Pipeline details */}
        <div className="space-y-1.5 text-xs">
          <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5 mb-2">
            <Activity size={12} className="text-brand" />
            <span>Inference Pipeline</span>
          </div>
          <div className="grid grid-cols-2 gap-y-1.5 gap-x-2 text-[11.5px]">
            <div className="text-muted-foreground">Assigned Model:</div>
            <div className="font-bold text-brand truncate text-right">{model}</div>

            <div className="text-muted-foreground">Resolution:</div>
            <div className="font-mono text-foreground text-right">{resolution}</div>

            <div className="text-muted-foreground">Protocol:</div>
            <div className="font-mono text-foreground text-right">{live ? 'WebRTC / WHEP' : camera.runtime.protocol}</div>

            <div className="text-muted-foreground">Bitrate:</div>
            <div className="font-mono text-foreground text-right">{stats?.bitrateKbps ? `${stats.bitrateKbps} kbps` : '—'}</div>
          </div>
        </div>

        {/* Action Button */}
        <Button
          variant="brand"
          size="sm"
          className="w-full mt-auto"
          leftIcon={<Play size={14} />}
          onClick={() => onOpen(camera)}
        >
          View Stream &amp; HUD
        </Button>
      </div>
    </Card>
  )
}

