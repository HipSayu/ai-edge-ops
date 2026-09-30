import { useState } from 'react'
import { X, Camera, Server, Plus } from 'lucide-react'
import type { Cluster } from '@/modules/cluster/types/cluster'

interface Props {
  isOpen: boolean
  onClose: () => void
  clusters: Cluster[]
  defaultNodeId?: string
  onAddCamera: (cameraData: Record<string, unknown>) => void
}

export default function AddCameraModal({
  isOpen,
  onClose,
  clusters,
  defaultNodeId,
  onAddCamera,
}: Props) {
  const [name, setName] = useState('')
  const [streamUrl, setStreamUrl] = useState('')
  const [zone, setZone] = useState('Gate A')
  const [selectedNodeId, setSelectedNodeId] = useState(defaultNodeId || '')
  const [resolution, setResolution] = useState('1920x1080')
  const [fps, setFps] = useState(30)
  const [model, setModel] = useState('yolov8n')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  // Flatten all nodes from all clusters
  const allNodes = clusters.flatMap((c) =>
    c.nodes.map((n) => ({
      id: n.id,
      name: n.name,
      clusterName: c.name,
      ip: n.ip,
    }))
  )

  const effectiveNodeId = selectedNodeId || allNodes[0]?.id || ''

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !streamUrl.trim()) return

    setIsSubmitting(true)
    setTimeout(() => {
      onAddCamera({
        id: `cam-${Date.now()}`,
        name: name.toUpperCase(),
        zone,
        nodeId: effectiveNodeId,
        deviceId: effectiveNodeId,
        online: true,
        alertCount: 0,
        thumbHue: Math.floor(Math.random() * 360),
        runtime: {
          resolution,
          protocol: streamUrl.startsWith('rtsp') ? 'RTSP' : 'WebRTC',
          model,
          fps,
          roiZones: 2,
          lastHeartbeat: 'Just now',
          streamUrl,
        },
      })
      setIsSubmitting(false)
      onClose()
    }, 500)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4 bg-muted/20">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-purple-500/10 text-purple-500">
              <Camera size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-foreground">Connect New Camera Feed</h3>
              <p className="text-[11px] text-muted-foreground">Attach RTSP / WebRTC stream to target Node Agent</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Camera Name *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. CAM-GATE-01"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono font-bold text-foreground placeholder:text-muted-foreground/60 focus:border-brand outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Zone / ROI Area *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Gate A / Loading Bay"
                value={zone}
                onChange={(e) => setZone(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 text-foreground outline-none focus:border-brand"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
              Stream Ingest URL (RTSP / WebRTC) *
            </label>
            <input
              type="text"
              required
              placeholder="rtsp://admin:pass@192.168.1.50:554/ch1/main"
              value={streamUrl}
              onChange={(e) => setStreamUrl(e.target.value)}
              className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono text-foreground placeholder:text-muted-foreground/60 focus:border-brand outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Assign to Node Agent *
              </label>
              <div className="relative flex items-center">
                <Server size={13} className="absolute left-3 text-muted-foreground" />
                <select
                  value={effectiveNodeId}
                  onChange={(e) => setSelectedNodeId(e.target.value)}
                  className="w-full h-9 rounded-lg border border-border bg-muted/30 pl-8 pr-3 text-foreground outline-none focus:border-brand font-medium"
                >
                  {allNodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.name} ({n.clusterName})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Vision AI Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono text-foreground outline-none focus:border-brand font-semibold"
              >
                <option value="yolov8n">yolov8n (Fast Detection)</option>
                <option value="yolov8s">yolov8s (Accurate)</option>
                <option value="yolov8-pose">yolov8-pose (Safety Guard)</option>
                <option value="yolov11n">yolov11n (Next-Gen)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Stream Resolution
              </label>
              <select
                value={resolution}
                onChange={(e) => setResolution(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono text-foreground outline-none focus:border-brand"
              >
                <option value="1920x1080">1920 × 1080 (1080p FHD)</option>
                <option value="1280x720">1280 × 720 (720p HD)</option>
                <option value="2560x1440">2560 × 1440 (2K QHD)</option>
                <option value="3840x2160">3840 × 2160 (4K UHD)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Target Framerate (FPS)
              </label>
              <input
                type="number"
                min={5}
                max={60}
                value={fps}
                onChange={(e) => setFps(Number(e.target.value))}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono text-foreground outline-none focus:border-brand font-bold"
              />
            </div>
          </div>

          {/* Footer buttons */}
          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-border mt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-xs font-bold text-white hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
            >
              <Plus size={14} />
              <span>{isSubmitting ? 'Connecting Feed...' : 'Connect Camera'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
