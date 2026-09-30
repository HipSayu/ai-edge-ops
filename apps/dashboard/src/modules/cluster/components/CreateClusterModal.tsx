import { useState } from 'react'
import { X, Network, Plus, MapPin, Server } from 'lucide-react'
import type { Cluster } from '@/modules/cluster/types/cluster'

interface Props {
  isOpen: boolean
  onClose: () => void
  onCreateCluster: (cluster: Partial<Cluster>) => void
}

export default function CreateClusterModal({ isOpen, onClose, onCreateCluster }: Props) {
  const [name, setName] = useState('')
  const [site, setSite] = useState('')
  const [region, setRegion] = useState('North')
  const [description, setDescription] = useState('')
  const [initialNodeIp, setInitialNodeIp] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !site.trim()) return

    setIsSubmitting(true)
    setTimeout(() => {
      const newClusterId = `cluster-${name.toLowerCase().replace(/[^a-z0-9]/g, '-')}-${Date.now().toString(36)}`
      onCreateCluster({
        id: newClusterId,
        name: name.toUpperCase().trim(),
        site: site.trim(),
        description: description.trim() || `${region} Edge Vision Processing Site`,
        status: 'healthy',
        totalNodes: initialNodeIp.trim() ? 1 : 0,
        onlineNodes: initialNodeIp.trim() ? 1 : 0,
        totalCameras: 0,
        onlineCameras: 0,
        totalAlerts: 0,
        avgCpuUsage: 18,
        avgGpuUsage: 25,
        avgTempC: 39,
        aggregateFps: 0,
        nodes: initialNodeIp.trim()
          ? [
              {
                id: `node-${Date.now().toString(36)}`,
                name: `${name.toUpperCase().trim()}-GW-01`,
                clusterId: newClusterId,
                status: 'online',
                ip: initialNodeIp.trim(),
                hardware: 'NVIDIA Jetson Orin AGX 64GB',
                agentVersion: 'v2.4.0',
                uptime: '0h 01m',
                cpuUsage: 18,
                gpuUsage: 25,
                ramUsedGb: 6.2,
                ramTotalGb: 64,
                diskUsage: 28,
                tempC: 39,
                lastHeartbeat: 'Just now',
                cameras: [],
                modelRunning: 'yolov8x-safety-v2',
              },
            ]
          : [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
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
            <div className="flex size-8 items-center justify-center rounded-lg bg-brand/10 text-brand">
              <Network size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-foreground">Create New Edge Cluster</h3>
              <p className="text-[11px] text-muted-foreground">Provision a distributed multi-node site cluster</p>
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
          <div>
            <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
              Cluster Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. HN-LOGISTICS-02"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 font-mono font-bold text-foreground placeholder:text-muted-foreground/60 focus:border-brand outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Site Location *
              </label>
              <div className="relative flex items-center">
                <MapPin size={13} className="absolute left-3 text-muted-foreground" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Dinh Vu Warehouse"
                  value={site}
                  onChange={(e) => setSite(e.target.value)}
                  className="w-full h-9 rounded-lg border border-border bg-muted/30 pl-8 pr-3 text-foreground placeholder:text-muted-foreground/60 focus:border-brand outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
                Region
              </label>
              <select
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full h-9 rounded-lg border border-border bg-muted/30 px-3 text-foreground outline-none focus:border-brand font-medium"
              >
                <option value="North">North Region</option>
                <option value="Central">Central Region</option>
                <option value="South">South Region</option>
                <option value="Cloud/HQ">Cloud / Headquarter</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-muted-foreground tracking-wider mb-1.5">
              Description
            </label>
            <textarea
              rows={2}
              placeholder="Operational purpose, network topology or surveillance scope..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-border bg-muted/30 p-2.5 text-foreground placeholder:text-muted-foreground/60 focus:border-brand outline-none resize-none"
            />
          </div>

          <div className="rounded-xl border border-border bg-muted/15 p-3.5 flex flex-col gap-2">
            <span className="flex items-center gap-1.5 font-bold text-foreground text-[11.5px]">
              <Server size={13} className="text-info" />
              Initial Gateway Node (Optional)
            </span>
            <input
              type="text"
              placeholder="Master Node IP address, e.g. 192.168.1.100"
              value={initialNodeIp}
              onChange={(e) => setInitialNodeIp(e.target.value)}
              className="w-full h-8 rounded-lg border border-border bg-background px-3 font-mono text-xs text-foreground placeholder:text-muted-foreground/60 focus:border-brand outline-none"
            />
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
              <span>{isSubmitting ? 'Creating Cluster...' : 'Create Cluster'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
