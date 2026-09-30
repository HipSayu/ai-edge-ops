import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Server,
  Camera,
  Thermometer,
  Cpu,
  HardDrive,
  MemoryStick,
  Zap,
  AlertTriangle,
  XCircle,
  Terminal,
  ChevronRight,
  Plus,
} from 'lucide-react'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'
import type { NodeAgent, CameraOnNode } from '@/modules/cluster/types/cluster'
import ProvisionNodeModal from '@/modules/agent/components/ProvisionNodeModal'
import StatCard from '@/shared/components/StatCard'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function statusDot(status: string) {
  switch (status) {
    case 'healthy':
    case 'online':
      return 'bg-success'
    case 'degraded':
      return 'bg-warning'
    case 'critical':
    case 'offline':
      return 'bg-destructive'
    default:
      return 'bg-muted-foreground'
  }
}

function statusBadge(status: string) {
  switch (status) {
    case 'healthy':
      return 'bg-success/10 text-success border-success/20'
    case 'degraded':
      return 'bg-warning/10 text-warning border-warning/20'
    case 'critical':
      return 'bg-destructive/10 text-destructive border-destructive/20'
    case 'offline':
      return 'bg-muted text-muted-foreground border-border'
    default:
      return 'bg-muted text-muted-foreground border-border'
  }
}

function metricColor(value: number, warn: number, danger: number) {
  if (value >= danger) return 'bg-destructive'
  if (value >= warn) return 'bg-warning'
  return 'bg-success'
}

// ─── Metric bar ───────────────────────────────────────────────────────────────

interface MetricBarProps {
  label: string
  value: number
  max?: number
  unit?: string
  warn?: number
  danger?: number
  icon?: React.ReactNode
}

function MetricBar({ label, value, max = 100, unit = '%', warn = 70, danger = 85, icon }: MetricBarProps) {
  const pct = Math.min(100, (value / max) * 100)
  const barColor = metricColor(pct, warn, danger)

  return (
    <div className="flex flex-col gap-0.5">
      <div className="flex items-center justify-between text-[10px]">
        <span className="flex items-center gap-1 text-muted-foreground font-medium">
          {icon}
          {label}
        </span>
        <span className="font-mono font-semibold text-foreground tabular-nums">
          {value}{unit}
          {max !== 100 && <span className="text-muted-foreground font-normal">/{max}{unit}</span>}
        </span>
      </div>
      <div className="h-1 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

// ─── Camera table row ─────────────────────────────────────────────────────────

function CamRow({ cam }: { cam: CameraOnNode }) {
  return (
    <tr className="border-b border-border/50 last:border-0 hover:bg-muted/30 transition-colors">
      <td className="px-2.5 py-1.5 text-xs font-medium text-foreground">{cam.name}</td>
      <td className="px-2.5 py-1.5 text-[11px] text-muted-foreground">{cam.zone}</td>
      <td className="px-2.5 py-1.5">
        <span className={`flex items-center gap-1 text-[11px] ${cam.online ? 'text-success' : 'text-destructive'}`}>
          <span className={`size-1.5 rounded-full ${statusDot(cam.online ? 'online' : 'offline')}`} />
          {cam.online ? 'Online' : 'Offline'}
        </span>
      </td>
      <td className="px-2.5 py-1.5 text-right text-xs font-mono text-foreground">
        {cam.online ? cam.fps : '—'}
      </td>
      <td className="px-2.5 py-1.5 text-right text-[11px] text-muted-foreground hidden sm:table-cell">
        {cam.resolution}
      </td>
    </tr>
  )
}

// ─── Node card ────────────────────────────────────────────────────────────────

function NodeCard({ node }: { node: NodeAgent }) {
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden flex flex-col">
      {/* Node header */}
      <div className="flex items-start gap-2.5 p-3.5 border-b border-border">
        <span className={`mt-1 size-2 shrink-0 rounded-full ${statusDot(node.status)}`} />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-bold text-foreground">{node.name}</span>
            <span className={`rounded-full border px-1.5 py-px text-[9px] font-semibold ${statusBadge(node.status)}`}>
              {node.status}
            </span>
          </div>
          <p className="text-[10px] text-muted-foreground font-mono mt-0.5">{node.ip}</p>
          <p className="text-[10px] text-muted-foreground mt-0.5 truncate">{node.hardware}</p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-[9px] text-muted-foreground">Agent</p>
          <p className="text-[10px] font-mono font-medium text-foreground">{node.agentVersion || '—'}</p>
        </div>
      </div>

      {/* Metrics */}
      {node.status !== 'offline' && (
        <div className="p-3 flex flex-col gap-2 border-b border-border bg-muted/10">
          <MetricBar label="CPU" value={node.cpuUsage} icon={<Cpu size={9} />} warn={70} danger={85} />
          <MetricBar label="GPU" value={node.gpuUsage} icon={<Zap size={9} />} warn={75} danger={90} />
          <MetricBar label="RAM" value={node.ramUsedGb} max={node.ramTotalGb} unit=" GB" icon={<MemoryStick size={9} />} warn={70} danger={88} />
          <MetricBar label="Disk" value={node.diskUsage} icon={<HardDrive size={9} />} warn={75} danger={90} />
          <div className="flex items-center justify-between text-[10px] mt-0.5">
            <span className="flex items-center gap-1 text-muted-foreground font-medium">
              <Thermometer size={9} />
              Thermal
            </span>
            <span className={`font-mono font-semibold ${node.tempC >= 75 ? 'text-destructive' : node.tempC >= 60 ? 'text-warning' : 'text-success'}`}>
              {node.tempC}°C
            </span>
          </div>
        </div>
      )}

      {/* Camera mini table */}
      <div className="flex-1 p-3">
        <div className="flex items-center justify-between mb-1.5 text-[10.5px] font-bold text-foreground">
          <span>Assigned Cameras ({node.cameras.length})</span>
        </div>
        <div className="rounded-lg border border-border overflow-hidden">
          <table className="w-full text-left">
            <tbody className="divide-y divide-border/50">
              {node.cameras.map((cam) => (
                <CamRow key={cam.id} cam={cam} />
              ))}
              {node.cameras.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-2 text-center text-[10px] text-muted-foreground">
                    No cameras attached.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Node Detail & Runtimes Link */}
      <Link
        to={`/agent/nodes/${node.id}`}
        className="flex items-center justify-between border-t border-border bg-muted/20 px-3.5 py-2 text-xs font-semibold text-brand hover:bg-muted/40 transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <Terminal size={12} />
          <span>Node Telemetry &amp; Runtimes</span>
        </span>
        <ChevronRight size={13} />
      </Link>
    </div>
  )
}

// ─── Main Cluster Detail Page ──────────────────────────────────────────────────

export default function ClusterDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { clusters, loading, provisionNode } = useEdgeOps()
  const [showProvisionModal, setShowProvisionModal] = useState(false)

  const cluster = clusters.find((c) => c.id === id || c.name.toLowerCase() === id?.toLowerCase())

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <div className="flex items-center gap-2 text-sm">
          <div className="size-4 animate-spin rounded-full border-2 border-border border-t-brand" />
          Loading cluster details…
        </div>
      </div>
    )
  }

  if (!cluster) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-12">
        <XCircle size={36} className="text-destructive" />
        <p className="text-foreground font-semibold">Cluster not found</p>
        <Link
          to="/agent/clusters"
          className="rounded-lg bg-brand px-4 py-2 text-xs font-semibold text-white hover:opacity-90 transition-opacity"
        >
          ← Back to Clusters
        </Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Provision Node Modal */}
      <ProvisionNodeModal
        isOpen={showProvisionModal}
        onClose={() => setShowProvisionModal(false)}
        clusters={clusters}
        defaultClusterId={cluster.id}
        onProvision={(node) => provisionNode(cluster.id, node as import('@/modules/cluster/types/cluster').NodeAgent)}
      />

      {/* Cluster Title Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-foreground">{cluster.name}</h1>
            <span className={`rounded-full border px-2.5 py-0.5 text-xs font-bold ${statusBadge(cluster.status)}`}>
              {cluster.status}
            </span>
          </div>
          <p className="text-xs text-muted-foreground">{cluster.site} · {cluster.description}</p>
        </div>

        <button
          onClick={() => setShowProvisionModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-brand px-3.5 py-2 text-xs font-semibold text-white hover:opacity-90 transition-opacity cursor-pointer"
        >
          <Plus size={13} />
          <span>Provision Node to Cluster</span>
        </button>
      </div>

      {/* ── Compact Cluster Telemetry KPI Bar ── */}
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard
          label="Nodes Online"
          value={`${cluster.onlineNodes} / ${cluster.totalNodes}`}
          icon={<Server size={15} />}
          variant="brand"
        />
        <StatCard
          label="Cameras Live"
          value={`${cluster.onlineCameras} / ${cluster.totalCameras}`}
          icon={<Camera size={15} />}
          variant="purple"
        />
        <StatCard
          label="Aggregate FPS"
          value={`${cluster.aggregateFps} FPS`}
          icon={<Zap size={15} />}
          variant="success"
        />
        <StatCard
          label="Avg CPU Load"
          value={`${cluster.avgCpuUsage}%`}
          icon={<Cpu size={15} />}
          variant="info"
        />
        <StatCard
          label="Avg Temp"
          value={`${cluster.avgTempC}°C`}
          icon={<Thermometer size={15} />}
          variant="warning"
        />
        <StatCard
          label="Cluster Alerts"
          value={cluster.totalAlerts}
          icon={<AlertTriangle size={15} />}
          variant={cluster.totalAlerts > 0 ? 'destructive' : 'info'}
        />
      </div>

      {/* ── Node Agents Grid ── */}
      <div className="flex items-center justify-between pt-1">
        <h2 className="text-xs font-bold tracking-wider text-muted-foreground">
          Cluster Nodes &amp; Hardware Matrices
        </h2>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {cluster.nodes.map((node) => (
          <NodeCard key={node.id} node={node} />
        ))}
      </div>
    </div>
  )
}
