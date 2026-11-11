import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Camera,
  LogOut,
  Moon,
  Maximize2,
  Minimize2,
  Network,
  Server,
  ShieldAlert,
  Sun,
  Users,
  Video,
} from 'lucide-react'
import type { Cluster, GridItem, NodeItem } from '@/api/types'
import { ROLE_LABEL } from '@/constants/labels'
import { useAuth } from '@/contexts/AuthContext'
import { useFilters } from '@/contexts/FilterContext'
import { useTheme } from '@/contexts/ThemeContext'
import { useResource } from '@/hooks/useResource'
import { clusterService } from '@/services/cluster.service'
import { nodeService } from '@/services/node.service'

interface Props {
  totalCameras?: number
  totalPeople?: number
  cameras?: GridItem[]
}

const NO_CLUSTERS: Cluster[] = []
const NO_NODES: NodeItem[] = []

export default function TopBar({ totalCameras, totalPeople, cameras = [] }: Props) {
  const { user, logout, canOperate } = useAuth()
  const { dark, toggle: toggleTheme } = useTheme()
  const { clusterId, nodeId, cameraId, setClusterId, setNodeId, setCameraId } = useFilters()
  const { data: clusters } = useResource(clusterService.list, NO_CLUSTERS)
  const { data: allNodes } = useResource(nodeService.list, NO_NODES)
  const location = useLocation()
  const isAdminRoute = location.pathname.startsWith('/admin')
  const isTopologyRoute = location.pathname.startsWith('/topology')
  const isDetectRoute = location.pathname.startsWith('/detect')
  const isMonitorRoute = !isAdminRoute && !isTopologyRoute && !isDetectRoute

  // Available Nodes under selected Cluster
  const availableNodes = clusterId
    ? allNodes.filter((n) => n.cluster_id === clusterId)
    : allNodes

  // Available Cameras under selected Node & Cluster
  const availableCameras = cameras.filter((c) => {
    const matchCluster = clusterId === null || c.cluster_id === clusterId
    const matchNode = nodeId === null || c.node_id === nodeId
    return matchCluster && matchNode
  })

  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement))
    }
    document.addEventListener('fullscreenchange', handleFsChange)
    return () => document.removeEventListener('fullscreenchange', handleFsChange)
  }, [])

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
    } else {
      document.exitFullscreen().catch(() => {})
    }
  }

  return (
    <header className="flex min-h-9 shrink-0 flex-wrap select-none items-center justify-between gap-x-2 gap-y-1 border-b border-line bg-panel/95 px-2.5 py-1 text-xs backdrop-blur-md">
      {/* Left: Brand + Navigation Mode Tabs + Strict 2-Level Filter: Cluster -> Nodes */}
      <div className="flex flex-wrap items-center gap-2 max-sm:w-full">
        {/* VMS System Logo */}
        <div className="brand flex items-center gap-1.5 pr-2 border-r border-line/60">
          <div className="grid size-5 place-items-center rounded bg-blue-600 text-white font-black text-[11px]">
            <ShieldAlert size={12} />
          </div>
          <span className="hidden font-extrabold tracking-wider text-ink uppercase text-[11px] sm:flex items-center gap-1">
            PPE VISION <span className="text-cyan-400 font-mono text-[9px] px-1 py-0.2 rounded bg-cyan-500/10 border border-cyan-500/20">VMS</span>
          </span>
        </div>

        {/* Top Navigation Mode Tabs (Segmented Switcher Style) */}
        <nav className="flex items-center p-0.5 rounded-md bg-black/40 border border-line/50">
          <Link
            to="/"
            className={`px-2.5 py-0.5 rounded text-[11px] tracking-tight transition-all ${
              isMonitorRoute
                ? 'bg-panel2 text-ink shadow-xs font-semibold border border-line-strong'
                : 'text-dim hover:text-ink font-medium'
            }`}
          >
            Camera Viewer
          </Link>

          <Link
            to="/topology"
            className={`px-2.5 py-0.5 rounded text-[11px] tracking-tight transition-all ${
              isTopologyRoute
                ? 'bg-panel2 text-ink shadow-xs font-semibold border border-line-strong'
                : 'text-dim hover:text-ink font-medium'
            }`}
          >
            Topology
          </Link>

          <Link
            to="/detect"
            className={`px-2.5 py-0.5 rounded text-[11px] tracking-tight transition-all ${
              isDetectRoute
                ? 'bg-panel2 text-ink shadow-xs font-semibold border border-line-strong'
                : 'text-dim hover:text-ink font-medium'
            }`}
          >
            Test Detect
          </Link>

          {canOperate && (
            <Link
              to="/admin"
              className={`px-2.5 py-0.5 rounded text-[11px] tracking-tight transition-all ${
                isAdminRoute
                  ? 'bg-panel2 text-ink shadow-xs font-semibold border border-line-strong'
                  : 'text-dim hover:text-ink font-medium'
              }`}
            >
              Administration
            </Link>
          )}
        </nav>

        {/* Strict Hierarchy Filters: 1. Cluster -> 2. Nodes -> 3. Camera */}
        {isMonitorRoute && (
          <div className="flex flex-wrap items-center gap-1.5 pl-2 max-sm:grid max-sm:w-full max-sm:grid-cols-3 max-sm:gap-1 max-sm:pl-0 max-sm:border-l-0 border-l border-line/60">
            {/* Level 1: Cluster Filter */}
            <div className="flex min-w-0 items-center gap-1 rounded bg-panel2/60 hover:bg-panel2 px-1.5 py-0.5 border border-line transition-colors">
              <Server size={10} className="text-cyan-400 shrink-0" />
              <select
                value={clusterId ?? ''}
                onChange={(e) => setClusterId(e.target.value ? Number(e.target.value) : null)}
                className="min-w-0 bg-transparent text-[11px] font-mono text-ink outline-none cursor-pointer max-w-[150px] truncate max-sm:w-full max-sm:max-w-none"
              >
                <option value="" className="bg-panel text-ink">All</option>
                {clusters.map((c) => (
                  <option key={c.id} value={c.id} className="bg-panel text-ink">
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <span className="hidden text-dim/40 text-[9px] font-mono sm:inline">&rsaquo;</span>

            {/* Level 2: Edge Node Filter (Dependent on Cluster) */}
            <div className="flex min-w-0 items-center gap-1 rounded bg-panel2/60 hover:bg-panel2 px-1.5 py-0.5 border border-line transition-colors">
              <Network size={10} className="text-emerald-400 shrink-0" />
              <select
                value={nodeId ?? ''}
                onChange={(e) => setNodeId(e.target.value ? Number(e.target.value) : null)}
                className="min-w-0 bg-transparent text-[11px] font-mono text-ink outline-none cursor-pointer max-w-[140px] truncate max-sm:w-full max-sm:max-w-none"
              >
                <option value="" className="bg-panel text-ink">All</option>
                {availableNodes.map((n) => (
                  <option key={n.id} value={n.id} className="bg-panel text-ink">
                    {n.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Level 3: Direct Camera selection (if specific camera isolated) */}
            {isMonitorRoute && (
              <>
                <span className="hidden text-dim/40 text-[9px] font-mono sm:inline">&rsaquo;</span>
                <div className="flex min-w-0 items-center gap-1 rounded bg-panel2/60 hover:bg-panel2 px-1.5 py-0.5 border border-line transition-colors">
                  <Camera size={10} className="text-amber-400 shrink-0" />
                  <select
                    value={cameraId ?? ''}
                    onChange={(e) => setCameraId(e.target.value ? Number(e.target.value) : null)}
                    className="min-w-0 bg-transparent text-[11px] font-mono text-ink outline-none cursor-pointer max-w-[130px] truncate max-sm:w-full max-sm:max-w-none"
                  >
                    <option value="" className="bg-panel text-ink">All</option>
                    {availableCameras.map((c) => (
                      <option key={c.camera_id} value={c.camera_id} className="bg-panel text-ink">
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Right: Metrics + Fullscreen & Logout */}
      <div className="flex items-center gap-2">
        {isMonitorRoute && (
          <div className="flex items-center gap-1.5">
            <div className="flex items-center gap-1 rounded bg-panel2/50 px-1.5 py-0.5 border border-line/60 text-[10px]">
              <Video size={11} className="text-emerald-400" />
              <span className="hidden text-dim/80 sm:inline">CAM:</span>
              <span className="font-mono font-bold text-ink">{totalCameras ?? 0}</span>
            </div>

            <div className="flex items-center gap-1 rounded bg-panel2/50 px-1.5 py-0.5 border border-line/60 text-[10px]">
              <Users size={11} className="text-cyan-400" />
              <span className="hidden text-dim/80 sm:inline">PEOPLE:</span>
              <span className="font-mono font-bold text-ink">{totalPeople ?? 0}</span>
            </div>
          </div>
        )}

        <div className="h-3.5 w-px bg-line/60" />

        {/* User Info */}
        {user && (
          <div className="hidden xl:flex items-center gap-1 px-1.5 py-0.5 rounded bg-panel2/50 border border-line/60 text-dim text-[11px]">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            <span className="font-medium text-ink max-w-[120px] truncate">{user.full_name}</span>
            <span className="text-[9px] font-mono text-dim/70">[{ROLE_LABEL[user.role]}]</span>
          </div>
        )}

        {/* Fullscreen button */}
        <button
          onClick={toggleFullscreen}
          title={isFullscreen ? 'Exit Fullscreen' : 'Toggle Fullscreen'}
          className="rounded p-1 text-dim hover:bg-panel2 hover:text-ink cursor-pointer border border-transparent hover:border-line transition-colors"
        >
          {isFullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
        </button>

        <button
          onClick={toggleTheme}
          title={dark ? 'Light theme' : 'Dark theme'}
          className="rounded p-1 text-dim hover:bg-panel2 hover:text-ink cursor-pointer border border-transparent hover:border-line transition-colors"
        >
          {dark ? <Sun size={12} /> : <Moon size={12} />}
        </button>

        {/* Logout */}
        <button
          onClick={logout}
          title="Logout"
          className="rounded p-1 text-dim hover:bg-rose-500/10 hover:text-rose-400 cursor-pointer border border-transparent hover:border-rose-500/20 transition-colors"
        >
          <LogOut size={12} />
        </button>
      </div>
    </header>
  )
}
