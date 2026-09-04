import { useState, useEffect, useId } from 'react'
import { Link } from 'react-router-dom'
import {
  Cpu,
  Camera,
  Boxes,
  Rocket,
  AlertTriangle,
  Activity,
  ArrowRight,
  Radio,
  Zap,
  Truck,
  ShieldAlert,
  Heart,
} from 'lucide-react'
import KpiCard from '@/components\KpiCard'
import { mockDevices, type EdgeDevice } from '@/mock\fleet'
import { mockCameras } from '@/mock\cameras'
import { mockDeployments } from '@/mock\ai'
import { mockIncidents } from '@/mock\incidents'

// Initial seed data for rolling telemetry (16 points)
const INITIAL_POINTS = Array.from({ length: 16 }, (_, i) => {
  const d = new Date(Date.now() - (15 - i) * 2000)
  const time = d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  return {
    time,
    fps: Number((119 + Math.sin(i * 0.8) * 3 + (Math.random() * 2 - 1)).toFixed(1)),
    latency: Number((32 + Math.cos(i * 0.7) * 3 + (Math.random() * 1.5 - 0.75)).toFixed(1)),
    detections: Math.floor(46 + Math.sin(i * 0.6) * 8 + Math.random() * 4),
  }
})

type ChartMetric = 'fps' | 'latency' | 'detections'

const DETECTION_CLASSES = [
  { name: 'Person / Worker', pct: 42, count: 6254, color: '#ee0033' },
  { name: 'Safety Vest', pct: 24, count: 3574, color: '#10b981' },
  { name: 'Hard Hat', pct: 18, count: 2680, color: '#f59e0b' },
  { name: 'Forklift / Machinery', pct: 10, count: 1489, color: '#8b5cf6' },
  { name: 'Zone Intrusion', pct: 6, count: 895, color: '#b91c1c' },
]

export default function Overview() {
  const isLive = true
  const [activeMetric, setActiveMetric] = useState<ChartMetric>('fps')
  const [telemetry, setTelemetry] = useState(INITIAL_POINTS)
  const [totalDetections, setTotalDetections] = useState(14892)
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const [hoveredClass, setHoveredClass] = useState<number | null>(null)
  const [deviceStats, setDeviceStats] = useState<EdgeDevice[]>(mockDevices)

  const gradId = useId()

  // Real-time telemetry simulation interval
  useEffect(() => {
    if (!isLive) return

    const timer = setInterval(() => {
      const now = new Date()
      const timeStr = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })

      const newFps = Number((120.5 + (Math.random() * 4 - 2)).toFixed(1))
      const newLatency = Number((31.2 + (Math.random() * 3 - 1.5)).toFixed(1))
      const newDetections = Math.floor(48 + Math.random() * 8)

      setTelemetry((prev) => {
        const next = [...prev.slice(1), { time: timeStr, fps: newFps, latency: newLatency, detections: newDetections }]
        return next
      })

      setTotalDetections((prev) => prev + Math.floor(Math.random() * 3 + 1))

      // Subtle real-time fluctuation in device GPU/CPU load
      setDeviceStats((prev) =>
        prev.map((d) => {
          const deltaGpu = Math.floor(Math.random() * 3 - 1)
          const deltaCpu = Math.floor(Math.random() * 3 - 1)
          return {
            ...d,
            gpuUsage: Math.min(96, Math.max(30, d.gpuUsage + deltaGpu)),
            cpuUsage: Math.min(92, Math.max(20, d.cpuUsage + deltaCpu)),
          }
        })
      )
    }, 1600)

    return () => clearInterval(timer)
  }, [isLive])

  // Compute metrics for the active stream
  const currentMetricValues = telemetry.map((p) => p[activeMetric])
  const minVal = Math.min(...currentMetricValues)
  const maxVal = Math.max(...currentMetricValues)
  const avgVal = Number((currentMetricValues.reduce((a, b) => a + b, 0) / currentMetricValues.length).toFixed(1))

  const metricMeta = {
    fps: { label: 'Fleet Throughput', unit: 'FPS', color: '#ee0033', secondary: '#f87171' },
    latency: { label: 'AI Inference Latency', unit: 'ms', color: '#10b981', secondary: '#34d399' },
    detections: { label: 'Detection Velocity', unit: 'objs/s', color: '#8b5cf6', secondary: '#a78bfa' },
  }[activeMetric]

  // SVG Area Chart geometry
  const SVG_W = 680
  const SVG_H = 220
  const PAD_L = 36
  const PAD_R = 24
  const PAD_T = 24
  const PAD_B = 34

  const range = Math.max(maxVal - minVal, 1)
  const stepX = (SVG_W - PAD_L - PAD_R) / (telemetry.length - 1)

  const points = telemetry.map((pt, i) => {
    const val = pt[activeMetric]
    const x = PAD_L + i * stepX
    const y = SVG_H - PAD_B - ((val - minVal) / range) * (SVG_H - PAD_T - PAD_B)
    return { x, y, val, time: pt.time }
  })

  // Smooth cubic bezier spline generator
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
  const DONUT_SIZE = 170
  const DONUT_R = 64
  const DONUT_STROKE = 22
  const CIRCUMFERENCE = 2 * Math.PI * DONUT_R

  let cumulativePct = 0
  const donutSlices = DETECTION_CLASSES.map((item, idx) => {
    const strokeDasharray = `${(item.pct / 100) * CIRCUMFERENCE} ${CIRCUMFERENCE}`
    const strokeDashoffset = -((cumulativePct / 100) * CIRCUMFERENCE)
    cumulativePct += item.pct
    return { ...item, strokeDasharray, strokeDashoffset, idx }
  })

  const onlineDevices = deviceStats.filter((d) => d.status === 'online').length
  const onlineCameras = mockCameras.filter((c) => c.online).length
  const criticalAlerts = mockIncidents.filter((i) => i.severity === 'critical').length

  return (
    <div>
      {/* KPI Overview Cards matching reference image */}
      <div className="av-kpi-row">
        <KpiCard
          label="Total Detections"
          value={totalDetections.toLocaleString()}
          sub="Real-time Stream"
          icon={<Activity size={22} />}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#2563eb"
          deltaText="12.8% vs last hr"
          isUp={true}
          chartType="sparkline"
          chartColor="#2563eb"
          chartData={[12, 16, 14, 22, 18, 28, 22, 30]}
        />
        <KpiCard
          label="Edge Fleet"
          value={`${onlineDevices} / ${deviceStats.length}`}
          sub="Nodes Active"
          icon={<Truck size={22} />}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
          deltaText="0% vs last hr"
          isUp={true}
          chartType="sparkline"
          chartColor="#10b981"
          chartData={[18, 22, 19, 25, 23, 29, 24, 28]}
        />
        <KpiCard
          label="Live Cameras"
          value={`${onlineCameras} / ${mockCameras.length}`}
          sub="30 FPS avg"
          icon={<Camera size={22} />}
          iconBg="rgba(168, 85, 247, 0.12)"
          iconColor="#9333ea"
          deltaText="2.4% vs last hr"
          isUp={true}
          chartType="sparkline"
          chartColor="#9333ea"
          chartData={[10, 16, 13, 22, 18, 26, 23, 29]}
        />
        <KpiCard
          label="Inference Latency"
          value={`${telemetry[telemetry.length - 1].latency} ms`}
          sub="TensorRT FP16"
          icon={<Zap size={22} />}
          iconBg="rgba(245, 158, 11, 0.14)"
          iconColor="#d97706"
          deltaText="4.1% vs last hr"
          isUp={false}
          chartType="sparkline"
          chartColor="#f59e0b"
          chartData={[22, 26, 19, 28, 22, 29, 25, 31]}
        />
        <KpiCard
          label="Security Incidents"
          value={String(mockIncidents.length)}
          badge={`${criticalAlerts} critical`}
          sub="Facility Safety"
          icon={<ShieldAlert size={22} />}
          iconBg="rgba(239, 68, 68, 0.12)"
          iconColor="#ef4444"
          deltaText="15% vs last hr"
          isUp={false}
          chartType="bars"
          chartColor="#ef4444"
          chartData={[6, 12, 18, 10, 16, 26, 22]}
        />
        <KpiCard
          label="Fleet Health"
          value="99.4%"
          sub="Optimal Status"
          icon={<Heart size={22} />}
          iconBg="rgba(56, 189, 248, 0.14)"
          iconColor="#0284c7"
          deltaText="0.8% vs last hr"
          isUp={true}
          chartType="bars"
          chartColor="#38bdf8"
          chartData={[20, 22, 24, 21, 23, 25, 22, 24, 26, 25, 23, 26]}
        />
        <KpiCard
          label="Bandwidth Usage"
          value="1.42 GB/s"
          sub="Edge to Cloud"
          icon={<Radio size={22} />}
          iconBg="rgba(236, 72, 153, 0.12)"
          iconColor="#ec4899"
          deltaText="1.2% vs last hr"
          isUp={true}
          chartType="sparkline"
          chartColor="#ec4899"
          chartData={[12, 14, 13, 16, 15, 18, 14, 15]}
        />
        <KpiCard
          label="Avg GPU Load"
          value="78%"
          sub="Compute Capacity"
          icon={<Cpu size={22} />}
          iconBg="rgba(14, 165, 233, 0.12)"
          iconColor="#0ea5e9"
          deltaText="4.5% vs last hr"
          isUp={true}
          chartType="sparkline"
          chartColor="#0ea5e9"
          chartData={[65, 68, 70, 62, 75, 74, 76, 78]}
        />
      </div>

      {/* Hero Visual Real-Time Charts (2-Column Grid) */}
      <div className="av-chart-hero-grid">
        {/* Chart 1: Real-Time Performance Spline Area Chart */}
        <section className="av-panel">
          <div className="av-panel-header" style={{ flexWrap: 'wrap', gap: 10 }}>
            <div>
              <span className="av-panel-title">
                <Activity size={16} />
                <span>Real-Time Fleet Telemetry Stream</span>
              </span>
              <div style={{ fontSize: 11.5, color: 'var(--text-faint)', marginTop: 2 }}>
                Live time-series window ({telemetry[0].time} → {lastPt.time})
              </div>
            </div>

            {/* Metric Switcher Tabs */}
            <div style={{ display: 'flex', gap: 6, background: 'var(--panel-2)', padding: 3, borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
              <button
                className={`av-btn${activeMetric === 'fps' ? ' av-btn-primary' : ' av-btn-secondary'}`}
                onClick={() => setActiveMetric('fps')}
                style={{ fontSize: 11, padding: '4px 9px', borderRadius: 'var(--radius-sm)' }}
              >
                Throughput (FPS)
              </button>
              <button
                className={`av-btn${activeMetric === 'latency' ? ' av-btn-primary' : ' av-btn-secondary'}`}
                onClick={() => setActiveMetric('latency')}
                style={{ fontSize: 11, padding: '4px 9px', borderRadius: 'var(--radius-sm)' }}
              >
                Latency (ms)
              </button>
              <button
                className={`av-btn${activeMetric === 'detections' ? ' av-btn-primary' : ' av-btn-secondary'}`}
                onClick={() => setActiveMetric('detections')}
                style={{ fontSize: 11, padding: '4px 9px', borderRadius: 'var(--radius-sm)' }}
              >
                Detections/s
              </button>
            </div>
          </div>

          <div className="av-panel-body" style={{ padding: '16px 20px 20px' }}>
            {/* Live Stats Strip */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span className="av-mono" style={{ fontSize: 26, fontWeight: 800, color: metricMeta.color }}>
                  {activePoint.val}
                </span>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-dim)' }}>
                  {metricMeta.unit}
                </span>
                <span className="av-mono" style={{ fontSize: 11.5, color: 'var(--text-faint)', marginLeft: 8 }}>
                  at {activePoint.time}
                </span>
              </div>

              <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
                <div>
                  <span style={{ color: 'var(--text-faint)' }}>Min: </span>
                  <strong className="av-mono">{minVal} {metricMeta.unit}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-faint)' }}>Avg: </span>
                  <strong className="av-mono">{avgVal} {metricMeta.unit}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-faint)' }}>Max: </span>
                  <strong className="av-mono">{maxVal} {metricMeta.unit}</strong>
                </div>
              </div>
            </div>

            {/* SVG Spline Chart */}
            <div style={{ width: '100%', position: 'relative' }}>
              <svg
                width="100%"
                viewBox={`0 0 ${SVG_W} ${SVG_H}`}
                style={{ overflow: 'visible', display: 'block' }}
                role="img"
                aria-label="Real-time telemetry chart"
              >
                <defs>
                  <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={metricMeta.color} stopOpacity={0.32} />
                    <stop offset="100%" stopColor={metricMeta.color} stopOpacity={0.0} />
                  </linearGradient>
                </defs>

                {/* Horizontal Grid lines */}
                {[0, 0.33, 0.66, 1].map((ratio, i) => {
                  const y = PAD_T + ratio * (SVG_H - PAD_T - PAD_B)
                  return (
                    <line
                      key={i}
                      x1={PAD_L}
                      y1={y}
                      x2={SVG_W - PAD_R}
                      y2={y}
                      stroke="var(--border)"
                      strokeDasharray="4 4"
                      strokeWidth={1}
                      opacity={0.6}
                    />
                  )
                })}

                {/* Area Gradient Fill */}
                <path d={areaPath} fill={`url(#${gradId})`} />

                {/* Smooth Curve Line */}
                <path
                  d={smoothPath}
                  fill="none"
                  stroke={metricMeta.color}
                  strokeWidth={2.6}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Pulsing latest real-time dot */}
                {isLive && (
                  <>
                    <circle
                      cx={lastPt.x}
                      cy={lastPt.y}
                      r={7}
                      fill="none"
                      stroke={metricMeta.color}
                      strokeWidth={1.5}
                      opacity={0.7}
                    >
                      <animate
                        attributeName="r"
                        values="4;12;4"
                        dur="1.8s"
                        repeatCount="indefinite"
                      />
                      <animate
                        attributeName="opacity"
                        values="0.8;0;0.8"
                        dur="1.8s"
                        repeatCount="indefinite"
                      />
                    </circle>
                    <circle
                      cx={lastPt.x}
                      cy={lastPt.y}
                      r={4.5}
                      fill={metricMeta.color}
                      stroke="#ffffff"
                      strokeWidth={2}
                    />
                  </>
                )}

                {/* Hover crosshair */}
                {hoveredIndex !== null && (
                  <>
                    <line
                      x1={points[hoveredIndex].x}
                      y1={PAD_T}
                      x2={points[hoveredIndex].x}
                      y2={SVG_H - PAD_B}
                      stroke="var(--accent)"
                      strokeWidth={1.5}
                      strokeDasharray="3 3"
                    />
                    <circle
                      cx={points[hoveredIndex].x}
                      cy={points[hoveredIndex].y}
                      r={5}
                      fill="var(--accent)"
                      stroke="#ffffff"
                      strokeWidth={2}
                    />
                  </>
                )}

                {/* Interactive hover capture columns */}
                {points.map((p, i) => (
                  <rect
                    key={i}
                    x={p.x - stepX / 2}
                    y={PAD_T}
                    width={stepX}
                    height={SVG_H - PAD_T - PAD_B}
                    fill="transparent"
                    style={{ cursor: 'pointer' }}
                    onMouseEnter={() => setHoveredIndex(i)}
                    onMouseLeave={() => setHoveredIndex(null)}
                  />
                ))}

                {/* X-Axis timestamps */}
                {points
                  .filter((_, i) => i % 3 === 0 || i === points.length - 1)
                  .map((p, i) => (
                    <text
                      key={i}
                      x={p.x}
                      y={SVG_H - 10}
                      textAnchor="middle"
                      fill="var(--text-faint)"
                      fontSize={10.5}
                      fontFamily="var(--font-mono)"
                    >
                      {p.time.slice(3)}
                    </text>
                  ))}
              </svg>
            </div>
          </div>
        </section>

        {/* Chart 2: Real-Time Detection Class Donut Breakdown */}
        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Boxes size={16} />
              <span>Real-Time Detection Breakdown</span>
            </span>
            <span className="av-status-pill reviewed" style={{ fontSize: 10.5 }}>
              Active Model
            </span>
          </div>

          <div className="av-panel-body" style={{ padding: '16px 18px 20px' }}>
            <div className="av-donut-container">
              {/* SVG Donut Circle */}
              <div style={{ position: 'relative', width: DONUT_SIZE, height: DONUT_SIZE, flexShrink: 0 }}>
                <svg width={DONUT_SIZE} height={DONUT_SIZE} viewBox={`0 0 ${DONUT_SIZE} ${DONUT_SIZE}`}>
                  <g transform={`rotate(-90 ${DONUT_SIZE / 2} ${DONUT_SIZE / 2})`}>
                    {/* Background Track Ring */}
                    <circle
                      cx={DONUT_SIZE / 2}
                      cy={DONUT_SIZE / 2}
                      r={DONUT_R}
                      fill="none"
                      stroke="var(--panel-2)"
                      strokeWidth={DONUT_STROKE}
                    />

                    {/* Colored Donut Slices */}
                    {donutSlices.map((slice) => {
                      const isSelected = hoveredClass === slice.idx
                      return (
                        <circle
                          key={slice.idx}
                          cx={DONUT_SIZE / 2}
                          cy={DONUT_SIZE / 2}
                          r={DONUT_R}
                          fill="none"
                          stroke={slice.color}
                          strokeWidth={isSelected ? DONUT_STROKE + 4 : DONUT_STROKE}
                          strokeDasharray={slice.strokeDasharray}
                          strokeDashoffset={slice.strokeDashoffset}
                          strokeLinecap="round"
                          style={{
                            transition: 'stroke-width 0.2s ease, opacity 0.2s ease',
                            cursor: 'pointer',
                            opacity: hoveredClass === null || isSelected ? 1 : 0.5,
                          }}
                          onMouseEnter={() => setHoveredClass(slice.idx)}
                          onMouseLeave={() => setHoveredClass(null)}
                        />
                      )
                    })}
                  </g>
                </svg>

                {/* Center Readout */}
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    pointerEvents: 'none',
                  }}
                >
                  <span className="av-mono" style={{ fontSize: 18, fontWeight: 800, color: 'var(--text)' }}>
                    {hoveredClass !== null ? `${DETECTION_CLASSES[hoveredClass].pct}%` : `${totalDetections.toLocaleString()}`}
                  </span>
                  <span style={{ fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {hoveredClass !== null ? DETECTION_CLASSES[hoveredClass].name.split(' ')[0] : 'Total Live'}
                  </span>
                </div>
              </div>

              {/* Legend List */}
              <div className="av-donut-legend">
                {DETECTION_CLASSES.map((item, idx) => (
                  <div
                    key={idx}
                    className="av-donut-legend-item"
                    style={{
                      borderColor: hoveredClass === idx ? item.color : undefined,
                      background: hoveredClass === idx ? 'var(--panel)' : undefined,
                      cursor: 'pointer',
                    }}
                    onMouseEnter={() => setHoveredClass(idx)}
                    onMouseLeave={() => setHoveredClass(null)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ width: 9, height: 9, borderRadius: '50%', background: item.color, flexShrink: 0 }} />
                      <span style={{ fontSize: 12, fontWeight: 600 }}>{item.name}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="av-mono" style={{ fontSize: 11, color: 'var(--text-faint)' }}>
                        {item.count.toLocaleString()}
                      </span>
                      <span className="av-mono" style={{ fontSize: 12, fontWeight: 700, color: item.color }}>
                        {item.pct}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Middle Grid: Edge Fleet Real-Time Load Meters & Live Cameras Matrix */}
      <div className="av-overview-split" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* Real-Time Edge Devices Compute Meters */}
        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Cpu size={16} />
              <span>Edge Hardware Live Telemetry</span>
            </span>
            <Link to="/fleet/devices" className="av-link-action" style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span>Fleet View</span>
              <ArrowRight size={13} />
            </Link>
          </div>
          <div className="av-panel-body">
            <div className="av-meter-list">
              {deviceStats.map((dev) => {
                const isDegraded = dev.status === 'degraded'
                return (
                  <div key={dev.id} className="av-meter-card">
                    <div className="av-meter-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className={`av-dot ${dev.status === 'online' ? 'good' : isDegraded ? 'warning' : 'critical'}`} />
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 700 }}>{dev.name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-faint)' }}>{dev.hardware} • {dev.ip}</div>
                        </div>
                      </div>
                      <span className={`av-status-pill ${dev.status === 'online' ? 'reviewed' : isDegraded ? 'in-progress' : 'escalated'}`}>
                        {dev.status.toUpperCase()}
                      </span>
                    </div>

                    <div className="av-meter-gauges">
                      <div className="av-gauge-sub">
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                          <span style={{ color: 'var(--text-faint)' }}>GPU Load</span>
                          <span className="av-mono" style={{ fontWeight: 700, color: dev.gpuUsage > 80 ? 'var(--critical)' : 'var(--text)' }}>
                            {dev.gpuUsage}%
                          </span>
                        </div>
                        <div className="av-telemetry-bar-track" style={{ height: 5 }}>
                          <div
                            className={`av-telemetry-bar-fill${dev.gpuUsage > 80 ? ' crit' : dev.gpuUsage > 65 ? ' warn' : ''}`}
                            style={{ width: `${dev.gpuUsage}%` }}
                          />
                        </div>
                      </div>

                      <div className="av-gauge-sub">
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                          <span style={{ color: 'var(--text-faint)' }}>CPU Load</span>
                          <span className="av-mono" style={{ fontWeight: 700, color: dev.cpuUsage > 80 ? 'var(--critical)' : 'var(--text)' }}>
                            {dev.cpuUsage}%
                          </span>
                        </div>
                        <div className="av-telemetry-bar-track" style={{ height: 5 }}>
                          <div
                            className={`av-telemetry-bar-fill${dev.cpuUsage > 80 ? ' crit' : dev.cpuUsage > 65 ? ' warn' : ''}`}
                            style={{ width: `${dev.cpuUsage}%` }}
                          />
                        </div>
                      </div>

                      <div className="av-gauge-sub">
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                          <span style={{ color: 'var(--text-faint)' }}>Core Temp</span>
                          <span className="av-mono" style={{ fontWeight: 700, color: dev.tempC > 60 ? 'var(--warning)' : 'var(--text)' }}>
                            {dev.tempC}°C
                          </span>
                        </div>
                        <div className="av-telemetry-bar-track" style={{ height: 5 }}>
                          <div
                            className={`av-telemetry-bar-fill${dev.tempC > 60 ? ' warn' : ''}`}
                            style={{ width: `${(dev.tempC / 85) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        {/* Live Camera Stream Previews */}
        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Camera size={16} />
              <span>Camera Fleet Real-Time Streams</span>
            </span>
            <Link to="/fleet/cameras" className="av-link-action" style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span>View All ({mockCameras.length})</span>
              <ArrowRight size={13} />
            </Link>
          </div>
          <div className="av-panel-body">
            <div className="av-camera-matrix-grid">
              {mockCameras.slice(0, 4).map((cam) => (
                <div key={cam.id} className="av-camera-hud-card">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Radio size={13} color={cam.online ? 'var(--good)' : 'var(--critical)'} />
                      <span style={{ fontSize: 12.5, fontWeight: 700 }}>{cam.id}</span>
                    </div>
                    <span className={`av-alert-pill${cam.alertCount > 0 ? ' has-alerts' : ''}`} style={{ fontSize: 10 }}>
                      {cam.alertCount > 0 ? `${cam.alertCount} ALERTS` : 'NORMAL'}
                    </span>
                  </div>

                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{cam.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-faint)' }}>{cam.zone}</div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border)', paddingTop: 8, marginTop: 4 }}>
                    <span className="av-mono" style={{ fontSize: 11, color: 'var(--accent)', fontWeight: 600 }}>
                      {cam.runtime.model.split('-')[0]}
                    </span>
                    <span className="av-mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                      {cam.runtime.fps} FPS • {cam.runtime.resolution}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      {/* Bottom Section: Active Deployments Pipeline & Security Incidents */}
      <div className="av-overview-split" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20 }}>
        {/* Model Rollout Pipeline */}
        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Rocket size={16} />
              <span>Active Model Deployments</span>
            </span>
            <Link to="/ai/deployments" className="av-link-action" style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span>Manage Pipelines</span>
              <ArrowRight size={13} />
            </Link>
          </div>
          <div className="av-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {mockDeployments.map((dep) => (
              <div key={dep.id} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, fontWeight: 600 }}>
                  <span>
                    {dep.modelName} <span className="av-mono" style={{ color: 'var(--text-faint)', fontSize: 11.5 }}>{dep.modelVersion}</span>
                  </span>
                  <span className={`av-status-pill ${dep.status === 'Active' ? 'reviewed' : dep.status === 'In Progress' ? 'new' : 'escalated'}`}>
                    {dep.status}
                  </span>
                </div>
                <div className="av-telemetry-bar-track" style={{ height: 6 }}>
                  <div
                    className={`av-telemetry-bar-fill${dep.status === 'Failed' ? ' crit' : ''}`}
                    style={{ width: `${dep.progressPct}%` }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-faint)' }}>
                  <span>Target: {dep.targetDevices.join(', ')}</span>
                  <span>{dep.progressPct}% • {dep.strategy}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Real-Time Security Incidents Feed */}
        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <AlertTriangle size={16} />
              <span>Live Security & Safety Alerts</span>
            </span>
            <Link to="/observability/alerts" className="av-link-action" style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span>Triage Center</span>
              <ArrowRight size={13} />
            </Link>
          </div>
          <div className="av-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {mockIncidents.slice(0, 4).map((inc) => (
              <div
                key={inc.id}
                style={{
                  display: 'flex',
                  gap: 12,
                  padding: '11px 13px',
                  background: 'var(--panel-2)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  alignItems: 'center',
                }}
              >
                <span className={`av-dot ${inc.severity === 'critical' ? 'critical' : inc.severity === 'warning' ? 'warning' : 'good'}`} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                    <span style={{ fontWeight: 700 }}>{inc.event}</span>
                    <span className="av-mono" style={{ fontSize: 11, color: 'var(--text-faint)' }}>{inc.time}</span>
                  </div>
                  <div style={{ fontSize: 11.5, color: 'var(--text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {inc.camera} • Person {inc.personId}
                  </div>
                </div>
                <span className={`av-status-pill ${inc.status === 'Reviewed' ? 'reviewed' : inc.status === 'New' ? 'new' : 'escalated'}`} style={{ fontSize: 10 }}>
                  {inc.status}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

