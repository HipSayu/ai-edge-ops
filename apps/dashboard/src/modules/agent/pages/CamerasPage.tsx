import { useState, useEffect, useMemo } from 'react'
import {
  Camera, Radio, WifiOff, Search, Grid2X2, Grid3X3, LayoutGrid,
  List, AlertTriangle, Server, X, Tv, Eye, Maximize2,
  Activity, Clock, ShieldAlert, Cpu, Video, CheckCircle2,
  RefreshCw, Volume2, VolumeX,
} from 'lucide-react'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'
import AddCameraModal from '../components/AddCameraModal'
import Pagination from '@/shared/components/Pagination'
import StatCard from '@/shared/components/StatCard'

interface ExtendedCamera {
  id: string
  name: string
  zone: string
  nodeId: string
  nodeName: string
  clusterId: string
  clusterName: string
  online: boolean
  fps: number
  resolution: string
  alertCount: number
  model: string
  streamUrl?: string
}

type ViewMode = 'cards' | 'grid4' | 'grid9' | 'table'
type TvWallLayout = '1x1' | '2x2' | '3x3' | '4x4' | 'auto'

const PAGE_SIZE_OPTIONS = [12, 24, 48]

export default function CamerasPage() {
  const { clusters, loading, addCameraToNode, events } = useEdgeOps()

  // Filters
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'online' | 'offline' | 'alerts'>('all')
  const [selectedCluster, setSelectedCluster] = useState<string>('all')
  const [selectedNode, setSelectedNode] = useState<string>('all')
  const [viewMode, setViewMode] = useState<ViewMode>('cards')
  const [showEventLog, setShowEventLog] = useState(true)

  // Events & audio
  const [audioMuted, setAudioMuted] = useState(true)

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(12)

  // TV Wall (fullscreen native)
  const [isTvWallMode, setIsTvWallMode] = useState(false)
  const [tvLayout, setTvLayout] = useState<TvWallLayout>('2x2')
  const [tvSelectedCamera, setTvSelectedCamera] = useState<ExtendedCamera | null>(null)
  const [tvPreSelectLayout, setTvPreSelectLayout] = useState<TvWallLayout>('2x2')

  // Modals & Player
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedPlayerCamera, setSelectedPlayerCamera] = useState<ExtendedCamera | null>(null)
  const [actionNotice, setActionNotice] = useState<string | null>(null)

  // Native Fullscreen enter/exit helpers
  const enterFullScreen = async (layout: TvWallLayout) => {
    setTvLayout(layout)
    setTvSelectedCamera(null)
    setIsTvWallMode(true)
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen?.()
      }
    } catch {
      // Ignore
    }
  }

  const exitFullScreen = async () => {
    setIsTvWallMode(false)
    setTvSelectedCamera(null)
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen?.()
      }
    } catch {
      // Ignore
    }
  }

  // Listen for ESC key and fullscreen change
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.code === 'Escape') {
        if (isTvWallMode) {
          exitFullScreen()
        }
      }
    }

    const handleFsChange = () => {
      if (!document.fullscreenElement && isTvWallMode) {
        setIsTvWallMode(false)
        setTvSelectedCamera(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    document.addEventListener('fullscreenchange', handleFsChange)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('fullscreenchange', handleFsChange)
    }
  }, [isTvWallMode])

  // Derive flat camera list from clusters state
  const cameras = useMemo(() => {
    const allCams: ExtendedCamera[] = []
    clusters.forEach((c) => {
      c.nodes.forEach((n) => {
        n.cameras.forEach((cam) => {
          allCams.push({
            id: cam.id,
            name: cam.name,
            zone: cam.zone,
            nodeId: n.id,
            nodeName: n.name,
            clusterId: c.id,
            clusterName: c.name,
            online: cam.online,
            fps: cam.fps,
            resolution: cam.resolution,
            alertCount: cam.alertCount,
            model: cam.model || 'yolov8n',
            streamUrl: cam.streamUrl || `rtsp://${n.ip}:8554/live/${cam.id}`,
          })
        })
      })
    })
    return allCams
  }, [clusters])

  const handleAddCamera = (camData: Record<string, unknown>) => {
    const targetNodeId = (camData.nodeId as string) || (camData.deviceId as string) || clusters[0]?.nodes[0]?.id
    if (!targetNodeId) return
    addCameraToNode(targetNodeId, {
      id: camData.id as string,
      name: camData.name as string,
      zone: camData.zone as string,
      online: true,
      fps: Number(camData.fps) || 30,
      resolution: (camData.resolution as string) || '1920x1080',
      alertCount: 0,
      model: (camData.model as string) || 'yolov8n',
      streamUrl: camData.streamUrl as string,
    })
    setActionNotice(`Camera ${camData.name} connected successfully`)
    setTimeout(() => setActionNotice(null), 3500)
  }

  // Filter logic
  const filtered = useMemo(() => {
    return cameras.filter((cam) => {
      const matchSearch =
        !search ||
        cam.name.toLowerCase().includes(search.toLowerCase()) ||
        cam.id.toLowerCase().includes(search.toLowerCase()) ||
        cam.zone.toLowerCase().includes(search.toLowerCase()) ||
        cam.nodeName.toLowerCase().includes(search.toLowerCase()) ||
        cam.model.toLowerCase().includes(search.toLowerCase())
      const matchStatus =
        statusFilter === 'all' ||
        (statusFilter === 'online' && cam.online) ||
        (statusFilter === 'offline' && !cam.online) ||
        (statusFilter === 'alerts' && cam.alertCount > 0)
      const matchCluster = selectedCluster === 'all' || cam.clusterId === selectedCluster
      const matchNode = selectedNode === 'all' || cam.nodeId === selectedNode
      return matchSearch && matchStatus && matchCluster && matchNode
    })
  }, [cameras, search, statusFilter, selectedCluster, selectedNode])

  // Paginated
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const paginated = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize)

  // Stats
  const totalCams = cameras.length
  const onlineCams = cameras.filter((c) => c.online).length
  const offlineCams = totalCams - onlineCams
  const totalAlerts = cameras.reduce((s, c) => s + c.alertCount, 0)
  const avgFps = onlineCams > 0 ? Math.round(cameras.filter((c) => c.online).reduce((s, c) => s + c.fps, 0) / onlineCams) : 0
  const unsafeCount = events.filter((e) => e.status === 'UNSAFE').length

  const resetPage = () => setCurrentPage(1)

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <div className="flex items-center gap-2 text-sm">
          <RefreshCw className="size-4 animate-spin text-brand" />
          <span>Loading camera stream telemetry…</span>
        </div>
      </div>
    )
  }

  // ─────────────────────────────────────────────────────────────
  // ── FULLSCREEN TV WALL
  // ─────────────────────────────────────────────────────────────
  if (isTvWallMode) {
    const displayStreams = tvSelectedCamera
      ? [tvSelectedCamera]
      : tvLayout === '1x1'
      ? filtered.slice(0, 1)
      : tvLayout === '2x2'
      ? filtered.slice(0, 4)
      : tvLayout === '3x3'
      ? filtered.slice(0, 9)
      : tvLayout === '4x4'
      ? filtered.slice(0, 16)
      : filtered

    const gridClass =
      tvSelectedCamera || tvLayout === '1x1'
        ? 'grid-cols-1 grid-rows-1'
        : tvLayout === '2x2'
        ? 'grid-cols-2 grid-rows-2'
        : tvLayout === '3x3'
        ? 'grid-cols-3 grid-rows-3'
        : tvLayout === '4x4'
        ? 'grid-cols-4 grid-rows-4'
        : 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4'

    return (
      <div className="fixed inset-0 z-99999 h-screen w-screen overflow-hidden bg-black select-none flex flex-col font-mono">
        {/* Top Floating HUD bar */}
        <div className="absolute top-2 left-4 right-4 z-50 flex items-center justify-between pointer-events-none">
          <div className="flex items-center gap-3 rounded-lg bg-black/75 px-3 py-1.5 backdrop-blur-md border border-white/10 pointer-events-auto">
            <span className="size-2 rounded-full bg-success animate-pulse" />
            <span className="text-xs font-bold text-white tracking-wider">TV wall monitor</span>
            <span className="text-[11px] text-zinc-400">Layout: {tvLayout.toUpperCase()}</span>
            <span className="text-[11px] text-emerald-400 font-bold">{displayStreams.length} FEEDS ACTIVE</span>
          </div>

          <div className="flex items-center gap-2 rounded-lg bg-black/75 px-2 py-1 backdrop-blur-md border border-white/10 pointer-events-auto">
            <button
              onClick={() => setAudioMuted(!audioMuted)}
              className="rounded p-1.5 text-zinc-300 hover:text-white hover:bg-white/10 transition-colors"
              title={audioMuted ? 'Unmute Audio' : 'Mute Audio'}
            >
              {audioMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
            </button>
            <button
              onClick={exitFullScreen}
              className="flex items-center gap-1 rounded bg-white/15 px-2.5 py-1 text-xs font-bold text-white hover:bg-white/25 transition-colors"
            >
              <X size={13} />
              <span>ESC</span>
            </button>
          </div>
        </div>

        {/* Video Matrix */}
        <div className={`grid h-full w-full gap-1.5 bg-black p-1.5 ${gridClass}`}>
          {displayStreams.map((cam) => (
            <div
              key={cam.id}
              onClick={() => {
                if (tvSelectedCamera) setTvSelectedCamera(null)
                else setTvSelectedCamera(cam)
              }}
              className={`group relative overflow-hidden rounded-lg bg-zinc-950 cursor-pointer border border-zinc-800 hover:border-brand/70 transition-all ${
                tvLayout === 'auto' ? 'min-h-[220px]' : 'h-full w-full'
              }`}
            >
              {/* Synthetic Camera Simulation */}
              <div
                className="absolute inset-0 transition-transform duration-500 group-hover:scale-102"
                style={{
                  background: `radial-gradient(ellipse at ${30 + (cam.fps % 5) * 8}% ${25 + (cam.fps % 4) * 10}%, hsl(${cam.fps * 9}, 45%, 15%) 0%, #030508 100%)`,
                }}
              />

              {/* Grid scanning lines effect */}
              <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

              {/* Bounding box simulation */}
              <div
                className="absolute rounded border-2 border-emerald-400 bg-emerald-500/10 pointer-events-none transition-all duration-700"
                style={{
                  top: `${20 + (cam.fps % 4) * 8}%`,
                  left: `${25 + (cam.fps % 5) * 8}%`,
                  width: '32%',
                  height: '42%',
                }}
              >
                <span className="absolute -top-5 left-0 rounded bg-emerald-500 px-1.5 py-0.5 font-mono text-[9px] font-bold text-black">
                  {cam.model.split('-')[0]} 96.4%
                </span>
              </div>

              {cam.alertCount > 0 && (
                <div className="absolute right-4 top-12 rounded border border-red-500 bg-red-500/20 px-2 py-1 pointer-events-none backdrop-blur-xs animate-pulse">
                  <span className="font-mono text-[10px] font-bold text-red-400">Alert detected</span>
                </div>
              )}

              {/* Bottom HUD info bar */}
              <div className="absolute inset-x-0 bottom-0 p-2.5 bg-gradient-to-t from-black/90 via-black/40 to-transparent flex items-end justify-between pointer-events-none">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="font-bold text-xs text-white">{cam.name}</span>
                    <span className="text-[10px] text-zinc-400">{cam.zone}</span>
                  </div>
                  <div className="text-[10px] text-zinc-400 font-mono mt-0.5">
                    {cam.nodeName} · {cam.resolution}
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  <span className="rounded bg-black/60 px-1.5 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/30">
                    {cam.fps} FPS
                  </span>
                  <span className="text-[9px] text-zinc-400 mt-0.5">H.265 RTSP</span>
                </div>
              </div>
            </div>
          ))}

          {displayStreams.length === 0 && (
            <div className="flex h-full w-full col-span-full items-center justify-center text-zinc-600 font-mono text-sm">
              No active camera streams available
            </div>
          )}
        </div>
      </div>
    )
  }

  // ─────────────────────────────────────────────────────────────
  // ── STANDARD DASHBOARD VIEW
  // ─────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col gap-4">
      {/* Modal Add Camera */}
      <AddCameraModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        clusters={clusters}
        onAddCamera={handleAddCamera}
      />

      {/* Action Notice */}
      {actionNotice && (
        <div className="flex items-center justify-between rounded-xl border border-success/30 bg-success/10 px-4 py-2.5 text-xs font-semibold text-success animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={15} />
            <span>{actionNotice}</span>
          </div>
          <button onClick={() => setActionNotice(null)} className="text-success/70 hover:text-success cursor-pointer">
            <X size={14} />
          </button>
        </div>
      )}

      {/* ── 1. KPI Stats Summary ── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          label="Camera Streams"
          value={onlineCams}
          sub={`${onlineCams}/${totalCams} online`}
          icon={<Video size={16} />}
          variant="purple"
        />
        <StatCard
          label="Avg Ingestion FPS"
          value={`${avgFps} FPS`}
          sub="Aggregate Ingest Speed"
          icon={<Radio size={16} />}
          variant="success"
        />
        <StatCard
          label="Active Alerts"
          value={totalAlerts}
          sub={`${unsafeCount} unsafe violations`}
          icon={<ShieldAlert size={16} />}
          variant={totalAlerts > 0 ? 'destructive' : 'info'}
        />
        <StatCard
          label="Edge Pipeline Nodes"
          value={`${clusters.reduce((s, c) => s + c.totalNodes, 0)} Nodes`}
          sub="Active Inference Targets"
          icon={<Cpu size={16} />}
          variant="info"
        />
      </div>

      {/* ── 2. Filters & Actions Bar ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-3">
        {/* Left: Search + Cluster & Node Filter */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative flex items-center">
            <Search size={13} className="absolute left-2.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search camera, zone, model..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); resetPage() }}
              className="h-8 w-44 rounded-lg border border-border bg-muted/40 pl-8 pr-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:w-56 focus:border-brand transition-all outline-none"
            />
          </div>

          {/* Cluster filter */}
          <select
            value={selectedCluster}
            onChange={(e) => { setSelectedCluster(e.target.value); setSelectedNode('all'); resetPage() }}
            className="h-8 rounded-lg border border-border bg-muted/40 px-2.5 text-xs font-semibold text-foreground outline-none focus:border-brand"
          >
            <option value="all">All Clusters</option>
            {clusters.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.site})</option>)}
          </select>

          {/* Node filter */}
          <select
            value={selectedNode}
            onChange={(e) => { setSelectedNode(e.target.value); resetPage() }}
            className="h-8 rounded-lg border border-border bg-muted/40 px-2.5 text-xs font-semibold text-foreground outline-none focus:border-brand"
          >
            <option value="all">All Nodes</option>
            {clusters
              .filter((c) => selectedCluster === 'all' || c.id === selectedCluster)
              .flatMap((c) => c.nodes)
              .map((n) => <option key={n.id} value={n.id}>{n.name} ({n.ip})</option>)}
          </select>

          {/* Status chips */}
          <div className="flex items-center gap-1 rounded-lg border border-border bg-muted/20 p-1">
            {(['all', 'online', 'offline', 'alerts'] as const).map((s) => (
              <button
                key={s}
                onClick={() => { setStatusFilter(s); resetPage() }}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-colors cursor-pointer ${
                  statusFilter === s
                    ? 'bg-foreground text-background'
                    : 'text-muted-foreground hover:bg-muted/60'
                }`}
              >
                {s === 'all' ? `All (${totalCams})` : s === 'online' ? `Live (${onlineCams})` : s === 'offline' ? `Offline (${offlineCams})` : `Alerts (${totalAlerts})`}
              </button>
            ))}
          </div>
        </div>

        {/* Right: TV Wall + View Mode + Add Button */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Toggle Detection Log Sidebar */}
          <button
            onClick={() => setShowEventLog((v) => !v)}
            className={`flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-xs font-semibold transition-colors cursor-pointer ${
              showEventLog
                ? 'border-brand/40 bg-brand/10 text-brand'
                : 'border-border bg-muted/30 text-muted-foreground hover:text-foreground'
            }`}
          >
            <Activity size={13} />
            <span>AI Events Log</span>
            {unsafeCount > 0 && (
              <span className="size-2 rounded-full bg-destructive animate-pulse" />
            )}
          </button>

          {/* Fullscreen TV Wall Selector */}
          <div className="flex items-center gap-1 rounded-lg border border-purple-500/30 bg-purple-500/10 p-1">
            {(['1x1', '2x2', '3x3', '4x4', 'auto'] as const).map((l) => (
              <button
                key={l}
                onClick={() => setTvPreSelectLayout(l)}
                className={`rounded px-1.5 py-0.5 text-[10px] font-mono font-bold transition-all cursor-pointer ${
                  tvPreSelectLayout === l
                    ? 'bg-purple-500 text-white'
                    : 'text-purple-400 hover:bg-purple-500/20'
                }`}
              >
                {l}
              </button>
            ))}
            <button
              onClick={() => enterFullScreen(tvPreSelectLayout)}
              className="flex items-center gap-1 rounded-md bg-purple-500 px-2.5 py-1 text-xs font-bold text-white hover:bg-purple-600 transition-colors cursor-pointer"
            >
              <Tv size={12} />
              <span>TV Wall</span>
            </button>
          </div>

          {/* View mode toggle */}
          <div className="flex items-center gap-0.5 rounded-lg border border-border bg-muted/20 p-1">
            <button onClick={() => setViewMode('cards')} title="Detail Cards" className={`rounded p-1 transition-colors cursor-pointer ${viewMode === 'cards' ? 'bg-foreground text-background' : 'text-muted-foreground hover:text-foreground'}`}><LayoutGrid size={14} /></button>
            <button onClick={() => setViewMode('grid4')} title="2x2 Grid" className={`rounded p-1 transition-colors cursor-pointer ${viewMode === 'grid4' ? 'bg-foreground text-background' : 'text-muted-foreground hover:text-foreground'}`}><Grid2X2 size={14} /></button>
            <button onClick={() => setViewMode('grid9')} title="3x3 Grid" className={`rounded p-1 transition-colors cursor-pointer ${viewMode === 'grid9' ? 'bg-foreground text-background' : 'text-muted-foreground hover:text-foreground'}`}><Grid3X3 size={14} /></button>
            <button onClick={() => setViewMode('table')} title="List View" className={`rounded p-1 transition-colors cursor-pointer ${viewMode === 'table' ? 'bg-foreground text-background' : 'text-muted-foreground hover:text-foreground'}`}><List size={14} /></button>
          </div>

        </div>
      </div>

      {/* ── 3. Main Workspace: Video Grid + Events Log ── */}
      <div className="flex min-h-0 gap-4">
        {/* Left: Cameras Container */}
        <div className="flex-1 min-w-0 flex flex-col gap-4">
          {filtered.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card/50 text-center text-muted-foreground p-6">
              <WifiOff size={32} className="mb-2 text-muted-foreground/50" />
              <p className="text-sm font-bold text-foreground">No matching cameras found</p>
              <p className="text-xs mt-1">Please adjust your search criteria or connect a new camera stream.</p>
            </div>
          ) : viewMode === 'cards' ? (
            <>
              {/* Detailed Cards View */}
              <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3">
                {paginated.map((cam) => (
                  <div
                    key={cam.id}
                    className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition-all hover:border-brand/40"
                  >
                    {/* Video Viewport */}
                    <div
                      className="relative aspect-video w-full overflow-hidden bg-zinc-950 cursor-pointer select-none"
                      onClick={() => setSelectedPlayerCamera(cam)}
                    >
                      <div
                        className="absolute inset-0 transition-transform duration-500 group-hover:scale-103"
                        style={{
                          background: `radial-gradient(ellipse at ${30 + (cam.fps % 5) * 8}% 30%, hsl(${cam.fps * 9}, 45%, 15%) 0%, #060910 100%)`,
                        }}
                      />

                      {/* Scanlines overlay */}
                      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

                      {/* Top Badges */}
                      <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                        <span className={`size-2 rounded-full ${cam.online ? 'bg-success animate-pulse' : 'bg-destructive'}`} />
                        <span className="rounded bg-black/60 px-1.5 py-0.5 font-mono text-[9.5px] font-bold text-white/90 backdrop-blur-xs">
                          {cam.online ? `${cam.fps} FPS` : 'OFFLINE'}
                        </span>
                      </div>

                      {cam.alertCount > 0 && (
                        <span className="absolute top-2.5 right-2.5 flex items-center gap-1 rounded bg-destructive/90 px-1.5 py-0.5 text-[9.5px] font-bold text-white backdrop-blur-xs">
                          <AlertTriangle size={10} />
                          {cam.alertCount} ALERTS
                        </span>
                      )}

                      {/* Center Play Overlay */}
                      <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100 backdrop-blur-2xs">
                        <div className="flex items-center gap-1.5 rounded-full bg-brand px-3 py-1.5 text-xs font-semibold text-white">
                          <Eye size={13} />
                          <span>View Stream</span>
                        </div>
                      </div>

                      {/* Bottom stream tag */}
                      <div className="absolute bottom-2 left-2.5 right-2.5 flex items-center justify-between text-[9.5px] font-mono text-white/70 pointer-events-none">
                        <span>{cam.resolution}</span>
                        <span className="text-emerald-400 font-bold">{cam.model.split('-')[0]}</span>
                      </div>
                    </div>

                    {/* Metadata Card Footer */}
                    <div className="flex flex-col p-3.5 gap-2.5">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <h3 className="text-xs font-bold text-foreground truncate">{cam.name}</h3>
                          <p className="text-[11px] text-muted-foreground truncate">{cam.zone} · {cam.clusterName}</p>
                        </div>
                        <span className="shrink-0 rounded-md bg-muted/50 px-2 py-0.5 text-[10px] font-mono text-muted-foreground">
                          {cam.nodeName}
                        </span>
                      </div>

                      <div className="flex items-center justify-between border-t border-border/60 pt-2 text-[11px] font-mono text-muted-foreground">
                        <span className="text-brand font-semibold">{cam.model}</span>
                        <span>RTSP / TCP</span>
                      </div>
                    </div>
                  </div>
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
          ) : viewMode === 'grid4' || viewMode === 'grid9' ? (
            <>
              {/* Matrix Live Feed View (2x2 or 3x3) */}
              <div className={`grid gap-2.5 ${viewMode === 'grid4' ? 'grid-cols-2' : 'grid-cols-3'}`}>
                {paginated.slice(0, viewMode === 'grid4' ? 4 : 9).map((cam) => (
                  <div
                    key={cam.id}
                    onClick={() => setSelectedPlayerCamera(cam)}
                    className="group relative aspect-video overflow-hidden rounded-xl border border-border bg-zinc-950 cursor-pointer min-h-[180px] hover:border-brand/50 transition-all"
                  >
                    <div
                      className="absolute inset-0"
                      style={{ background: `radial-gradient(ellipse at center, hsl(${cam.fps * 9}, 45%, 15%) 0%, #05080e 100%)` }}
                    />
                    <div className="absolute inset-x-0 top-0 flex items-center justify-between p-2.5 bg-gradient-to-b from-black/80 via-black/40 to-transparent">
                      <div className="flex items-center gap-1.5">
                        <span className="size-2 rounded-full bg-success animate-pulse" />
                        <span className="text-xs font-bold text-white">{cam.name}</span>
                      </div>
                      <span className="font-mono text-[10.5px] font-bold text-emerald-400 bg-black/60 px-1.5 py-0.5 rounded">
                        {cam.fps} FPS
                      </span>
                    </div>

                    <div className="absolute inset-x-0 bottom-0 flex items-center justify-between p-2.5 bg-gradient-to-t from-black/80 via-black/40 to-transparent text-[10px] font-mono text-zinc-300">
                      <span>{cam.zone}</span>
                      <span className="text-brand font-bold">{cam.model.split('-')[0]}</span>
                    </div>
                  </div>
                ))}
              </div>

              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalItems={filtered.length}
                pageSize={viewMode === 'grid4' ? 4 : 9}
                onPageChange={setCurrentPage}
              />
            </>
          ) : (
            /* Table Ingestion View */
            <>
              <div className="overflow-hidden rounded-xl border border-border bg-card">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-border bg-muted/30 text-[11px] font-semibold text-muted-foreground tracking-wider">
                    <tr>
                      <th className="px-4 py-3">Camera / Name / Zone</th>
                      <th className="px-4 py-3">Cluster &amp; Node</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">FPS</th>
                      <th className="px-4 py-3">Resolution</th>
                      <th className="px-4 py-3">Vision AI Model</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {paginated.map((cam) => (
                      <tr key={cam.id} className="hover:bg-muted/20 transition-colors">
                        <td className="px-4 py-3 font-medium text-foreground">
                          <div className="font-bold">{cam.name}</div>
                          <div className="text-[11px] text-muted-foreground">{cam.zone}</div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">
                          <span className="font-semibold text-foreground">{cam.clusterName}</span> / {cam.nodeName}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-bold ${cam.online ? 'bg-success/10 text-success' : 'bg-destructive/10 text-destructive'}`}>
                            <span className={`size-1.5 rounded-full ${cam.online ? 'bg-success animate-pulse' : 'bg-destructive'}`} />
                            {cam.online ? 'Live Streaming' : 'Offline'}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono font-bold text-foreground">{cam.fps}</td>
                        <td className="px-4 py-3 font-mono text-muted-foreground">{cam.resolution}</td>
                        <td className="px-4 py-3 font-mono text-brand font-semibold">{cam.model}</td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => setSelectedPlayerCamera(cam)}
                            className="rounded-lg border border-border px-2.5 py-1 text-xs font-semibold text-foreground hover:bg-muted hover:border-brand/40 transition-colors cursor-pointer"
                          >
                            View Stream
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
        </div>

        {/* Right: Live Detection Events Sidebar */}
        {showEventLog && (
          <aside className="flex w-[300px] shrink-0 flex-col rounded-2xl border border-border bg-card overflow-hidden">
            <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-muted/15">
              <div className="flex items-center gap-2 text-xs font-bold text-foreground">
                <Activity size={14} className="text-brand" />
                <span>Detection Events</span>
              </div>
              <span className="rounded-full bg-destructive/10 px-2 py-0.5 text-[10px] font-bold text-destructive">
                {unsafeCount} UNSAFE
              </span>
            </div>

            {/* Event Stats Summary */}
            <div className="grid grid-cols-3 border-b border-border bg-muted/10 text-center py-2 text-xs">
              <div className="border-r border-border/60">
                <div className="text-[10px] text-muted-foreground font-semibold">Total</div>
                <div className="text-xs font-bold text-foreground font-mono">{events.length}</div>
              </div>
              <div className="border-r border-border/60">
                <div className="text-[10px] text-destructive font-semibold">Unsafe</div>
                <div className="text-xs font-bold text-destructive font-mono">{unsafeCount}</div>
              </div>
              <div>
                <div className="text-[10px] text-warning font-semibold">Warn</div>
                <div className="text-xs font-bold text-warning font-mono">{events.filter(e => e.status === 'WARNING').length}</div>
              </div>
            </div>

            {/* Event Stream List */}
            <div className="flex-1 overflow-y-auto divide-y divide-border/60 max-h-[620px]">
              {events.map((ev) => (
                <div key={ev.id} className="flex items-start gap-2.5 p-3 hover:bg-muted/15 transition-colors">
                  <div className="mt-1 size-2 shrink-0 rounded-full" style={{ backgroundColor: ev.color }} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-bold text-foreground truncate">{ev.label}</span>
                      <span
                        className="shrink-0 rounded px-1.5 py-0.2 font-mono text-[9px] font-bold"
                        style={{ background: `${ev.color}18`, color: ev.color }}
                      >
                        {ev.status}
                      </span>
                    </div>
                    <div className="text-[11px] text-muted-foreground flex items-center justify-between mt-0.5">
                      <span>{ev.cameraName}</span>
                      <span className="font-mono text-[10px] font-semibold text-foreground">{ev.confidence.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center gap-1 font-mono text-[9.5px] text-muted-foreground/70 mt-1">
                      <Clock size={9} />
                      <span>{ev.time}</span>
                      <span>·</span>
                      <span className="truncate">{ev.zone}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </aside>
        )}
      </div>

      {/* Stream Inspector Modal */}
      {selectedPlayerCamera && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="relative w-full max-w-3xl overflow-hidden rounded-2xl border border-border bg-card animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-border p-4 bg-muted/20">
              <div className="flex items-center gap-2.5">
                <div className="flex size-7 items-center justify-center rounded-lg bg-brand/10 text-brand">
                  <Camera size={15} />
                </div>
                <div>
                  <div className="text-sm font-bold text-foreground">{selectedPlayerCamera.name}</div>
                  <div className="text-[11px] text-muted-foreground">{selectedPlayerCamera.zone} · {selectedPlayerCamera.clusterName}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => enterFullScreen('1x1')}
                  title="Fullscreen TV Wall"
                  className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
                >
                  <Maximize2 size={15} />
                </button>
                <button
                  onClick={() => setSelectedPlayerCamera(null)}
                  className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
                >
                  <X size={15} />
                </button>
              </div>
            </div>

            {/* Video Canvas Simulation */}
            <div
              className="relative aspect-video w-full bg-black select-none"
              style={{ background: `radial-gradient(ellipse at center, hsl(${selectedPlayerCamera.fps * 9}, 45%, 15%) 0%, #05070a 100%)` }}
            >
              <div className="absolute top-3 left-3 flex items-center gap-2 font-mono text-xs text-white bg-black/60 px-2.5 py-1 rounded-lg backdrop-blur-xs">
                <span className="size-2 rounded-full bg-success animate-pulse" />
                <span>RTSP STREAM ACTIVE • {selectedPlayerCamera.fps} FPS</span>
              </div>

              {/* Bounding Box HUD */}
              <div
                className="absolute rounded border-2 border-emerald-400 bg-emerald-500/10 pointer-events-none"
                style={{
                  top: '25%',
                  left: '30%',
                  width: '35%',
                  height: '50%',
                }}
              >
                <span className="absolute -top-5 left-0 rounded bg-emerald-500 px-1.5 py-0.5 font-mono text-[9px] font-bold text-black">
                  {selectedPlayerCamera.model} 98.2%
                </span>
              </div>
            </div>

            {/* Metadata Footer */}
            <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted-foreground bg-muted/10 font-mono">
              <div className="flex items-center gap-2">
                <Server size={13} className="text-info" />
                <span>{selectedPlayerCamera.nodeName} ({selectedPlayerCamera.streamUrl})</span>
              </div>
              <span className="text-foreground font-semibold">{selectedPlayerCamera.resolution}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
