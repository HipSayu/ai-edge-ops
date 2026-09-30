import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  Network, CheckCircle, AlertTriangle, Camera,
  ChevronDown, ChevronRight, Server, Eye,
  LayoutGrid, Share2, Plus, Search,
} from 'lucide-react'
import type { Cluster, ClusterSummary } from '@/modules/cluster/types/cluster'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'
import ClusterTopologyGraph from '../components/ClusterTopologyGraph'
import CreateClusterModal from '../components/CreateClusterModal'
import ProvisionNodeModal from '@/modules/agent/components/ProvisionNodeModal'
import Pagination from '@/shared/components/Pagination'
import StatCard from '@/shared/components/StatCard'

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_CONFIG = {
  healthy:  { label: 'Healthy',  dot: 'bg-success',     text: 'text-success',     badge: 'bg-success/10 text-success' },
  degraded: { label: 'Degraded', dot: 'bg-warning',     text: 'text-warning',     badge: 'bg-warning/10 text-warning' },
  critical: { label: 'Critical', dot: 'bg-destructive', text: 'text-destructive', badge: 'bg-destructive/10 text-destructive' },
  offline:  { label: 'Offline',  dot: 'bg-muted-foreground', text: 'text-muted-foreground', badge: 'bg-muted text-muted-foreground' },
} as const

const NODE_STATUS_MAP = {
  online:   { dot: 'bg-success',  text: 'text-success' },
  degraded: { dot: 'bg-warning',  text: 'text-warning' },
  offline:  { dot: 'bg-muted-foreground', text: 'text-muted-foreground' },
} as const

function getNodeCfg(status: string) {
  return NODE_STATUS_MAP[status as keyof typeof NODE_STATUS_MAP] ?? NODE_STATUS_MAP.offline
}

function getClusterCfg(status: string) {
  return STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.offline
}

function MiniBar({ value }: { value: number }) {
  const color = value > 85 ? 'bg-destructive' : value > 70 ? 'bg-warning' : 'bg-info'
  return (
    <div className="h-1.5 w-full rounded-full bg-muted">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(100, value)}%` }} />
    </div>
  )
}

// ── Summary KPI bar (Compact) ───────────────────────────────────────────────────

function SummaryBar({ summary }: { summary: ClusterSummary }) {
  return (
    <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 xl:grid-cols-6">
      <StatCard
        label="Total Clusters"
        value={summary.totalClusters}
        icon={<Network size={15} />}
        variant="brand"
      />
      <StatCard
        label="Healthy"
        value={summary.healthyClusters}
        icon={<CheckCircle size={15} />}
        variant="success"
      />
      <StatCard
        label="Degraded"
        value={summary.degradedClusters}
        icon={<AlertTriangle size={15} />}
        variant="warning"
      />
      <StatCard
        label="Nodes Online"
        value={`${summary.onlineNodes}/${summary.totalNodes}`}
        icon={<Server size={15} />}
        variant="info"
      />
      <StatCard
        label="Cameras Online"
        value={`${summary.onlineCameras}/${summary.totalCameras}`}
        icon={<Camera size={15} />}
        variant="purple"
      />
      <StatCard
        label="Active Alerts"
        value={summary.totalAlerts}
        icon={<AlertTriangle size={15} />}
        variant={summary.totalAlerts > 0 ? 'destructive' : 'info'}
      />
    </div>
  )
}

// ── Main Clusters Page Component ──────────────────────────────────────────────

const PAGE_SIZE_OPTIONS = [6, 12, 24]

export default function ClustersPage() {
  const { clusters, summary, loading, createCluster, provisionNode } = useEdgeOps()

  const [expandedCluster, setExpandedCluster] = useState<string | null>(null)
  const [expandedNode, setExpandedNode] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'cards' | 'graph'>('cards')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(6)

  // Modals
  const [showCreateClusterModal, setShowCreateClusterModal] = useState(false)
  const [showProvisionNodeModal, setShowProvisionNodeModal] = useState(false)
  const [targetClusterForNode, setTargetClusterForNode] = useState<string | undefined>(undefined)

  const handleOpenAddNode = (clusterId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    setTargetClusterForNode(clusterId)
    setShowProvisionNodeModal(true)
  }

  // Filtered clusters
  const filteredClusters = useMemo(() => {
    const q = search.toLowerCase()
    return clusters.filter((c) => {
      const matchSearch =
        !q ||
        c.name.toLowerCase().includes(q) ||
        c.site.toLowerCase().includes(q) ||
        c.description.toLowerCase().includes(q) ||
        c.nodes.some((n) => n.name.toLowerCase().includes(q) || n.ip.includes(q))
      const matchStatus = statusFilter === 'all' || c.status === statusFilter
      return matchSearch && matchStatus
    })
  }, [clusters, search, statusFilter])

  const totalPages = Math.max(1, Math.ceil(filteredClusters.length / pageSize))
  const paginatedClusters = filteredClusters.slice((currentPage - 1) * pageSize, currentPage * pageSize)

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <div className="flex items-center gap-2 text-sm">
          <div className="size-4 animate-spin rounded-full border-2 border-border border-t-brand" />
          Loading edge clusters…
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {/* ── Top Modals ── */}
      <CreateClusterModal
        isOpen={showCreateClusterModal}
        onClose={() => setShowCreateClusterModal(false)}
        onCreateCluster={createCluster}
      />

      <ProvisionNodeModal
        isOpen={showProvisionNodeModal}
        onClose={() => setShowProvisionNodeModal(false)}
        clusters={clusters}
        defaultClusterId={targetClusterForNode}
        onProvision={(node) => provisionNode(node.clusterId as string, node as import('@/modules/cluster/types/cluster').NodeAgent)}
      />

      {/* ── 1. KPI SUMMARY STRIP ── */}
      {summary && <SummaryBar summary={summary} />}

      {/* ── 2. TOOLBAR: Switch View Mode + Search + Add Cluster Action ── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {/* View mode toggle */}
          <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-0.5">
            <button
              onClick={() => setViewMode('cards')}
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
                viewMode === 'cards'
                  ? 'bg-foreground text-background'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <LayoutGrid size={13} />
              <span>Card Grid</span>
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
                viewMode === 'graph'
                  ? 'bg-foreground text-background'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Share2 size={13} />
              <span>Canvas Topology Graph</span>
            </button>
          </div>

          {/* Search box if cards view */}
          {viewMode === 'cards' && (
            <>
              <div className="relative flex items-center">
                <Search size={13} className="absolute left-2.5 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search cluster, site, node..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setCurrentPage(1)
                  }}
                  className="h-8 w-44 rounded-lg border border-border bg-card pl-8 pr-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:w-56 focus:border-brand transition-all outline-none"
                />
              </div>

              <div className="flex items-center gap-0.5 rounded-lg border border-border bg-card p-0.5">
                {(['all', 'healthy', 'degraded', 'offline'] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => {
                      setStatusFilter(s)
                      setCurrentPage(1)
                    }}
                    className={`rounded px-2 py-0.5 text-[11px] font-semibold capitalize transition-colors ${
                      statusFilter === s ? 'bg-foreground text-background' : 'text-muted-foreground hover:bg-muted/60'
                    }`}
                  >
                    {s === 'all' ? 'All' : s}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Action Button: Add Cluster */}
        <button
          onClick={() => setShowCreateClusterModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-xs font-semibold text-white transition-opacity hover:opacity-90"
        >
          <Plus size={13} />
          <span>Add Cluster</span>
        </button>
      </div>

      {/* ── 3. VIEW MODE SWITCHING (Cards or Topology Graph) ── */}
      {viewMode === 'graph' ? (
        <section className="flex flex-col gap-3">
          <ClusterTopologyGraph clusters={clusters} />
        </section>
      ) : (
        /* ── CARDS GRID VIEW ── */
        <>
          {paginatedClusters.length === 0 ? (
            <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-border bg-card/40 text-xs text-muted-foreground">
              No clusters found matching your filter.
            </div>
          ) : (
            <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-2 xl:grid-cols-3">
              {paginatedClusters.map((c: Cluster) => {
                const isExpanded = expandedCluster === c.id
                const cfg = getClusterCfg(c.status)

                return (
                  <div
                    key={c.id}
                    className="flex flex-col rounded-xl border border-border bg-card transition-all hover:border-border/80"
                  >
                    {/* Cluster Card Header */}
                    <div
                      className="flex cursor-pointer items-start justify-between p-4"
                      onClick={() => setExpandedCluster(isExpanded ? null : c.id)}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand">
                          <Network size={18} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-foreground">{c.name}</span>
                            <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${cfg.badge}`}>
                              {cfg.label}
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">{c.site}</div>
                          <p className="mt-1 text-xs text-muted-foreground/80">{c.description}</p>
                        </div>
                      </div>
                      <button className="text-muted-foreground hover:text-foreground">
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </button>
                    </div>

                    {/* Cluster Quick Telemetry Metrics */}
                    <div className="grid grid-cols-3 gap-2 border-y border-border/60 bg-muted/10 px-4 py-2.5 text-xs">
                      <div>
                        <span className="text-muted-foreground text-[11px]">Nodes:</span>{' '}
                        <span className="font-semibold text-foreground font-mono">{c.onlineNodes}/{c.totalNodes}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground text-[11px]">Cameras:</span>{' '}
                        <span className="font-semibold text-foreground font-mono">{c.onlineCameras}/{c.totalCameras}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground text-[11px]">Agg FPS:</span>{' '}
                        <span className="font-semibold text-foreground font-mono">{c.aggregateFps}</span>
                      </div>
                    </div>

                    {/* Expandable Node List */}
                    {isExpanded && (
                      <div className="flex flex-col divide-y divide-border/60 p-3 space-y-2">
                        <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground px-1">
                          <span>Assigned Edge Nodes ({c.nodes.length})</span>
                          <button
                            onClick={(e) => handleOpenAddNode(c.id, e)}
                            className="flex items-center gap-1 text-[11px] font-semibold text-brand hover:underline"
                          >
                            <Plus size={12} />
                            <span>Add Node</span>
                          </button>
                        </div>

                        {c.nodes.length === 0 ? (
                          <div className="p-4 text-center text-xs text-muted-foreground">
                            No nodes registered. Click "Add Node" above to provision one.
                          </div>
                        ) : (
                          c.nodes.map((node) => {
                            const isNodeExpanded = expandedNode === node.id
                            const nCfg = getNodeCfg(node.status)

                            return (
                              <div key={node.id} className="pt-2">
                                <div
                                  className="flex cursor-pointer items-center justify-between rounded-lg p-2 hover:bg-muted/20"
                                  onClick={() => setExpandedNode(isNodeExpanded ? null : node.id)}
                                >
                                  <div className="flex items-center gap-2">
                                    <span className={`size-2 rounded-full ${nCfg.dot}`} />
                                    <div>
                                      <div className="text-xs font-bold text-foreground">{node.name}</div>
                                      <div className="text-[10px] text-muted-foreground font-mono">{node.ip} · {node.hardware}</div>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <div className="text-right text-[11px] font-mono">
                                      <span className="text-muted-foreground">CPU:</span> {node.cpuUsage}%
                                    </div>
                                    <Link
                                      to={`/agent/nodes/${node.id}`}
                                      onClick={(e) => e.stopPropagation()}
                                      className="rounded p-1 text-brand hover:bg-brand/10"
                                      title="View Node Detail"
                                    >
                                      <Eye size={14} />
                                    </Link>
                                  </div>
                                </div>

                                {/* Node Metrics mini bar */}
                                <div className="px-2 pb-2">
                                  <div className="grid grid-cols-2 gap-2 text-[10px] text-muted-foreground mb-1">
                                    <span>CPU Load ({node.cpuUsage}%)</span>
                                    <span>GPU Load ({node.gpuUsage}%)</span>
                                  </div>
                                  <div className="grid grid-cols-2 gap-2">
                                    <MiniBar value={node.cpuUsage} />
                                    <MiniBar value={node.gpuUsage} />
                                  </div>
                                </div>
                              </div>
                            )
                          })
                        )}
                      </div>
                    )}

                    {/* Footer Link */}
                    <div className="flex items-center justify-between border-t border-border/60 p-3 text-xs">
                      <span className="text-[11px] text-muted-foreground">Gateway gRPC Sync</span>
                      <Link
                        to={`/agent/clusters/${c.id}`}
                        className="font-semibold text-brand hover:underline"
                      >
                        View Cluster Details →
                      </Link>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Pagination */}
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={filteredClusters.length}
            pageSize={pageSize}
            pageSizeOptions={PAGE_SIZE_OPTIONS}
            onPageChange={setCurrentPage}
            onPageSizeChange={(s) => {
              setPageSize(s)
              setCurrentPage(1)
            }}
          />
        </>
      )}
    </div>
  )
}
