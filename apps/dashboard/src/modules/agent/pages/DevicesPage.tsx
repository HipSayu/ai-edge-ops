import { useState, useMemo } from 'react'
import {
  Server, Search, RotateCw, Cpu,
  Activity, Plus, ChevronRight, Terminal,
  CheckCircle2, AlertTriangle, Camera, Filter,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'
import Pagination from '@/shared/components/Pagination'
import StatCard from '@/shared/components/StatCard'
import type { NodeAgent } from '@/modules/cluster/types/cluster'

// ─── Status Badge ─────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: NodeAgent['status'] }) {
  const cfg = {
    online: { cls: 'bg-success/10 text-success border-success/30', dot: 'bg-success animate-pulse', label: 'Healthy' },
    degraded: { cls: 'bg-warning/10 text-warning border-warning/30', dot: 'bg-warning', label: 'Degraded' },
    offline: { cls: 'bg-destructive/10 text-destructive border-destructive/30', dot: 'bg-destructive', label: 'Offline' },
  }[status]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${cfg.cls}`}>
      <span className={`size-1.5 rounded-full ${cfg.dot}`} />
      <span>{cfg.label}</span>
    </span>
  )
}

// ─── Compact Node Card ───────────────────────────────────────────────────────
function NodeCard({ node, clusterName, onRestart }: {
  node: NodeAgent; clusterName: string; onRestart: (id: string) => void
}) {
  const isHealthy = node.status === 'online'

  return (
    <div className="flex flex-col justify-between rounded-xl border border-border bg-card p-4 transition-all hover:border-border/80">
      {/* Top info */}
      <div className="flex flex-col gap-3">
        {/* Header: Name + Health status */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${
              isHealthy ? 'bg-success/10 text-success' : node.status === 'degraded' ? 'bg-warning/10 text-warning' : 'bg-destructive/10 text-destructive'
            }`}>
              <Server size={15} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-sm font-bold text-foreground truncate">{node.name}</span>
                <span className="font-mono text-[10.5px] text-muted-foreground">({node.id})</span>
              </div>
              <div className="text-[11px] text-muted-foreground truncate">{node.hardware} · <span className="text-brand font-medium">{clusterName}</span></div>
            </div>
          </div>
          <StatusBadge status={node.status} />
        </div>

        {/* Essential Core Health Metrics (CPU, GPU, RAM) */}
        <div className="grid grid-cols-3 gap-2 rounded-lg border border-border/60 bg-muted/10 p-2.5 text-center">
          <div>
            <div className="text-[10px] text-muted-foreground">CPU Load</div>
            <div className={`text-sm font-bold font-mono ${node.cpuUsage > 85 ? 'text-destructive' : node.cpuUsage > 70 ? 'text-warning' : 'text-foreground'}`}>
              {node.cpuUsage}%
            </div>
          </div>
          <div>
            <div className="text-[10px] text-muted-foreground">GPU Load</div>
            <div className={`text-sm font-bold font-mono ${node.gpuUsage > 85 ? 'text-destructive' : node.gpuUsage > 70 ? 'text-warning' : 'text-foreground'}`}>
              {node.gpuUsage}%
            </div>
          </div>
          <div>
            <div className="text-[10px] text-muted-foreground">Cameras</div>
            <div className="text-sm font-bold font-mono text-info flex items-center justify-center gap-1">
              <Camera size={12} />
              {node.cameras.length}
            </div>
          </div>
        </div>

        {/* Quick IP & AI Model */}
        <div className="flex items-center justify-between text-[11px] text-muted-foreground px-0.5">
          <span className="font-mono">IP: <strong className="text-foreground">{node.ip}</strong></span>
          <span className="font-mono truncate max-w-[150px]">Model: <strong className="text-brand">{node.modelRunning}</strong></span>
        </div>
      </div>

      {/* Action footer */}
      <div className="flex items-center gap-2 pt-3 mt-3 border-t border-border/60">
        <Link
          to={`/agent/nodes/${node.id}`}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 transition-opacity"
        >
          <Terminal size={13} />
          <span>Xem Runtimes &amp; Logs</span>
          <ChevronRight size={12} />
        </Link>
        <button
          onClick={() => onRestart(node.id)}
          title="Restart Agent"
          className="flex size-7.5 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <RotateCw size={13} />
        </button>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
const PAGE_SIZE_OPTIONS = [6, 12, 24]

export default function DevicesPage() {
  const { clusters, loading, provisionNode } = useEdgeOps()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'online' | 'degraded' | 'offline'>('all')
  const [clusterFilter, setClusterFilter] = useState('all')
  const [actionNotice, setActionNotice] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(6)
  const [showAddModal, setShowAddModal] = useState(false)

  // Form state for provisioning
  const [newNode, setNewNode] = useState({ name: '', ip: '', clusterId: '', hardware: 'Jetson Orin Nano' })

  // Flat list of all nodes with cluster info
  const allNodes = useMemo(() => {
    return clusters.flatMap((c) =>
      c.nodes.map((n) => ({ node: n, clusterName: c.name, clusterId: c.id }))
    )
  }, [clusters])

  // KPI
  const totalNodes = allNodes.length
  const onlineNodes = allNodes.filter((r) => r.node.status === 'online').length
  const degradedNodes = allNodes.filter((r) => r.node.status === 'degraded').length
  const avgCpu = totalNodes > 0 ? Math.round(allNodes.reduce((s, r) => s + r.node.cpuUsage, 0) / totalNodes) : 0
  const avgGpu = totalNodes > 0 ? Math.round(allNodes.reduce((s, r) => s + r.node.gpuUsage, 0) / totalNodes) : 0

  // Filtered
  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return allNodes.filter((r) => {
      const n = r.node
      const matchSearch = !q ||
        n.name.toLowerCase().includes(q) ||
        n.id.toLowerCase().includes(q) ||
        n.ip.includes(q) ||
        n.hardware.toLowerCase().includes(q) ||
        r.clusterName.toLowerCase().includes(q)
      const matchStatus = statusFilter === 'all' || n.status === statusFilter
      const matchCluster = clusterFilter === 'all' || r.clusterId === clusterFilter
      return matchSearch && matchStatus && matchCluster
    })
  }, [allNodes, search, statusFilter, clusterFilter])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const paginated = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize)

  const resetPage = () => setCurrentPage(1)

  function notify(msg: string) {
    setActionNotice(msg)
    setTimeout(() => setActionNotice(null), 3000)
  }

  function handleRestart(nodeId: string) {
    notify(`Restarting agent on ${nodeId}…`)
  }

  function handleProvision(e: React.FormEvent) {
    e.preventDefault()
    if (!newNode.clusterId) return notify('Please select a cluster.')
    provisionNode(newNode.clusterId, {
      id: `node-${Date.now()}`,
      name: newNode.name,
      clusterId: newNode.clusterId,
      status: 'offline',
      ip: newNode.ip,
      hardware: newNode.hardware,
      agentVersion: 'v2.4.1',
      uptime: '0m',
      cpuUsage: 0,
      gpuUsage: 0,
      ramUsedGb: 0,
      ramTotalGb: 8,
      diskUsage: 0,
      tempC: 0,
      lastHeartbeat: new Date().toISOString(),
      cameras: [],
      modelRunning: 'none',
    })
    setShowAddModal(false)
    setNewNode({ name: '', ip: '', clusterId: '', hardware: 'Jetson Orin Nano' })
    notify(`Node "${newNode.name}" provisioned and pending online sync.`)
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <div className="flex items-center gap-2 text-sm">
          <div className="size-4 animate-spin rounded-full border-2 border-border border-t-brand" />
          Loading edge nodes…
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {/* ── Action Notice ── */}
      {actionNotice && (
        <div className="flex items-center justify-between rounded-lg border border-brand/30 bg-brand/10 px-4 py-2 text-xs font-semibold text-brand">
          <span>{actionNotice}</span>
          <button onClick={() => setActionNotice(null)} className="text-brand/60 hover:text-brand">✕</button>
        </div>
      )}

      {/* ── KPI Strip ── */}
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-5">
        <StatCard
          label="Total Nodes"
          value={totalNodes}
          icon={<Server size={15} />}
          variant="info"
        />
        <StatCard
          label="Healthy / Online"
          value={onlineNodes}
          icon={<CheckCircle2 size={15} />}
          variant="success"
        />
        <StatCard
          label="Degraded"
          value={degradedNodes}
          icon={<AlertTriangle size={15} />}
          variant="warning"
        />
        <StatCard
          label="Avg CPU"
          value={`${avgCpu}%`}
          icon={<Cpu size={15} />}
          variant="brand"
        />
        <StatCard
          label="Avg GPU"
          value={`${avgGpu}%`}
          icon={<Activity size={15} />}
          variant="purple"
        />
      </div>

      {/* ── Toolbar ── */}
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); resetPage() }}
              placeholder="Search node, IP, hardware…"
              className="h-8 w-48 rounded-lg border border-border bg-card pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground outline-none focus:border-brand"
            />
          </div>

          {/* Cluster filter */}
          <div className="relative">
            <select
              value={clusterFilter}
              onChange={(e) => { setClusterFilter(e.target.value); resetPage() }}
              className="h-8 appearance-none rounded-lg border border-border bg-card pl-3 pr-7 text-xs text-foreground outline-none"
            >
              <option value="all">All Clusters</option>
              {clusters.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <Filter size={11} className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
          </div>

          {/* Status filter */}
          <div className="flex items-center gap-0.5 rounded-lg border border-border bg-card p-0.5">
            {(['all', 'online', 'degraded', 'offline'] as const).map((s) => (
              <button
                key={s}
                onClick={() => { setStatusFilter(s); resetPage() }}
                className={`rounded px-2.5 py-0.5 text-[11px] font-semibold capitalize transition-all ${
                  statusFilter === s ? 'bg-foreground text-background' : 'text-muted-foreground hover:bg-muted/60'
                }`}
              >
                {s === 'all' ? 'All' : s === 'online' ? 'Healthy' : s}
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* ── Node Grid ── */}
      {filtered.length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/40 text-muted-foreground">
          <Server size={28} className="mb-2 opacity-40" />
          <p className="text-xs font-semibold text-foreground">No nodes match the filter</p>
          <p className="text-[11px]">Try adjusting the search or status filter.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 xl:grid-cols-3">
            {paginated.map(({ node, clusterName }) => (
              <NodeCard
                key={node.id}
                node={node}
                clusterName={clusterName}
                onRestart={handleRestart}
              />
            ))}
          </div>
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={filtered.length}
            pageSize={pageSize}
            pageSizeOptions={PAGE_SIZE_OPTIONS}
            onPageChange={setCurrentPage}
            onPageSizeChange={(s) => { setPageSize(s); setCurrentPage(1) }}
          />
        </>
      )}

      {/* ── Provision Node Modal ── */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowAddModal(false)}>
          <div
            className="w-full max-w-md rounded-2xl border border-border bg-card"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div className="flex items-center gap-2.5">
                <div className="flex size-8 items-center justify-center rounded-lg bg-brand/10"><Server size={15} className="text-brand" /></div>
                <div>
                  <div className="text-sm font-bold text-foreground">Provision Edge Node</div>
                  <div className="text-[10px] text-muted-foreground">Register a new node to a cluster</div>
                </div>
              </div>
              <button onClick={() => setShowAddModal(false)} className="text-muted-foreground hover:text-foreground">✕</button>
            </div>
            <form onSubmit={handleProvision} className="flex flex-col gap-4 p-5">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-muted-foreground tracking-wide">Cluster *</label>
                <select
                  required
                  value={newNode.clusterId}
                  onChange={(e) => setNewNode({ ...newNode, clusterId: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-brand"
                >
                  <option value="">Select cluster…</option>
                  {clusters.map((c) => <option key={c.id} value={c.id}>{c.name} — {c.site}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-muted-foreground tracking-wide">Node Name *</label>
                <input
                  required
                  type="text"
                  placeholder="e.g. HN-Node-04"
                  value={newNode.name}
                  onChange={(e) => setNewNode({ ...newNode, name: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-brand"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-muted-foreground tracking-wide">IP Address *</label>
                <input
                  required
                  type="text"
                  placeholder="e.g. 192.168.1.55"
                  value={newNode.ip}
                  onChange={(e) => setNewNode({ ...newNode, ip: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-brand"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-muted-foreground tracking-wide">Hardware Platform</label>
                <select
                  value={newNode.hardware}
                  onChange={(e) => setNewNode({ ...newNode, hardware: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-brand"
                >
                  <option>Jetson Orin Nano</option>
                  <option>Jetson AGX Orin</option>
                  <option>Intel NUC (OpenVINO)</option>
                  <option>Raspberry Pi 5 + Hailo</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-1 border-t border-border">
                <button type="button" onClick={() => setShowAddModal(false)} className="rounded-lg border border-border px-4 py-2 text-xs font-semibold text-muted-foreground hover:bg-accent">Cancel</button>
                <button type="submit" className="flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-xs font-semibold text-white hover:opacity-90">
                  <Plus size={12} />
                  Provision Node
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
