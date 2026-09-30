import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  RotateCw, Cpu, MemoryStick, HardDrive,
  Thermometer, Activity, Camera, Radio, Terminal, Search,
  Download, Copy, Trash2, Pause, Play, Check, AlertTriangle,
  Boxes, Plus, Server, Network, Globe, Tag, Clock,
} from 'lucide-react'
import type { NodeAgent } from '@/modules/cluster/types/cluster'
import type { RuntimeId, LogLevel } from '@/modules/agent/types/logs'
import { useNodeLogStream } from '@/modules/agent/hooks/useNodeLogStream'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'
import AddCameraModal from '@/modules/agent/components/AddCameraModal'
import NodeMetricGauge from '@/modules/agent/components/NodeMetricGauge'

const LEVEL_COLORS: Record<LogLevel, { text: string; bg: string; border: string }> = {
  INFO:  { text: 'text-info',        bg: 'bg-info/10',        border: 'border-info/20' },
  WARN:  { text: 'text-warning',     bg: 'bg-warning/10',     border: 'border-warning/20' },
  ERROR: { text: 'text-destructive', bg: 'bg-destructive/10', border: 'border-destructive/20' },
  DEBUG: { text: 'text-muted-foreground', bg: 'bg-muted/40', border: 'border-border' },
  TRACE: { text: 'text-purple-400',  bg: 'bg-purple-500/10',  border: 'border-purple-500/20' },
}

const STATUS_STYLE: Record<NodeAgent['status'], { label: string; badge: string; dot: string; tile: string }> = {
  online:   { label: 'Online',   badge: 'border-success/30 bg-success/10 text-success',             dot: 'bg-success animate-pulse', tile: 'border-success/30 bg-success/10 text-success' },
  degraded: { label: 'Degraded', badge: 'border-warning/30 bg-warning/10 text-warning',             dot: 'bg-warning',               tile: 'border-warning/30 bg-warning/10 text-warning' },
  offline:  { label: 'Offline',  badge: 'border-border bg-muted/50 text-muted-foreground',          dot: 'bg-muted-foreground',      tile: 'border-border bg-muted/50 text-muted-foreground' },
}

export default function NodeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { clusters, loading: edgeOpsLoading, addCameraToNode } = useEdgeOps()

  const [showAddCameraModal, setShowAddCameraModal] = useState(false)

  // Log terminal states
  const [selectedRuntime, setSelectedRuntime] = useState<RuntimeId | 'all'>('all')
  const [logLevel, setLogLevel] = useState<LogLevel | 'ALL'>('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [copied, setCopied] = useState(false)
  const [actionNotice, setActionNotice] = useState<string | null>(null)

  // Find matching node and cluster from reactive context
  let node: NodeAgent | null = null
  let cluster: import('@/modules/cluster/types/cluster').Cluster | null = null

  for (const c of clusters) {
    const found = c.nodes.find((n) => n.id === id || n.name.toLowerCase() === id?.toLowerCase())
    if (found) {
      node = found
      cluster = c
      break
    }
  }

  // Fallback to first node if not found and clusters available
  if (!node && clusters[0]?.nodes[0]) {
    node = clusters[0].nodes[0]
    cluster = clusters[0]
  }

  const loading = edgeOpsLoading

  // ── 2. Runtimes & logs come from context (initial API load + realtime) ──
  const { runtimes, logs, isLive: isLiveStreaming, toggleLive, clear: clearLogs } =
    useNodeLogStream(node?.id, selectedRuntime, logLevel)

  const handleAddCamera = (camData: Record<string, unknown>) => {
    if (!node) return
    addCameraToNode(node.id, {
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
    setActionNotice(`Camera ${camData.name} added to ${node.name} successfully`)
    setShowAddCameraModal(false)
    setTimeout(() => setActionNotice(null), 3500)
  }

  const handleRestartProcess = (runtimeName: string) => {
    setActionNotice(`Restart command dispatched to runtime "${runtimeName}". Process recycling...`)
    setTimeout(() => setActionNotice(null), 3500)
  }

  const handleCopyLogs = () => {
    const text = logs.map((l) => `[${l.timestamp}] [${l.level}] [${l.runtime}] ${l.message}`).join('\n')
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  const handleDownloadLogs = () => {
    const text = logs.map((l) => `[${l.timestamp}] [${l.level}] [${l.runtime}] ${l.message}`).join('\n')
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${node?.name || 'node'}-${selectedRuntime}-logs.log`
    a.click()
    URL.revokeObjectURL(url)
  }

  const filteredLogs = logs.filter((l) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return l.message.toLowerCase().includes(q) || l.runtime.toLowerCase().includes(q)
  })

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <div className="flex items-center gap-2 text-sm">
          <div className="size-4 animate-spin rounded-full border-2 border-border border-t-brand" />
          Loading node details…
        </div>
      </div>
    )
  }

  if (!node) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 p-12 text-muted-foreground">
        <AlertTriangle size={36} className="text-destructive" />
        <p className="font-semibold text-foreground">Node Agent Not Found</p>
        <Link to="/agent/nodes" className="text-xs font-semibold text-brand hover:underline">
          ← Back to Nodes
        </Link>
      </div>
    )
  }

  const onlineCameras = node.cameras.filter((c) => c.online).length

  return (
    <div className="flex flex-col gap-6">
      {/* ── Action Notice ── */}
      {actionNotice && (
        <div className="flex items-center justify-between rounded-lg border border-info/30 bg-info/10 px-4 py-2 text-xs font-medium text-info animate-in fade-in duration-150">
          <span>{actionNotice}</span>
          <button onClick={() => setActionNotice(null)} className="text-info/70 hover:text-info">✕</button>
        </div>
      )}

      {/* ── TOP HEADER CARD: identity + status + meta + actions ── */}
      <section className="rounded-xl border border-border bg-card p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3.5">
            <div className={`flex size-11 shrink-0 items-center justify-center rounded-xl border ${STATUS_STYLE[node.status].tile}`}>
              <Server size={20} />
            </div>
            <div className="flex min-w-0 flex-col gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="font-mono text-lg font-bold leading-none tracking-tight text-foreground">{node.name}</h1>
                <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${STATUS_STYLE[node.status].badge}`}>
                  <span className={`size-1.5 rounded-full ${STATUS_STYLE[node.status].dot}`} />
                  {STATUS_STYLE[node.status].label}
                </span>
                {cluster && (
                  <Link
                    to={`/agent/clusters/${cluster.id}`}
                    className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-[11px] font-semibold text-muted-foreground transition-colors hover:border-brand/40 hover:text-brand"
                  >
                    <Network size={11} />
                    {cluster.name}
                  </Link>
                )}
              </div>
              <dl className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
                {[
                  { icon: <Globe size={12} />, label: 'IP', value: node.ip, mono: true },
                  { icon: <Cpu size={12} />, label: 'HW', value: node.hardware, mono: false },
                  { icon: <Tag size={12} />, label: 'Agent', value: node.agentVersion, mono: true },
                  { icon: <Clock size={12} />, label: 'Uptime', value: node.uptime, mono: true },
                ].map((m) => (
                  <div key={m.label} className="flex items-center gap-1.5 text-muted-foreground">
                    {m.icon}
                    <dt className="sr-only">{m.label}</dt>
                    <dd className={`text-foreground/90 ${m.mono ? 'font-mono' : 'font-medium'}`}>{m.value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="hidden text-[11px] text-muted-foreground sm:inline">
              Heartbeat <span className="font-mono text-foreground/80">{node.lastHeartbeat}</span>
            </span>
            <button
              onClick={() => handleRestartProcess('Edge Agent Core')}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:border-brand/40 hover:bg-muted cursor-pointer"
            >
              <RotateCw size={13} />
              Restart Agent
            </button>
          </div>
        </div>
      </section>

      {/* ── 1. HARDWARE TELEMETRY GAUGES ── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
        <NodeMetricGauge icon={<Cpu size={12} />} label="CPU" value={node.cpuUsage} unit="%" percent={node.cpuUsage} />
        <NodeMetricGauge icon={<Activity size={12} />} label="GPU" value={node.gpuUsage} unit="%" percent={node.gpuUsage} />
        <NodeMetricGauge
          icon={<MemoryStick size={12} />} label="RAM"
          value={node.ramUsedGb} unit="GB" suffix={`/ ${node.ramTotalGb}`}
          percent={node.ramTotalGb ? (node.ramUsedGb / node.ramTotalGb) * 100 : 0}
        />
        <NodeMetricGauge icon={<HardDrive size={12} />} label="Storage" value={node.diskUsage} unit="%" percent={node.diskUsage} warnAt={80} critAt={92} />
        <NodeMetricGauge icon={<Thermometer size={12} />} label="Temp" value={node.tempC} unit="°C" percent={(node.tempC / 90) * 100} warnAt={78} critAt={89} />
        <NodeMetricGauge
          icon={<Camera size={12} />} label="Cameras"
          value={onlineCameras} suffix={`/ ${node.cameras.length} online`}
          percent={node.cameras.length ? (onlineCameras / node.cameras.length) * 100 : 0}
          barClassName={onlineCameras === node.cameras.length ? 'bg-success' : 'bg-warning'}
        />
      </div>

      {/* ── 2. RUNTIME PROCESSES MATRIX (Từng runtime chi tiết) ── */}
      <section className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-muted/20">
          <div className="flex items-center gap-2">
            <Boxes size={15} className="text-brand" />
            <span className="text-xs font-bold text-foreground tracking-wider">
              Node Runtimes &amp; Active Processes ({runtimes.length})
            </span>
          </div>
          <span className="text-xs text-muted-foreground">
            Model: <strong className="text-foreground font-mono">{node.modelRunning}</strong>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border/80 bg-muted/10 text-muted-foreground text-[11px] font-semibold">
                <th className="px-4 py-2.5 text-left">Runtime Process</th>
                <th className="px-4 py-2.5 text-left">PID / Version</th>
                <th className="px-4 py-2.5 text-center">Status</th>
                <th className="px-4 py-2.5 text-right">CPU</th>
                <th className="px-4 py-2.5 text-right">Memory</th>
                <th className="px-4 py-2.5 text-right">Uptime</th>
                <th className="px-4 py-2.5 text-right">24h Errors</th>
                <th className="px-4 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {runtimes.map((proc) => {
                const isSelected = selectedRuntime === proc.id
                return (
                  <tr
                    key={proc.id}
                    className={`border-b border-border/40 last:border-0 transition-colors ${
                      isSelected ? 'bg-brand/10' : 'hover:bg-muted/20'
                    }`}
                  >
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-bold text-foreground flex items-center gap-1.5">
                          <span className={`size-1.5 rounded-full ${proc.status === 'running' ? 'bg-success' : 'bg-warning'}`} />
                          <span>{proc.name}</span>
                        </div>
                        <div className="text-[11px] text-muted-foreground mt-0.5 truncate max-w-sm">{proc.description}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground">
                      PID: {proc.pid} · <span className="text-foreground">{proc.version}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold ${
                        proc.status === 'running' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
                      }`}>
                        {proc.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-foreground">
                      {proc.cpuPercent}%
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                      {proc.memoryMb} MB
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                      {proc.uptime}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {proc.errorCount24h > 0 ? (
                        <span className="rounded-full bg-destructive/15 px-1.5 py-0.5 font-bold text-destructive">
                          {proc.errorCount24h}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">0</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setSelectedRuntime(proc.id)}
                          className={`rounded px-2 py-1 text-[11px] font-semibold transition-colors ${
                            isSelected ? 'bg-brand text-brand-foreground' : 'bg-muted/60 text-muted-foreground hover:text-foreground'
                          }`}
                        >
                          View Logs
                        </button>
                        <button
                          onClick={() => handleRestartProcess(proc.name)}
                          title="Restart this runtime process"
                          className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                        >
                          <RotateCw size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Modal Thêm Camera */}
      {node && cluster && (
        <AddCameraModal
          isOpen={showAddCameraModal}
          onClose={() => setShowAddCameraModal(false)}
          clusters={clusters}
          defaultNodeId={node.id}
          onAddCamera={handleAddCamera}
        />
      )}

      {/* ── 3. ASSIGNED CAMERAS ON THIS NODE ── */}
      <section className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-muted/20">
          <div className="flex items-center gap-2">
            <Camera size={15} className="text-purple-500" />
            <span className="text-xs font-bold text-foreground tracking-wider">
              Assigned Camera Streams ({node.cameras.length})
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-success font-semibold">{onlineCameras} Cameras Live</span>
            <button
              onClick={() => setShowAddCameraModal(true)}
              className="flex items-center gap-1 rounded bg-brand px-2.5 py-1 text-xs font-semibold text-white hover:opacity-90 transition-opacity cursor-pointer"
            >
              <Plus size={12} />
              <span>Add Camera to Node</span>
            </button>
          </div>
        </div>

        <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
          {node.cameras.map((cam) => (
            <div key={cam.id} className="flex flex-col justify-between rounded-lg border border-border bg-muted/15 p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Radio size={12} className={cam.online ? 'text-success' : 'text-destructive'} />
                  <span className="font-bold text-xs text-foreground">{cam.name}</span>
                </div>
                <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-bold ${
                  cam.online ? 'bg-success/10 text-success' : 'bg-muted text-muted-foreground'
                }`}>
                  {cam.online ? 'LIVE' : 'OFFLINE'}
                </span>
              </div>
              <div className="my-2">
                <div className="text-[11px] text-muted-foreground">{cam.zone}</div>
                <div className="font-mono text-xs font-bold text-foreground mt-0.5">
                  {cam.online ? `${cam.fps} FPS · ${cam.resolution}` : 'Stream Inactive'}
                </div>
              </div>
              <div className="flex items-center justify-between border-t border-border/60 pt-2 text-[10px] text-muted-foreground">
                <span>Model: {cam.model}</span>
                {cam.alertCount > 0 && <span className="font-bold text-destructive">{cam.alertCount} Alerts</span>}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── 4. INTEGRATED RUNTIME LOGS CONSOLE ── */}
      <section className="flex flex-col rounded-xl border border-border bg-card overflow-hidden transition-colors">
        {/* Terminal toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/20 px-4 py-2.5">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Terminal size={14} className="text-brand" />
              <span className="text-xs font-bold text-foreground">
                Runtime Log Console {selectedRuntime !== 'all' && `[${selectedRuntime}]`}
              </span>
            </div>
            <span className="text-xs font-mono text-muted-foreground">
              ({filteredLogs.length} events)
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Search */}
            <div className="relative flex items-center">
              <Search size={12} className="absolute left-2.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Filter logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-7 w-32 rounded-md border border-border bg-background pl-7 pr-2 text-xs text-foreground placeholder:text-muted-foreground focus:w-44 focus:border-brand transition-all outline-none"
              />
            </div>

            {/* Level filter */}
            <select
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value as LogLevel | 'ALL')}
              className="h-7 rounded-md border border-border bg-background px-2 text-[11px] font-semibold text-foreground outline-none"
            >
              <option value="ALL">All Levels</option>
              <option value="INFO">Info</option>
              <option value="WARN">Warn</option>
              <option value="ERROR">Error</option>
              <option value="DEBUG">Debug</option>
            </select>

            {/* Runtime Filter Dropdown */}
            <select
              value={selectedRuntime}
              onChange={(e) => setSelectedRuntime(e.target.value as RuntimeId | 'all')}
              className="h-7 rounded-md border border-border bg-background px-2 text-[11px] font-semibold text-foreground outline-none"
            >
              <option value="all">All Runtimes</option>
              {runtimes.map((r) => (
                <option key={r.id} value={r.id}>{r.name.split(' (')[0]}</option>
              ))}
            </select>

            {/* Pause / Resume */}
            <button
              onClick={toggleLive}
              className={`flex h-7 items-center gap-1 rounded-md px-2 text-xs font-semibold transition-colors ${
                isLiveStreaming ? 'bg-muted text-foreground' : 'bg-success/20 text-success'
              }`}
            >
              {isLiveStreaming ? <Pause size={12} /> : <Play size={12} />}
              <span>{isLiveStreaming ? 'Pause' : 'Resume'}</span>
            </button>

            <div className="h-4 w-px bg-border/60 mx-0.5" />

            <button
              onClick={handleCopyLogs}
              title="Copy visible logs"
              className="flex size-7 items-center justify-center rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground cursor-pointer transition-colors"
            >
              {copied ? <Check size={13} className="text-success" /> : <Copy size={13} />}
            </button>

            <button
              onClick={handleDownloadLogs}
              title="Download .log file"
              className="flex size-7 items-center justify-center rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground cursor-pointer transition-colors"
            >
              <Download size={13} />
            </button>

            <button
              onClick={clearLogs}
              title="Clear log buffer"
              className="flex size-7 items-center justify-center rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-destructive cursor-pointer transition-colors"
            >
              <Trash2 size={13} />
            </button>
          </div>
        </div>

        {/* Terminal Lines with full Light/Dark theme support */}
        <div className="h-96 overflow-y-auto p-4 font-mono text-[12px] leading-relaxed bg-background/50 text-foreground transition-colors">
          {filteredLogs.map((log, index) => {
            const levelStyle = LEVEL_COLORS[log.level] || LEVEL_COLORS.INFO
            return (
              <div
                key={log.id}
                className="group flex items-start gap-2.5 py-0.5 transition-colors hover:bg-muted/30 rounded px-1"
              >
                <span className="w-8 shrink-0 text-right select-none text-[10px] text-muted-foreground/60">
                  {index + 1}
                </span>
                <span className="shrink-0 text-[11px] text-muted-foreground">
                  {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
                <span className={`shrink-0 rounded border px-1.5 py-px text-[9px] font-bold ${levelStyle.bg} ${levelStyle.text} ${levelStyle.border}`}>
                  {log.level}
                </span>
                <span className="shrink-0 text-[11px] text-brand font-semibold">
                  [{log.runtime}]
                </span>
                <span className={`flex-1 break-all ${log.level === 'ERROR' ? 'text-destructive font-medium' : log.level === 'WARN' ? 'text-warning' : 'text-foreground'}`}>
                  {log.message}
                </span>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
