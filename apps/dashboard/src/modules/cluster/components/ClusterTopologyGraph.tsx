import { useEffect, useRef, useState, useCallback } from 'react'
import {
  ZoomIn, ZoomOut, RotateCcw, Play, Pause, Maximize2, Minimize2,
  ArrowUpRight,
} from 'lucide-react'
import type { Cluster, NodeAgent, CameraOnNode } from '@/modules/cluster/types/cluster'

interface GraphNode {
  id: string
  label: string
  sublabel?: string
  type: 'hub' | 'cluster' | 'node' | 'camera'
  status: 'healthy' | 'online' | 'degraded' | 'critical' | 'offline'
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  data?: Cluster | NodeAgent | CameraOnNode
  clusterId?: string
  nodeId?: string
}

interface GraphLink {
  source: string
  target: string
  status: 'active' | 'warning' | 'error' | 'inactive'
  direction: 'up' | 'down' | 'bidirectional'
}

interface MessagePacket {
  sourceId: string
  targetId: string
  progress: number
  speed: number
  color: string
  size: number
  type: 'telemetry' | 'detection' | 'video_frame' | 'cloud_command'
}

interface Props {
  clusters: Cluster[]
  onSelectCluster?: (clusterId: string) => void
  onSelectNode?: (nodeId: string) => void
}

const STATUS_COLORS = {
  healthy: '#10b981',
  online: '#10b981',
  degraded: '#f59e0b',
  critical: '#ef4444',
  offline: '#64748b',
}

export default function ClusterTopologyGraph({ clusters, onSelectCluster, onSelectNode }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)

  const [selectedItem, setSelectedItem] = useState<GraphNode | null>(null)
  const [hoveredItem, setHoveredItem] = useState<GraphNode | null>(null)
  const [isSimulating, setIsSimulating] = useState(true)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [streamFilter, setStreamFilter] = useState<'all' | 'detections' | 'telemetry' | 'commands'>('all')

  // Transform state (Pan & Zoom)
  const transformRef = useRef({ x: 0, y: 0, scale: 1 })
  const isDraggingRef = useRef(false)
  const lastMousePosRef = useRef({ x: 0, y: 0 })
  const draggedNodeRef = useRef<GraphNode | null>(null)

  // Simulation state
  const nodesRef = useRef<GraphNode[]>([])
  const linksRef = useRef<GraphLink[]>([])
  const packetsRef = useRef<MessagePacket[]>([])
  const animFrameIdRef = useRef<number>(0)

  // ── 1. Initialize Graph Topology with 3-tier Pipeline ────────────────────────
  const initGraph = useCallback(() => {
    const nodes: GraphNode[] = []
    const links: GraphLink[] = []
    const packets: MessagePacket[] = []

    // Tier 1: Cloud & Control Plane Gateway
    const hubNode: GraphNode = {
      id: 'root-cloud',
      label: 'AI Edge Cloud',
      sublabel: 'Central Hub & Gateway',
      type: 'hub',
      status: 'online',
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      radius: 30,
    }
    nodes.push(hubNode)

    const clusterCount = clusters.length
    clusters.forEach((cluster, cIdx) => {
      const clusterAngle = (cIdx / Math.max(1, clusterCount)) * Math.PI * 2
      const clusterDist = 185 + (cIdx % 2) * 15
      const cx = Math.cos(clusterAngle) * clusterDist
      const cy = Math.sin(clusterAngle) * clusterDist

      // Tier 2: Cluster Gateway
      const cNode: GraphNode = {
        id: cluster.id,
        label: cluster.name,
        sublabel: `${cluster.site} (${cluster.onlineNodes}/${cluster.totalNodes} Nodes)`,
        type: 'cluster',
        status: cluster.status,
        x: cx,
        y: cy,
        vx: 0,
        vy: 0,
        radius: 22,
        data: cluster,
      }
      nodes.push(cNode)

      // Cluster <-> Cloud link
      links.push({
        source: cluster.id,
        target: 'root-cloud',
        status: cluster.status === 'healthy' ? 'active' : cluster.status === 'degraded' ? 'warning' : 'error',
        direction: 'up',
      })

      // Cloud command downward packet
      packets.push({
        sourceId: 'root-cloud',
        targetId: cluster.id,
        progress: Math.random(),
        speed: 0.003 + Math.random() * 0.003,
        color: '#c084fc', // purple
        size: 3,
        type: 'cloud_command',
      })

      // Tier 3: Edge Node Agents
      const nodeCount = cluster.nodes.length
      cluster.nodes.forEach((node, nIdx) => {
        const spreadAngle = clusterAngle + ((nIdx - (nodeCount - 1) / 2) * 0.46)
        const nodeDist = clusterDist + 130 + (nIdx % 2) * 20
        const nx = Math.cos(spreadAngle) * nodeDist
        const ny = Math.sin(spreadAngle) * nodeDist

        const nNode: GraphNode = {
          id: node.id,
          label: node.name,
          sublabel: `${node.hardware.split(' ')[0]} · ${node.ip}`,
          type: 'node',
          status: node.status,
          x: nx,
          y: ny,
          vx: 0,
          vy: 0,
          radius: 16,
          data: node,
          clusterId: cluster.id,
        }
        nodes.push(nNode)

        // Node -> Cluster Gateway link
        links.push({
          source: node.id,
          target: cluster.id,
          status: node.status === 'online' ? 'active' : node.status === 'degraded' ? 'warning' : 'inactive',
          direction: 'up',
        })

        if (node.status === 'online') {
          // Node -> Cluster Telemetry Packet Stream
          packets.push({
            sourceId: node.id,
            targetId: cluster.id,
            progress: Math.random(),
            speed: 0.005 + Math.random() * 0.004,
            color: '#10b981', // green telemetry
            size: 2.8,
            type: 'telemetry',
          })
          packets.push({
            sourceId: cluster.id,
            targetId: 'root-cloud',
            progress: Math.random(),
            speed: 0.006 + Math.random() * 0.005,
            color: '#10b981',
            size: 3,
            type: 'telemetry',
          })
        }

        // Tier 4: Edge Cameras (Leaf Devices)
        const camCount = node.cameras.length
        node.cameras.forEach((cam, camIdx) => {
          const camAngle = spreadAngle + ((camIdx - (camCount - 1) / 2) * 0.26)
          const camDist = nodeDist + 80 + (camIdx % 2) * 15
          const camX = Math.cos(camAngle) * camDist
          const camY = Math.sin(camAngle) * camDist

          const camNode: GraphNode = {
            id: cam.id,
            label: cam.name,
            sublabel: `${cam.fps} FPS · ${cam.zone}`,
            type: 'camera',
            status: cam.online ? 'online' : 'offline',
            x: camX,
            y: camY,
            vx: 0,
            vy: 0,
            radius: 11,
            data: cam,
            clusterId: cluster.id,
            nodeId: node.id,
          }
          nodes.push(camNode)

          // Camera -> Node link
          links.push({
            source: cam.id,
            target: node.id,
            status: cam.online ? 'active' : 'inactive',
            direction: 'up',
          })

          if (cam.online) {
            // Camera -> Node Video & Detection message stream
            packets.push({
              sourceId: cam.id,
              targetId: node.id,
              progress: Math.random(),
              speed: 0.008 + Math.random() * 0.006,
              color: cam.alertCount > 0 ? '#ef4444' : '#38bdf8', // red detection or blue video stream
              size: cam.alertCount > 0 ? 3.5 : 2.2,
              type: cam.alertCount > 0 ? 'detection' : 'video_frame',
            })
          }
        })
      })
    })

    nodesRef.current = nodes
    linksRef.current = links
    packetsRef.current = packets
  }, [clusters])

  useEffect(() => {
    initGraph()
  }, [initGraph])

  const resetView = useCallback(() => {
    if (!containerRef.current) return
    const { clientWidth, clientHeight } = containerRef.current
    transformRef.current = {
      x: clientWidth / 2,
      y: clientHeight / 2,
      scale: clientWidth < 768 ? 0.6 : 0.85,
    }
  }, [])

  useEffect(() => {
    resetView()
  }, [resetView])

  // ── 2. Canvas Render & Animated Particle Simulation ──────────────────────
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const render = (_time: number) => {

      // Handle Resize
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current
        const dpr = window.devicePixelRatio || 1
        if (canvas.width !== clientWidth * dpr || canvas.height !== clientHeight * dpr) {
          canvas.width = clientWidth * dpr
          canvas.height = clientHeight * dpr
        }
      }

      const dpr = window.devicePixelRatio || 1
      ctx.save()
      ctx.scale(dpr, dpr)
      ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr)

      const { x: panX, y: panY, scale } = transformRef.current
      ctx.translate(panX, panY)
      ctx.scale(scale, scale)

      const nodes = nodesRef.current
      const links = linksRef.current
      const packets = packetsRef.current
      const nodeMap = new Map(nodes.map(n => [n.id, n]))

      // ── Draw Grid Background ──
      const gridSpacing = 40
      const startX = Math.floor((-panX / scale) / gridSpacing) * gridSpacing - 100
      const endX = Math.ceil(((canvas.width / dpr - panX) / scale) / gridSpacing) * gridSpacing + 100
      const startY = Math.floor((-panY / scale) / gridSpacing) * gridSpacing - 100
      const endY = Math.ceil(((canvas.height / dpr - panY) / scale) / gridSpacing) + 100

      ctx.fillStyle = 'rgba(148, 163, 184, 0.08)'
      for (let gx = startX; gx < endX; gx += gridSpacing) {
        for (let gy = startY; gy < endY; gy += gridSpacing) {
          ctx.beginPath()
          ctx.arc(gx, gy, 1, 0, Math.PI * 2)
          ctx.fill()
        }
      }

      // ── Draw Links ──
      links.forEach((link) => {
        const src = nodeMap.get(link.source)
        const tgt = nodeMap.get(link.target)
        if (!src || !tgt) return

        ctx.beginPath()
        ctx.moveTo(src.x, src.y)
        ctx.lineTo(tgt.x, tgt.y)

        if (link.status === 'active') {
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.28)'
          ctx.lineWidth = 1.4
        } else if (link.status === 'warning') {
          ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)'
          ctx.lineWidth = 1.6
          ctx.setLineDash([4, 4])
        } else {
          ctx.strokeStyle = 'rgba(100, 116, 139, 0.18)'
          ctx.lineWidth = 1
          ctx.setLineDash([2, 4])
        }
        ctx.stroke()
        ctx.setLineDash([])
      })

      // ── Draw Animated Message Flow (Edge Camera -> Node -> Cloud) ──
      if (isSimulating) {
        packets.forEach((p) => {
          if (streamFilter !== 'all') {
            if (streamFilter === 'detections' && p.type !== 'detection') return
            if (streamFilter === 'telemetry' && p.type !== 'telemetry') return
            if (streamFilter === 'commands' && p.type !== 'cloud_command') return
          }

          const src = nodeMap.get(p.sourceId)
          const tgt = nodeMap.get(p.targetId)
          if (!src || !tgt) return

          p.progress = (p.progress + p.speed) % 1
          const px = src.x + (tgt.x - src.x) * p.progress
          const py = src.y + (tgt.y - src.y) * p.progress

          // Flow trail particle
          ctx.beginPath()
          ctx.arc(px, py, p.size, 0, Math.PI * 2)
          ctx.fillStyle = p.color
          ctx.fill()
        })
      }

      // ── Draw Nodes ──
      nodes.forEach((node) => {
        const isHovered = hoveredItem?.id === node.id
        const isSelected = selectedItem?.id === node.id
        const statusColor = STATUS_COLORS[node.status] || '#64748b'

        // Outer glow on hover / select
        if (isHovered || isSelected) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, node.radius + 7, 0, Math.PI * 2)
          ctx.fillStyle = `${statusColor}28`
          ctx.fill()
        }

        // Node Body Circle
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2)

        if (node.type === 'hub') {
          ctx.fillStyle = '#0f172a'
          ctx.strokeStyle = '#38bdf8'
          ctx.lineWidth = 2.8
        } else if (node.type === 'cluster') {
          ctx.fillStyle = '#1e293b'
          ctx.strokeStyle = statusColor
          ctx.lineWidth = isSelected ? 3 : 2
        } else if (node.type === 'node') {
          ctx.fillStyle = '#334155'
          ctx.strokeStyle = statusColor
          ctx.lineWidth = 1.8
        } else {
          // Camera
          ctx.fillStyle = node.status === 'online' ? '#0284c7' : '#475569'
          ctx.strokeStyle = statusColor
          ctx.lineWidth = 1.2
        }
        ctx.fill()
        ctx.stroke()

        // Status beacon indicator
        if (node.type !== 'camera') {
          ctx.beginPath()
          ctx.arc(node.x + node.radius * 0.7, node.y - node.radius * 0.7, 4, 0, Math.PI * 2)
          ctx.fillStyle = statusColor
          ctx.strokeStyle = '#ffffff'
          ctx.lineWidth = 1.2
          ctx.fill()
          ctx.stroke()
        }

        // Labels
        ctx.textAlign = 'center'
        ctx.font = node.type === 'hub' ? 'bold 11px system-ui' : node.type === 'cluster' ? 'bold 10.5px system-ui' : '9.5px system-ui'
        ctx.fillStyle = isHovered ? '#38bdf8' : '#f8fafc'
        ctx.fillText(node.label, node.x, node.y + node.radius + 13)

        if (node.sublabel && scale > 0.62) {
          ctx.font = '8.5px system-ui'
          ctx.fillStyle = '#94a3b8'
          ctx.fillText(node.sublabel, node.x, node.y + node.radius + 23)
        }
      })

      ctx.restore()
      animFrameIdRef.current = requestAnimationFrame(render)
    }

    animFrameIdRef.current = requestAnimationFrame(render)
    return () => cancelAnimationFrame(animFrameIdRef.current)
  }, [isSimulating, hoveredItem, selectedItem, streamFilter])

  // ── 3. Mouse & Touch Interactions ──────────────────────────────────────────
  const screenToWorld = useCallback((clientX: number, clientY: number) => {
    if (!canvasRef.current) return { x: 0, y: 0 }
    const rect = canvasRef.current.getBoundingClientRect()
    const { x: panX, y: panY, scale } = transformRef.current
    return {
      x: (clientX - rect.left - panX) / scale,
      y: (clientY - rect.top - panY) / scale,
    }
  }, [])

  const getNodeAtPos = useCallback((clientX: number, clientY: number) => {
    const { x, y } = screenToWorld(clientX, clientY)
    for (let i = nodesRef.current.length - 1; i >= 0; i--) {
      const n = nodesRef.current[i]
      if (Math.hypot(n.x - x, n.y - y) <= n.radius + 4) {
        return n
      }
    }
    return null
  }, [screenToWorld])

  const handleMouseDown = (e: React.MouseEvent) => {
    const node = getNodeAtPos(e.clientX, e.clientY)
    if (node) {
      draggedNodeRef.current = node
      setSelectedItem(node)
      if (node.type === 'cluster' && onSelectCluster) {
        onSelectCluster(node.id)
      } else if (node.type === 'node' && onSelectNode) {
        onSelectNode(node.id)
      }
    } else {
      isDraggingRef.current = true
      lastMousePosRef.current = { x: e.clientX, y: e.clientY }
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (draggedNodeRef.current) {
      const { x, y } = screenToWorld(e.clientX, e.clientY)
      draggedNodeRef.current.x = x
      draggedNodeRef.current.y = y
    } else if (isDraggingRef.current) {
      const dx = e.clientX - lastMousePosRef.current.x
      const dy = e.clientY - lastMousePosRef.current.y
      lastMousePosRef.current = { x: e.clientX, y: e.clientY }
      transformRef.current.x += dx
      transformRef.current.y += dy
    } else {
      const node = getNodeAtPos(e.clientX, e.clientY)
      setHoveredItem(node)
      if (canvasRef.current) {
        canvasRef.current.style.cursor = node ? 'pointer' : 'grab'
      }
    }
  }

  const handleMouseUp = () => {
    isDraggingRef.current = false
    draggedNodeRef.current = null
  }

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    if (!canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top

    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.88
    const newScale = Math.max(0.3, Math.min(2.5, transformRef.current.scale * zoomFactor))

    transformRef.current.x = mouseX - (mouseX - transformRef.current.x) * (newScale / transformRef.current.scale)
    transformRef.current.y = mouseY - (mouseY - transformRef.current.y) * (newScale / transformRef.current.scale)
    transformRef.current.scale = newScale
  }

  const zoomIn = () => {
    transformRef.current.scale = Math.min(2.5, transformRef.current.scale * 1.2)
  }

  const zoomOut = () => {
    transformRef.current.scale = Math.max(0.3, transformRef.current.scale / 1.2)
  }

  return (
    <div
      ref={containerRef}
      className={`relative w-full overflow-hidden rounded-xl border border-border bg-[#090d16] select-none ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none' : 'h-[calc(100vh-210px)] min-h-[580px]'
      }`}
    >
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        className="w-full h-full block"
      />

      {/* ── Top Left: View & Simulation Controls ── */}
      <div className="absolute top-3 left-3 flex flex-wrap items-center gap-1.5 rounded-lg border border-border/60 bg-card/85 p-1.5 backdrop-blur-md">
        <button onClick={zoomIn} title="Zoom In" className="flex size-7 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground">
          <ZoomIn size={14} />
        </button>
        <button onClick={zoomOut} title="Zoom Out" className="flex size-7 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground">
          <ZoomOut size={14} />
        </button>
        <button onClick={resetView} title="Reset View" className="flex size-7 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground">
          <RotateCcw size={14} />
        </button>
        <div className="h-4 w-px bg-border/60 mx-0.5" />
        <button
          onClick={() => setIsSimulating(v => !v)}
          title={isSimulating ? 'Pause Packet Stream' : 'Resume Packet Stream'}
          className={`flex size-7 items-center justify-center rounded transition-colors ${
            isSimulating ? 'text-brand hover:bg-brand/15' : 'text-muted-foreground hover:bg-muted'
          }`}
        >
          {isSimulating ? <Pause size={14} /> : <Play size={14} />}
        </button>
        <button
          onClick={() => setIsFullscreen(v => !v)}
          title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          className="flex size-7 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
        </button>
      </div>

      {/* ── Stream Filter Toolbar (Top Right) ── */}
      <div className="absolute top-3 right-3 flex flex-wrap items-center gap-1.5 rounded-lg border border-border/60 bg-card/85 p-1.5 backdrop-blur-md text-[11px]">
        <span className="text-muted-foreground px-1.5 font-medium">Message Flow:</span>
        {(['all', 'telemetry', 'detections', 'commands'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setStreamFilter(f)}
            className={`rounded px-2 py-0.5 font-semibold capitalize transition-colors ${
              streamFilter === f
                ? 'bg-foreground text-background'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {f === 'all' ? 'All Packets' : f === 'telemetry' ? 'Node Telemetry (🟢)' : f === 'detections' ? 'Detections (🔴)' : 'Cloud Sync (🟣)'}
          </button>
        ))}
      </div>

      {/* ── Packet Flow Pipeline Legend (Bottom Right) ── */}
      <div className="absolute bottom-3 right-3 hidden sm:flex flex-col gap-1.5 rounded-lg border border-border/60 bg-card/85 p-2.5 text-[10.5px] text-muted-foreground backdrop-blur-md pointer-events-none">
        <div className="font-semibold text-foreground flex items-center gap-1">
          <ArrowUpRight size={12} className="text-brand" />
          <span>Edge → Node → Cloud Pipeline:</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="size-2 rounded-full bg-[#38bdf8]" /> Camera RTSP / Frames
          <span className="text-muted-foreground/50">→</span>
          <span className="size-2 rounded-full bg-[#10b981]" /> Node Inference Telemetry
          <span className="text-muted-foreground/50">→</span>
          <span className="size-2 rounded-full bg-[#c084fc]" /> Cloud Sync
        </div>
      </div>

      {/* ── Selected Node Inspector Card ── */}
      {selectedItem && (
        <div className="absolute bottom-3 left-3 max-w-sm w-full rounded-xl border border-border bg-card/95 p-4 backdrop-blur-md animate-in fade-in slide-in-from-bottom-2 duration-150">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className={`size-2.5 rounded-full ${STATUS_COLORS[selectedItem.status] || 'bg-slate-500'}`} />
              <div>
                <h4 className="text-[13px] font-bold text-foreground leading-tight">{selectedItem.label}</h4>
                <p className="text-[10.5px] text-muted-foreground capitalize">{selectedItem.type} · {selectedItem.sublabel}</p>
              </div>
            </div>
            <button
              onClick={() => setSelectedItem(null)}
              className="text-muted-foreground hover:text-foreground text-xs px-1"
            >
              ✕
            </button>
          </div>

          {selectedItem.type === 'cluster' && selectedItem.data && (
            <div className="mt-3 grid grid-cols-3 gap-2 border-t border-border/60 pt-2 text-[11px]">
              <div>
                <span className="text-muted-foreground block text-[10px]">Nodes</span>
                <strong className="text-foreground">{(selectedItem.data as Cluster).onlineNodes}/{(selectedItem.data as Cluster).totalNodes}</strong>
              </div>
              <div>
                <span className="text-muted-foreground block text-[10px]">Cameras</span>
                <strong className="text-foreground">{(selectedItem.data as Cluster).onlineCameras}/{(selectedItem.data as Cluster).totalCameras}</strong>
              </div>
              <div>
                <span className="text-muted-foreground block text-[10px]">Agg FPS</span>
                <strong className="text-success">{(selectedItem.data as Cluster).aggregateFps}</strong>
              </div>
            </div>
          )}

          {selectedItem.type === 'node' && selectedItem.data && (
            <div className="mt-3 flex flex-col gap-2 border-t border-border/60 pt-2 text-[11px]">
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <span className="text-muted-foreground block text-[10px]">CPU</span>
                  <strong className="text-foreground">{(selectedItem.data as NodeAgent).cpuUsage}%</strong>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[10px]">GPU</span>
                  <strong className="text-foreground">{(selectedItem.data as NodeAgent).gpuUsage}%</strong>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[10px]">Cameras</span>
                  <strong className="text-info">{(selectedItem.data as NodeAgent).cameras.length}</strong>
                </div>
              </div>
              <a
                href={`#/agent/nodes/${selectedItem.id}`}
                className="mt-1 flex items-center justify-center gap-1.5 rounded-lg bg-brand py-1.5 text-xs font-semibold text-white hover:opacity-90 transition-opacity"
              >
                <span>View Node Runtimes &amp; Logs</span>
                <ArrowUpRight size={13} />
              </a>
            </div>
          )}

          {selectedItem.type === 'camera' && selectedItem.data && (
            <div className="mt-3 grid grid-cols-3 gap-2 border-t border-border/60 pt-2 text-[11px]">
              <div>
                <span className="text-muted-foreground block text-[10px]">FPS</span>
                <strong className="text-success">{(selectedItem.data as CameraOnNode).fps}</strong>
              </div>
              <div>
                <span className="text-muted-foreground block text-[10px]">Resolution</span>
                <strong className="text-foreground">{(selectedItem.data as CameraOnNode).resolution}</strong>
              </div>
              <div>
                <span className="text-muted-foreground block text-[10px]">Alerts</span>
                <strong className="text-destructive">{(selectedItem.data as CameraOnNode).alertCount}</strong>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
