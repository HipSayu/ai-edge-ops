import { useState } from 'react'
import { Clock, Cpu, HardDrive, Zap, ArrowDownUp } from 'lucide-react'
import { mockMonitoringTimeline } from '@/mock\observability'
import MiniTimeSeries from '@/components\MiniTimeSeries'

export default function MonitoringPage() {
  const [timeRange, setTimeRange] = useState('24h')

  return (
    <div>
      <div className="av-layout-toolbar">
        
        <div className="av-layout-switch">
          {['1h', '6h', '24h', '7d'].map((r) => (
            <button
              key={r}
              className={`av-layout-btn${timeRange === r ? ' active' : ''}`}
              onClick={() => setTimeRange(r)}
            >
              {r.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Primary Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 16, marginTop: 14 }}>
        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Cpu size={14} color="var(--accent)" />
              <span>Fleet GPU Utilization (%)</span>
            </span>
            <span className="av-panel-sub av-mono">Avg: 68%</span>
          </div>
          <MiniTimeSeries
            title="GPU Utilization"
            data={mockMonitoringTimeline.map((d) => ({ time: d.time, value: d.gpuAvg }))}
            color="var(--accent)"
            unit="%"
          />
        </section>

        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Cpu size={14} color="var(--warning)" />
              <span>CPU Core Utilization (%)</span>
            </span>
            <span className="av-panel-sub av-mono">Avg: 42%</span>
          </div>
          <MiniTimeSeries
            title="CPU Core Load"
            data={mockMonitoringTimeline.map((d) => ({ time: d.time, value: d.cpuAvg }))}
            color="var(--warning)"
            unit="%"
          />
        </section>

        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Zap size={14} color="var(--good)" />
              <span>Aggregate Inference Throughput (FPS)</span>
            </span>
            <span className="av-panel-sub av-mono">Mean: 28.5 FPS</span>
          </div>
          <MiniTimeSeries
            title="Inference Speed"
            data={mockMonitoringTimeline.map((d) => ({ time: d.time, value: d.fpsAvg }))}
            color="var(--good)"
            unit=" FPS"
          />
        </section>

        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <Clock size={14} color="var(--critical)" />
              <span>P95 End-to-End Latency (ms)</span>
            </span>
            <span className="av-panel-sub av-mono">P95: 25.4ms</span>
          </div>
          <MiniTimeSeries
            title="P95 Latency"
            data={mockMonitoringTimeline.map((d) => ({ time: d.time, value: d.latencyP95 }))}
            color="var(--critical)"
            unit="ms"
          />
        </section>

        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <HardDrive size={14} color="var(--info)" />
              <span>RAM / Unified Memory (%)</span>
            </span>
            <span className="av-panel-sub av-mono">Avg: 59%</span>
          </div>
          <MiniTimeSeries
            title="Memory Allocated"
            data={mockMonitoringTimeline.map((d) => ({ time: d.time, value: d.ramAvg }))}
            color="var(--info)"
            unit="%"
          />
        </section>

        <section className="av-panel">
          <div className="av-panel-header">
            <span className="av-panel-title">
              <ArrowDownUp size={14} color="#8b5cf6" />
              <span>Network Ingress / Streaming (Mbps)</span>
            </span>
            <span className="av-panel-sub av-mono">Bandwidth: 48 Mbps</span>
          </div>
          <MiniTimeSeries
            title="Network Throughput"
            data={mockMonitoringTimeline.map((d) => ({ time: d.time, value: d.networkMbps }))}
            color="#8b5cf6"
            unit=" Mbps"
          />
        </section>
      </div>
    </div>
  )
}
