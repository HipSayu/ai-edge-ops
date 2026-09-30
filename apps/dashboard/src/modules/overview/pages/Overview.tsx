import { useState, useId, useMemo } from 'react'
import {
  Cpu, Camera, Rocket, Activity, Radio, Zap, Server, ArrowRight,
  Network, AlertTriangle, ShieldCheck, Layers, CheckCircle,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'
import StatCard from '@/shared/components/StatCard'
import type { FleetMetricPoint } from '@/modules/ai/types/ai'

// ─── Metric types ────────────────────────────────────────────────────────────
type TelemetryMetric = 'fps' | 'latency' | 'throughput' | 'gpu'


type TrendKey = Exclude<keyof FleetMetricPoint, 'time'>

/** Flat line shown until the first two realtime samples arrive */
const EMPTY_SERIES: FleetMetricPoint[] = [0, 1].map(() => ({
  time: '-', fps: 0, latency: 0, throughput: 0, gpu: 0, alert: 0, healthyClusters: 0, onlineNodes: 0, onlineCameras: 0,
}))

export default function Overview() {
  const { clusters, summary: clusterSummary, fleetMetrics, classConfig, deployments } = useEdgeOps()

  // Telemetry series & KPI trends (initial API load + metrics:fleet samples)
  const series = fleetMetrics.length >= 2 ? fleetMetrics : EMPTY_SERIES
  const latest = series[series.length - 1]
  const trend = (k: TrendKey) => {
    const pts = fleetMetrics.slice(-6).map((p) => p[k])
    return pts.length >= 2 ? pts : [0, 0]
  }

  // Top-5 enabled classes by 24h detections (class:{id} stats)
  const classDistribution = useMemo(() => {
    const top = classConfig
      .filter((c) => c.enabled)
      .sort((a, b) => b.detectionCount24h - a.detectionCount24h)
      .slice(0, 5)
    const total = top.reduce((sum, c) => sum + c.detectionCount24h, 0) || 1
    return top.map((c) => ({
      name: c.displayName,
      count: c.detectionCount24h,
      pct: Math.round((c.detectionCount24h / total) * 100),
      color: c.color,
    }))
  }, [classConfig])
  const totalDetections = classDistribution.reduce((sum, c) => sum + c.count, 0)
  const compact = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n))
  // Label roughly every 6th sample so a 30-point window stays readable
  const labelEvery = Math.max(1, Math.ceil(series.length / 6))
  const [activeMetric, setActiveMetric] = useState<TelemetryMetric>('fps')
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const gradId = useId()

  // Aggregate stats
  const totalClusters = clusterSummary?.totalClusters ?? clusters.length
  const healthyClusters = clusterSummary?.healthyClusters ?? clusters.filter(c => c.status === 'healthy').length
  const totalNodes = clusterSummary?.totalNodes ?? clusters.reduce((s, c) => s + c.totalNodes, 0)
  const onlineNodes = clusterSummary?.onlineNodes ?? clusters.reduce((s, c) => s + c.onlineNodes, 0)
  const totalCameras = clusterSummary?.totalCameras ?? clusters.reduce((s, c) => s + c.totalCameras, 0)
  const onlineCameras = clusterSummary?.onlineCameras ?? clusters.reduce((s, c) => s + c.onlineCameras, 0)
  const totalAlerts = clusterSummary?.totalAlerts ?? clusters.reduce((s, c) => s + c.totalAlerts, 0)

  // Extract all cameras for Overview vision grid
  const allCameras = clusters.flatMap((c) =>
    c.nodes.flatMap((n) =>
      n.cameras.map((cam) => ({
        ...cam,
        clusterId: c.id,
        clusterName: c.name,
        nodeId: n.id,
        nodeName: n.name,
        modelRunning: n.modelRunning || 'YOLOv8x-Safety',
      }))
    )
  )


  // Compute telemetry summary for main chart
  const metricConfig = {
    fps: { label: 'Aggregate Stream FPS', unit: 'FPS', color: '#3b82f6', desc: 'Real-time camera feed processing rate' },
    latency: { label: 'AI Inference Latency', unit: 'ms', color: '#10b981', desc: 'Average end-to-end tensor inference time' },
    throughput: { label: 'Inference Throughput', unit: 'infer/s', color: '#8b5cf6', desc: 'Total model inferences across all edge nodes' },
    gpu: { label: 'Average GPU Utilization', unit: '%', color: '#f59e0b', desc: 'Weighted cluster compute workload' },
  }[activeMetric]

  const values = series.map(p => p[activeMetric])
  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)
  const avgVal = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1)

  // SVG Area Chart geometry
  const SVG_W = 660
  const SVG_H = 180
  const PAD_L = 36
  const PAD_R = 20
  const PAD_T = 20
  const PAD_B = 30

  const range = Math.max(maxVal - minVal, 1)
  const stepX = (SVG_W - PAD_L - PAD_R) / (series.length - 1)

  const points = series.map((pt, i) => {
    const val = pt[activeMetric]
    const x = PAD_L + i * stepX
    const y = SVG_H - PAD_B - ((val - minVal) / range) * (SVG_H - PAD_T - PAD_B)
    return { x, y, val, time: pt.time }
  })

  const smoothPath = points.reduce((acc, p, i, arr) => {
    if (i === 0) return `M ${p.x.toFixed(1)} ${p.y.toFixed(1)}`
    const prev = arr[i - 1]
    const cp1x = prev.x + (p.x - prev.x) / 2
    const cp1y = prev.y
    const cp2x = prev.x + (p.x - prev.x) / 2
    const cp2y = p.y
    return `${acc} C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p.x.toFixed(1)} ${p.y.toFixed(1)}`
  }, '')

  const lastPt = points[points.length - 1]
  const firstPt = points[0]
  const areaPath = `${smoothPath} L ${lastPt.x.toFixed(1)} ${SVG_H - PAD_B} L ${firstPt.x.toFixed(1)} ${SVG_H - PAD_B} Z`
  const activePoint = hoveredIndex !== null ? points[hoveredIndex] : lastPt

  // Donut chart geometry
  const DONUT_SIZE = 140
  const DONUT_R = 52
  const CIRCUMFERENCE = 2 * Math.PI * DONUT_R

  let cumulativePct = 0
  const donutSlices = classDistribution.map((item, idx) => {
    const strokeDasharray = `${(item.pct / 100) * CIRCUMFERENCE} ${CIRCUMFERENCE}`
    const strokeDashoffset = -((cumulativePct / 100) * CIRCUMFERENCE)
    cumulativePct += item.pct
    return { ...item, strokeDasharray, strokeDashoffset, idx }
  })

  return (
    <div className="flex flex-col gap-5">
      {/* ── 1. TOP PRODUCTION SYSTEM SUMMARY (6 Core KPI Cards) ── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard
          label="Edge Clusters"
          value={`${healthyClusters}/${totalClusters}`}
          sub="Multi-site SLA 100%"
          icon={<Network size={14} />}
          variant="brand"
          trend={trend('healthyClusters')}
          trendColor="#3b82f6"
        />
        <StatCard
          label="Inference Nodes"
          value={`${onlineNodes}/${totalNodes}`}
          sub="Jetson Orin Nodes"
          icon={<Server size={14} />}
          variant="success"
          trend={trend('onlineNodes')}
          trendColor="#10b981"
        />
        <StatCard
          label="Camera Feeds"
          value={`${onlineCameras}/${totalCameras}`}
          sub="Live RTSP Ingestion"
          icon={<Camera size={14} />}
          variant="purple"
          trend={trend('onlineCameras')}
          trendColor="#a855f7"
        />
        <StatCard
          label="Avg Inference FPS"
          value={`${latest.fps} FPS`}
          sub="Aggregate Speed"
          icon={<Radio size={14} />}
          variant="info"
          trend={trend('fps')}
          trendColor="#0ea5e9"
        />
        <StatCard
          label="Latency"
          value={`${latest.latency} ms`}
          sub="TensorRT Acceleration"
          icon={<Zap size={14} />}
          variant="warning"
          trend={trend('latency')}
          trendColor="#f59e0b"
        />
        <StatCard
          label="Safety Events"
          value={totalAlerts}
          sub={totalAlerts > 0 ? 'Requires attention' : 'Normal status'}
          icon={<AlertTriangle size={14} />}
          variant={totalAlerts > 0 ? 'destructive' : 'success'}
          trend={trend('alert')}
          trendColor={totalAlerts > 0 ? '#ef4444' : '#10b981'}
        />
      </div>

      {/* ── 2. MAIN ANALYTICS SECTION: System Telemetry Trend + AI Class Distribution ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Left: 24h Telemetry Time-series Trend */}
        <section className="flex flex-col rounded-xl border border-border bg-card p-4 lg:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <div>
              <div className="flex items-center gap-2">
                <Activity size={15} className="text-brand" />
                <h3 className="text-xs font-bold tracking-wider text-foreground">
                  Edge System Telemetry (24h Trend)
                </h3>
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5">{metricConfig.desc}</p>
            </div>

            {/* Metric Switcher Tabs */}
            <div className="flex items-center gap-0.5 rounded-lg border border-border bg-muted/20 p-0.5">
              {(['fps', 'latency', 'throughput', 'gpu'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setActiveMetric(m)}
                  className={`rounded px-2.5 py-1 text-[11px] font-semibold transition-colors cursor-pointer ${
                    activeMetric === m ? 'bg-foreground text-background' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Quick value banner */}
          <div className="flex items-center gap-6 py-2 text-xs border-b border-border/60">
            <div>
              <span className="text-muted-foreground text-[10.5px]">Current:</span>{' '}
              <strong className="text-foreground font-mono text-sm">{activePoint.val} {metricConfig.unit}</strong>
            </div>
            <div>
              <span className="text-muted-foreground text-[10.5px]">Avg:</span>{' '}
              <span className="text-muted-foreground font-mono font-semibold">{avgVal} {metricConfig.unit}</span>
            </div>
            <div>
              <span className="text-muted-foreground text-[10.5px]">Peak:</span>{' '}
              <span className="text-foreground font-mono font-semibold">{maxVal} {metricConfig.unit}</span>
            </div>
            <div className="ml-auto text-muted-foreground text-[11px] font-mono">
              Timestamp: <strong className="text-brand">{activePoint.time}</strong>
            </div>
          </div>

          {/* SVG Smooth Curve Area Chart */}
          <div className="relative mt-2 w-full overflow-hidden">
            <svg
              viewBox={`0 0 ${SVG_W} ${SVG_H}`}
              className="w-full h-44 overflow-visible"
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <defs>
                <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={metricConfig.color} stopOpacity="0.3" />
                  <stop offset="100%" stopColor={metricConfig.color} stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid lines */}
              {[0, 0.33, 0.66, 1].map((ratio, i) => {
                const y = PAD_T + ratio * (SVG_H - PAD_T - PAD_B)
                return (
                  <line
                    key={i}
                    x1={PAD_L}
                    y1={y}
                    x2={SVG_W - PAD_R}
                    y2={y}
                    stroke="currentColor"
                    className="text-border/40"
                    strokeDasharray="4 4"
                  />
                )
              })}

              {/* Area & Line */}
              <path d={areaPath} fill={`url(#${gradId})`} />
              <path d={smoothPath} fill="none" stroke={metricConfig.color} strokeWidth={2.5} strokeLinecap="round" />

              {/* Interactive Points */}
              {points.map((p, idx) => (
                <g key={idx} onMouseEnter={() => setHoveredIndex(idx)} className="cursor-pointer">
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={hoveredIndex === idx ? 5 : 3}
                    fill={metricConfig.color}
                    className="transition-all"
                  />
                  {/* Time label bottom */}
                  <text
                    x={p.x}
                    y={SVG_H - 10}
                    textAnchor="middle"
                    className="text-[9.5px] fill-muted-foreground font-mono"
                  >
                    {idx % labelEvery === 0 || idx === points.length - 1 ? p.time : ''}
                  </text>
                </g>
              ))}
            </svg>
          </div>
        </section>

        {/* Right: AI Vision Class Distribution Donut Chart */}
        <section className="flex flex-col justify-between rounded-xl border border-border bg-card p-4">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers size={15} className="text-purple-500" />
                <h3 className="text-xs font-bold tracking-wider text-foreground">
                  AI Model Class Mix
                </h3>
              </div>
              <span className="rounded bg-muted/40 px-2 py-0.5 text-[10px] font-mono text-muted-foreground">
                {compact(totalDetections)} Inferences
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Distribution across detected object classes</p>
          </div>

          <div className="flex items-center justify-center gap-4 my-2">
            <svg width={DONUT_SIZE} height={DONUT_SIZE} className="overflow-visible">
              <g transform={`rotate(-90 ${DONUT_SIZE / 2} ${DONUT_SIZE / 2})`}>
                {donutSlices.map((slice) => (
                  <circle
                    key={slice.idx}
                    cx={DONUT_SIZE / 2}
                    cy={DONUT_SIZE / 2}
                    r={DONUT_R}
                    fill="none"
                    stroke={slice.color}
                    strokeWidth={20}
                    strokeDasharray={slice.strokeDasharray}
                    strokeDashoffset={slice.strokeDashoffset}
                    className="transition-all hover:opacity-80"
                  />
                ))}
              </g>
              {/* Inner label */}
              <text x="50%" y="48%" textAnchor="middle" className="fill-foreground font-mono font-bold text-base">
                {compact(totalDetections)}
              </text>
              <text x="50%" y="62%" textAnchor="middle" className="fill-muted-foreground text-[9px] font-semibold">
                Detections
              </text>
            </svg>

            {/* Compact Legend */}
            <div className="flex flex-col gap-1.5 text-xs flex-1 min-w-0">
              {classDistribution.map((c, i) => (
                <div key={i} className="flex items-center justify-between text-[11px]">
                  <div className="flex items-center gap-1.5 truncate">
                    <span className="size-2 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
                    <span className="truncate text-foreground font-medium">{c.name}</span>
                  </div>
                  <span className="font-mono font-bold text-muted-foreground shrink-0">{c.pct}%</span>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-border/60 pt-2 flex items-center justify-between text-[11px]">
            <span className="text-muted-foreground">Pipeline Health</span>
            <span className="text-success font-semibold flex items-center gap-1">
              <ShieldCheck size={12} /> All Models Active
            </span>
          </div>
        </section>
      </div>

      {/* ── 3. CLUSTERS HEALTH & ACTIVE HARDWARE NODES MATRIX ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Left: Clusters Quick Health */}
        <section className="flex flex-col rounded-xl border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Network size={15} className="text-brand" />
              <h3 className="text-xs font-bold tracking-wider text-foreground">
                Cluster Health Status ({clusters.length})
              </h3>
            </div>
            <Link to="/agent/clusters" className="flex items-center gap-1 text-xs font-semibold text-brand hover:underline">
              <span>View Topology</span>
              <ArrowRight size={12} />
            </Link>
          </div>

          <div className="flex flex-col gap-2.5">
            {clusters.map((c) => (
              <Link
                key={c.id}
                to={`/agent/clusters/${c.id}`}
                className="flex items-center justify-between rounded-lg border border-border bg-muted/15 p-3 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <span className={`size-2.5 rounded-full ${c.status === 'healthy' ? 'bg-success' : 'bg-warning'}`} />
                  <div>
                    <div className="text-xs font-bold text-foreground">{c.name}</div>
                    <div className="text-[10.5px] text-muted-foreground">{c.site} · {c.nodes.length} Nodes</div>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs font-mono">
                  <div>
                    <span className="text-muted-foreground text-[10px] block">Cameras</span>
                    <strong className="text-foreground">{c.onlineCameras}/{c.totalCameras}</strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground text-[10px] block">Agg FPS</span>
                    <strong className="text-success">{c.aggregateFps}</strong>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* Right: Live Edge Hardware Nodes */}
        <section className="flex flex-col rounded-xl border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Cpu size={15} className="text-info" />
              <h3 className="text-xs font-bold tracking-wider text-foreground">
                Active Edge Node Agents ({clusters.flatMap(c => c.nodes).length})
              </h3>
            </div>
            <Link to="/agent/nodes" className="flex items-center gap-1 text-xs font-semibold text-brand hover:underline">
              <span>View All Nodes</span>
              <ArrowRight size={12} />
            </Link>
          </div>

          <div className="flex flex-col gap-2.5">
            {clusters.flatMap(c => c.nodes).slice(0, 3).map((n) => (
              <Link
                key={n.id}
                to={`/agent/nodes/${n.id}`}
                className="flex items-center justify-between rounded-lg border border-border bg-muted/15 p-3 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <span className={`size-2 rounded-full ${n.status === 'online' ? 'bg-success animate-pulse' : 'bg-warning'}`} />
                  <div>
                    <div className="text-xs font-bold text-foreground">{n.name}</div>
                    <div className="text-[10.5px] text-muted-foreground font-mono">{n.hardware} · {n.ip}</div>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs font-mono">
                  <div>
                    <span className="text-muted-foreground text-[10px] block">CPU</span>
                    <strong className="text-foreground">{n.cpuUsage}%</strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground text-[10px] block">GPU</span>
                    <strong className="text-foreground">{n.gpuUsage}%</strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground text-[10px] block">Cameras</span>
                    <strong className="text-info">{n.cameras.length}</strong>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>

      {/* ── 4. CAMERA SENSORS & INGESTION TELEMETRY ── */}
      <section className="rounded-xl border border-border bg-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <Camera size={15} className="text-purple-500" />
            <h3 className="text-xs font-bold tracking-wider text-foreground">
              Edge Camera Ingestion &amp; Sensors ({onlineCameras}/{totalCameras} Active)
            </h3>
            <span className="flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[10px] font-bold text-success">
              <span className="size-1.5 rounded-full bg-success" />
              RTSP INGESTION STABLE
            </span>
          </div>

          <Link
            to="/agent/cameras"
            className="flex items-center gap-1 text-xs font-semibold text-brand hover:underline"
          >
            <span>Manage All Cameras ({allCameras.length})</span>
            <ArrowRight size={12} />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {allCameras.slice(0, 4).map((cam) => (
            <Link
              key={cam.id}
              to="/agent/cameras"
              className="flex flex-col justify-between rounded-lg border border-border bg-muted/15 p-3.5 hover:border-brand/40 hover:bg-muted/30 transition-all"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`size-2 rounded-full shrink-0 ${cam.online ? 'bg-success' : 'bg-muted-foreground'}`} />
                    <span className="text-xs font-bold text-foreground truncate">{cam.name}</span>
                  </div>
                  <div className="text-[11px] text-muted-foreground font-medium mt-0.5 truncate">
                    Zone: <span className="text-foreground">{cam.zone}</span>
                  </div>
                </div>

                {cam.alertCount > 0 ? (
                  <span className="flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-[10px] font-bold text-destructive shrink-0">
                    <AlertTriangle size={10} />
                    {cam.alertCount}
                  </span>
                ) : (
                  <span className="flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[10px] font-bold text-success shrink-0">
                    <CheckCircle size={10} />
                    OK
                  </span>
                )}
              </div>

              <div className="mt-3 flex items-center justify-between border-t border-border/50 pt-2 text-[11px] font-mono text-muted-foreground">
                <span className="truncate">{cam.clusterName}</span>
                <span className="font-bold text-foreground shrink-0">{cam.fps} FPS · {cam.resolution}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── 5. PRODUCTION PIPELINE: Model Registry & Workload ── */}
      <section className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Rocket size={15} className="text-brand" />
            <h3 className="text-xs font-bold tracking-wider text-foreground">
              Edge AI Models &amp; Workload
            </h3>
          </div>
          <Link to="/models/registry" className="flex items-center gap-1 text-xs font-semibold text-brand hover:underline">
            <span>Manage Models</span>
            <ArrowRight size={12} />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {deployments.map((dep) => (
            <div key={dep.id} className="flex flex-col justify-between rounded-lg border border-border bg-muted/10 p-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs font-bold text-foreground">{dep.modelName}</div>
                  <div className="text-[10.5px] text-muted-foreground font-mono">{dep.modelVersion} · {dep.targetDevices.length} nodes · {dep.strategy}</div>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[9.5px] font-bold ${
                  dep.status === 'Active' ? 'bg-success/10 text-success'
                    : dep.status === 'Failed' ? 'bg-destructive/10 text-destructive'
                      : 'bg-brand/10 text-brand'
                }`}>
                  {dep.status === 'Active' ? 'Active Ingestion' : dep.status === 'In Progress' ? `Syncing ${dep.progressPct}%` : dep.status}
                </span>
              </div>
              <div className="mt-3">
                <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-700 ${dep.status === 'Active' ? 'bg-success' : 'bg-brand'}`} style={{ width: `${dep.progressPct}%` }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
