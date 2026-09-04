import { useState } from 'react'
import { Zap, Search, Cpu, Camera, Rocket, Shield } from 'lucide-react'
import { mockEvents } from '@/modules/observability/mock/observability'

export default function EventsPage() {
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [severityFilter, setSeverityFilter] = useState('all')

  const filtered = mockEvents.filter((evt) => {
    const matchSearch =
      search === '' ||
      evt.title.toLowerCase().includes(search.toLowerCase()) ||
      evt.details.toLowerCase().includes(search.toLowerCase()) ||
      evt.targetNode.toLowerCase().includes(search.toLowerCase())

    const matchSource = sourceFilter === 'all' || evt.source === sourceFilter
    const matchSeverity = severityFilter === 'all' || evt.severity === severityFilter

    return matchSearch && matchSource && matchSeverity
  })

  function SourceIcon({ source }: { source: string }) {
    switch (source) {
      case 'Edge Device':
        return <Cpu size={14} />
      case 'Camera':
        return <Camera size={14} />
      case 'Deployment':
        return <Rocket size={14} />
      case 'Security':
        return <Shield size={14} />
      default:
        return <Zap size={14} />
    }
  }

  return (
    <div className="av-page-layout">
      

      {/* Filter and Search Bar */}
      <section className="av-page-header av-panel" style={{ marginBottom: 0 }}>
        <div className="av-filter-row">
          <div className="av-search-box">
            <Search size={14} color="var(--text-faint)" />
            <input
              type="text"
              placeholder="Search events by title, target node, or details..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
            <option value="all">All Event Sources</option>
            <option value="AI Inference">AI Inference</option>
            <option value="Edge Device">Edge Device</option>
            <option value="Camera">Camera Stream</option>
            <option value="Deployment">Deployment</option>
            <option value="Security">Security</option>
          </select>

          <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="success">Success</option>
            <option value="info">Info</option>
          </select>
        </div>
      </section>

      {/* Events Timeline */}
      <div className="av-page-content">
        <div className="av-panel" style={{ padding: 22 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {filtered.map((evt, idx) => (
            <div
              key={evt.id}
              style={{
                display: 'flex',
                gap: 16,
                position: 'relative',
                paddingBottom: idx === filtered.length - 1 ? 0 : 16,
                borderBottom: idx === filtered.length - 1 ? 'none' : '1px solid var(--border)',
              }}
            >
              {/* Event Dot & Source Badge */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 32 }}>
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    background:
                      evt.severity === 'critical'
                        ? 'var(--critical-dim)'
                        : evt.severity === 'warning'
                        ? 'var(--warning-dim)'
                        : evt.severity === 'success'
                        ? 'var(--good-dim)'
                        : 'var(--accent-dim)',
                    border: `1px solid ${
                      evt.severity === 'critical'
                        ? 'var(--critical)'
                        : evt.severity === 'warning'
                        ? 'var(--warning)'
                        : evt.severity === 'success'
                        ? 'var(--good)'
                        : 'var(--accent)'
                    }`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color:
                      evt.severity === 'critical'
                        ? 'var(--critical)'
                        : evt.severity === 'warning'
                        ? 'var(--warning)'
                        : evt.severity === 'success'
                        ? 'var(--good)'
                        : 'var(--accent)',
                  }}
                >
                  <SourceIcon source={evt.source} />
                </div>
              </div>

              {/* Event Content */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 6, marginBottom: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>
                      {evt.title}
                    </span>
                    <span
                      style={{
                        fontSize: 10,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        padding: '2px 6px',
                        borderRadius: 4,
                        background: 'var(--panel-2)',
                        color: 'var(--text-faint)',
                        border: '1px solid var(--border)',
                      }}
                    >
                      {evt.source}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span className="av-mono" style={{ fontSize: 11, color: 'var(--accent)', fontWeight: 600 }}>
                      Node: {evt.targetNode}
                    </span>
                    <span className="av-mono" style={{ fontSize: 11, color: 'var(--text-faint)' }}>
                      {evt.timestamp}
                    </span>
                  </div>
                </div>

                <p style={{ margin: 0, fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.5 }}>
                  {evt.details}
                </p>
              </div>
            </div>
          ))}

          {filtered.length === 0 && (
            <div style={{ textAlign: 'center', padding: 36, color: 'var(--text-faint)' }}>
              No system events match the selected criteria.
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  )
}
