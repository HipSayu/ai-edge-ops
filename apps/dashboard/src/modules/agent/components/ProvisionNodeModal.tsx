import { useState } from 'react'
import { X, Server, Plus, Layers, Camera } from 'lucide-react'
import type { Cluster, NodeAgent } from '@/modules/cluster/types/cluster'

interface Props {
  isOpen: boolean
  onClose: () => void
  clusters: Cluster[]
  defaultClusterId?: string
  onProvision: (node: Partial<NodeAgent>) => void
}

export default function ProvisionNodeModal({
  isOpen,
  onClose,
  clusters,
  defaultClusterId,
  onProvision,
}: Props) {
  const [name, setName] = useState('')
  const [clusterId, setClusterId] = useState(defaultClusterId || clusters[0]?.id || '')
  const [ip, setIp] = useState('')
  const [hardware, setHardware] = useState('NVIDIA Jetson Orin Nano (8GB)')
  const [initialModel, setInitialModel] = useState('yolov8n:v8.2')
  const [initialCamerasCount, setInitialCamerasCount] = useState(2)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !ip.trim() || !clusterId) return

    setIsSubmitting(true)
    setTimeout(() => {
      const targetCluster = clusters.find((c) => c.id === clusterId)
      onProvision({
        id: `node-${name.toLowerCase().replace(/[^a-z0-9]/g, '-')}-${Date.now().toString(36)}`,
        name: name.toUpperCase().trim(),
        clusterId,
        status: 'online',
        ip: ip.trim(),
        hardware,
        agentVersion: 'v2.4.0',
        uptime: '0h 01m',
        cpuUsage: 0,
        gpuUsage: 0,
        ramUsedGb: 3.2,
        ramTotalGb: hardware.includes('64GB') ? 64 : hardware.includes('16GB') ? 16 : 8,
        diskUsage: 22,
        tempC: 0,
        lastHeartbeat: 'Just now',
        modelRunning: initialModel,
        cameras: Array.from({ length: initialCamerasCount }).map((_, i) => ({
          id: `cam-${Date.now()}-${i + 1}`,
          name: `${name.toUpperCase().trim()}-CAM-0${i + 1}`,
          zone: `${targetCluster?.site.split(' ')[0] || 'Zone'} Perimeter`,
          online: true,
          fps: 30,
          resolution: '1920x1080',
          alertCount: 0,
        })),
      })
      setIsSubmitting(false)
      onClose()
    }, 450)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4 bg-muted/20">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-info/10 text-info">
              <Server size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-foreground">Provision New Node Agent</h3>
              <p className="text-[11px] text-muted-foreground">Register and attach an Edge compute device to a cluster</p>
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
                Node Agent Name *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. HN-AGENT-04"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono font-bold text-foreground placeholder:text-muted-foreground/60 focus:border-brand outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Target Cluster *
              </label>
              <div className="relative flex items-center">
                <Layers size={13} className="absolute left-3 text-muted-foreground" />
                <select
                  value={clusterId}
                  onChange={(e) => setClusterId(e.target.value)}
                  className="w-full h-9 rounded-lg border border-border bg-muted/30 pl-8 pr-3 text-foreground outline-none focus:border-brand font-medium"
                >
                  {clusters.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.site.split(' ')[0]})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Device IP Address *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. 192.168.1.150"
                value={ip}
                onChange={(e) => setIp(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono text-foreground placeholder:text-muted-foreground/60 focus:border-brand outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Hardware Platform
              </label>
              <select
                value={hardware}
                onChange={(e) => setHardware(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 text-foreground outline-none focus:border-brand font-medium"
              >
                <option value="NVIDIA Jetson Orin Nano (8GB)">NVIDIA Jetson Orin Nano (8GB)</option>
                <option value="NVIDIA Jetson Orin NX (16GB)">NVIDIA Jetson Orin NX (16GB)</option>
                <option value="NVIDIA Jetson AGX Orin (64GB)">NVIDIA Jetson AGX Orin (64GB)</option>
                <option value="Intel NUC 13 Core i7 (32GB)">Intel NUC 13 Core i7 (32GB)</option>
                <option value="Raspberry Pi 5 (8GB AI Kit)">Raspberry Pi 5 (8GB AI Kit)</option>
                <option value="x86 GPU Server (RTX 4090)">x86 GPU Server (RTX 4090)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Initial Default Model
              </label>
              <select
                value={initialModel}
                onChange={(e) => setInitialModel(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono text-foreground outline-none focus:border-brand font-medium"
              >
                <option value="yolov8n:v8.2">yolov8n:v8.2 (Nano - Fast)</option>
                <option value="yolov8s:v8.2">yolov8s:v8.2 (Small - Balanced)</option>
                <option value="yolov8m:v8.2">yolov8m:v8.2 (Medium - Accurate)</option>
                <option value="yolov11n:latest">yolov11n:latest (Next-Gen)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Initial Attached Cameras
              </label>
              <div className="relative flex items-center">
                <Camera size={13} className="absolute left-3 text-muted-foreground" />
                <input
                  type="number"
                  min={0}
                  max={16}
                  value={initialCamerasCount}
                  onChange={(e) => setInitialCamerasCount(Number(e.target.value))}
                  className="w-full h-9 rounded-lg border border-border bg-muted/30 pl-8 pr-3 font-mono text-foreground outline-none focus:border-brand"
                />
              </div>
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
              className="flex items-center gap-1.5 rounded-lg bg-info px-4 py-2 text-xs font-bold text-white hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
            >
              <Plus size={14} />
              <span>{isSubmitting ? 'Provisioning...' : 'Provision Node'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
