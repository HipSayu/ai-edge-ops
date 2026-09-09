import { useState, useEffect, useId } from 'react'
import {
  Cpu,
  Camera,
  Boxes,
  Rocket,
  Activity,
  Radio,
  Zap,
  Truck,
  Heart,
} from 'lucide-react'
import KpiCard from '@/shared/components/KpiCard'
import type { EdgeDevice } from '@/modules/agent/types'
import { agentService } from '@/shared/api/services/agent'
import { aiService } from '@/shared/api/services/ai'

type AnalyticsOverview = {
  violations_24h: number
  avg_inference_latency_ms: number | null
}

type ChartMetric = 'fps' | 'latency' | 'detections'

export default function Overview() {
  const [activeMetric, setActiveMetric] = useState<ChartMetric>('fps')
  const [telemetry, setTelemetry] = useState<{ time: string; fps: number; latency: number; detections: number }[]>([])
  const [detectionClasses] = useState<{ name: string; pct: number; count: number; color: string }[]>([])
  const [analyticsOverview, setAnalyticsOverview] = useState<AnalyticsOverview | null>(null)
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const [hoveredClass, setHoveredClass] = useState<number | null>(null)
  const [deviceStats, setDeviceStats] = useState<EdgeDevice[]>([])
  const [cameras, setCameras] = useState<import('@/modules/agent/types').Camera[]>([])
  const [deployments, setDeployments] = useState<import('@/modules/ai/types').Deployment[]>([])

  const gradId = useId()

  useEffect(() => {
    agentService.listDevices().then(async (devices) => {
      setDeviceStats(devices)
      const metrics = (await Promise.all(devices.map((device) => agentService.listDeviceMetrics(device.id))))
        .flat()
        .sort((a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime())
      setTelemetry(metrics.map((metric) => ({
        time: new Date(metric.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        fps: metric.fps ?? 0,
        latency: metric.inference_latency_ms ?? 0,
        detections: 0,
      })))
    }).catch(() => { setDeviceStats([]); setTelemetry([]) })
    agentService.listCameras().then(setCameras).catch(() => setCameras([]))
    aiService.listDeployments().then(setDeployments).catch(() => setDeployments([]))
    setAnalyticsOverview({ violations_24h: 0, avg_inference_latency_ms: null })
  }, [])

  // Compute metrics for the active stream
  const chartTelemetry = telemetry.length ? telemetry : [{ time: 'No data', fps: 0, latency: 0, detections: 0 }]
  const currentMetricValues = chartTelemetry.map((p) => p[activeMetric])
  const minVal = Math.min(...currentMetricValues)
  const maxVal = Math.max(...currentMetricValues)
  const avgVal = Number((currentMetricValues.reduce((a, b) => a + b, 0) / currentMetricValues.length).toFixed(1))

  const metricMeta = {
    fps: { label: 'Agent Throughput', unit: 'FPS', color: '#ee0033', secondary: '#f87171' },
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
  const stepX = (SVG_W - PAD_L - PAD_R) / Math.max(chartTelemetry.length - 1, 1)

  const points = chartTelemetry.map((pt, i) => {
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
  const donutSlices = detectionClasses.map((item, idx) => {
    const strokeDasharray = `${(item.pct / 100) * CIRCUMFERENCE} ${CIRCUMFERENCE}`
    const strokeDashoffset = -((cumulativePct / 100) * CIRCUMFERENCE)
    cumulativePct += item.pct
    return { ...item, strokeDasharray, strokeDashoffset, idx }
  })

  const onlineDevices = deviceStats.filter((d) => d.status === 'online').length
  const onlineCameras = cameras.filter((c) => c.online).length

  return (
    <div>
      {/* KPI Overview Cards matching reference image */}
      <div className="av-kpi-row">
        <KpiCard
          label="Total Detections"
          value={(analyticsOverview?.violations_24h ?? 0).toLocaleString()}
          sub="Real-time Stream"
          icon={<Activity size={22} />}
          iconBg="rgba(59, 130, 246, 0.12)"
          iconColor="#2563eb"
          deltaText="From backend analytics"
          isUp={true}
          chartType="sparkline"
          chartColor="#2563eb"
          chartData={telemetry.map((point) => point.detections)}
        />
        <KpiCard
          label="Edge Agent"
          value={`${onlineDevices} / ${deviceStats.length}`}
          sub="Nodes Active"
          icon={<Truck size={22} />}
          iconBg="rgba(16, 185, 129, 0.12)"
          iconColor="#10b981"
          deltaText="Current online status"
          isUp={true}
          chartType="sparkline"
          chartColor="#10b981"
          chartData={deviceStats.map((device) => device.cpuUsage)}
        />
        <KpiCard
          label="Live Cameras"
          value={`${onlineCameras} / ${cameras.length}`}
          sub="Backend camera status"
          icon={<Camera size={22} />}
          iconBg="rgba(168, 85, 247, 0.12)"
          iconColor="#9333ea"
          deltaText="Current online status"
          isUp={true}
          chartType="sparkline"
          chartColor="#9333ea"
          chartData={cameras.map((camera) => camera.runtime.fps)}
        />
        <KpiCard
          label="Inference Latency"
          value={analyticsOverview?.avg_inference_latency_ms != null ? `${analyticsOverview.avg_inference_latency_ms.toFixed(1)} ms` : '—'}
          sub="Backend average"
          icon={<Zap size={22} />}
          iconBg="rgba(245, 158, 11, 0.14)"
          iconColor="#d97706"
          deltaText="Backend average"
          isUp={false}
          chartType="sparkline"
          chartColor="#f59e0b"
          chartData={telemetry.map((point) => point.latency)}
        />
        <KpiCard
          label="Agent Health"
          value={deviceStats.length === 0 ? '—' : `${((onlineDevices / deviceStats.length) * 100).toFixed(1)}%`}
          sub="Optimal Status"
          icon={<Heart size={22} />}
          iconBg="rgba(56, 189, 248, 0.14)"
          iconColor="#0284c7"
          deltaText="Online devices"
          isUp={true}
          chartType="bars"
          chartColor="#38bdf8"
          chartData={deviceStats.map((device) => device.status === 'online' ? 1 : 0)}
        />
        <KpiCard
          label="Bandwidth Usage"
          value="—"
          sub="Edge to Cloud"
          icon={<Radio size={22} />}
          iconBg="rgba(236, 72, 153, 0.12)"
          iconColor="#ec4899"
          deltaText="Not provided by backend"
          isUp={true}
          chartType="sparkline"
          chartColor="#ec4899"
          chartData={[]}
        />
        <KpiCard
          label="Avg GPU Load"
          value={deviceStats.length === 0 ? '—' : `${(deviceStats.reduce((sum, device) => sum + device.gpuUsage, 0) / deviceStats.length).toFixed(1)}%`}
          sub="Compute Capacity"
          icon={<Cpu size={22} />}
          iconBg="rgba(14, 165, 233, 0.12)"
          iconColor="#0ea5e9"
          deltaText="Current device average"
          isUp={true}
          chartType="sparkline"
          chartColor="#0ea5e9"
          chartData={deviceStats.map((device) => device.gpuUsage)}
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
                <span>Real-Time Agent Telemetry Stream</span>
              </span>
              <div style={{ fontSize: 11.5, color: 'var(--text-faint)', marginTop: 2 }}>
                Live time-series window ({chartTelemetry[0].time} → {lastPt.time})
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
                {telemetry.length > 0 && (
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
                    {hoveredClass !== null ? `${detectionClasses[hoveredClass].pct.toFixed(1)}%` : `${(analyticsOverview?.violations_24h ?? 0).toLocaleString()}`}
                  </span>
                  <span style={{ fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {hoveredClass !== null ? detectionClasses[hoveredClass].name.split(' ')[0] : 'Total Live'}
                  </span>
                </div>
              </div>

              {/* Legend List */}
              <div className="av-donut-legend">
                {detectionClasses.map((item, idx) => (
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

      {/* Middle Grid: Edge Agent Real-Time Load Meters & Live Cameras Matrix */}
      <div className="av-overview-split" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* Real-Time Edge Devices Compute Meters */}
        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Cpu size={16} />
              <span>Edge Hardware Live Telemetry</span>
            </span>
            <Link to="/agent/devices" className="av-link-action" style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span>Agent View</span>
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
                        {dev.status}
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
              <span>Camera Agent Real-Time Streams</span>
            </span>
            <Link to="/agent/cameras" className="av-link-action" style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span>View All ({cameras.length})</span>
              <ArrowRight size={13} />
            </Link>
          </div>
          <div className="av-panel-body">
            <div className="av-camera-matrix-grid">
              {cameras.slice(0, 4).map((cam) => (
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
            {deployments.map((dep) => (
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

      </div>
    </div>
  )
}

