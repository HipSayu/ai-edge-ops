import { useCallback, useState } from 'react'
import { Search, Download, Play, Pause, Trash2, RotateCw } from 'lucide-react'
import type { LogEntry } from '@/modules/observability/types'
import { observabilityService } from '@/shared/api/services/observability'
import { useRealtimeChannel, type RealtimeEnvelope } from '@/shared/contexts/RealtimeContext'

type EdgeLogPayload = {
  level: string
  logger: string
  message: string
  recorded_at: string
  exception?: string | null
  device_id?: string
}

export default function LogsPage() {
  const [search, setSearch] = useState('')
  const [levelFilter, setLevelFilter] = useState('all')
  const [componentFilter, setComponentFilter] = useState('all')
  const [autoTail, setAutoTail] = useState(true)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [copiedNotice, setCopiedNotice] = useState(false)

  const handleRealtimeLog = useCallback((envelope: RealtimeEnvelope) => {
    if (!autoTail || envelope.type !== 'device.log') return
    const payload = envelope.payload as EdgeLogPayload
    const rawLevel = payload.level.toUpperCase()
    const level: LogEntry['level'] = rawLevel === 'ERROR' || rawLevel === 'WARN' || rawLevel === 'DEBUG' ? rawLevel : 'INFO'
    const entry: LogEntry = {
      id: `${envelope.source}-${payload.recorded_at}-${payload.message}`,
      timestamp: new Date(payload.recorded_at).toLocaleString(),
      level,
      component: payload.logger,
      node: payload.device_id ?? envelope.source,
      message: payload.exception ? `${payload.message} - ${payload.exception}` : payload.message,
    }
    setLogs((current) => [...current.slice(-499), entry])
  }, [autoTail])

  useRealtimeChannel('logs', handleRealtimeLog)

  const filtered = logs.filter((l) => {
    const matchSearch =
      search === '' ||
      l.message.toLowerCase().includes(search.toLowerCase()) ||
      l.node.toLowerCase().includes(search.toLowerCase()) ||
      l.component.toLowerCase().includes(search.toLowerCase())

    const matchLevel = levelFilter === 'all' || l.level === levelFilter
    const matchComponent = componentFilter === 'all' || l.component === componentFilter

    return matchSearch && matchLevel && matchComponent
  })

  function handleExportLogs() {
    const text = filtered.map((l) => `[${l.timestamp}] [${l.level}] [${l.component}] [${l.node}]: ${l.message}`).join('\n')
    navigator.clipboard.writeText(text)
    setCopiedNotice(true)
    setTimeout(() => setCopiedNotice(false), 2000)
  }

  function handleClear() {
    setLogs([])
  }

  function handleReset() {
    observabilityService.listLogs().then(setLogs).catch(() => setLogs([]))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className={`av-btn-secondary${autoTail ? ' active' : ''}`}
            onClick={() => setAutoTail(!autoTail)}
            style={{ fontSize: 12, padding: '6px 12px' }}
          >
            {autoTail ? <Pause size={13} /> : <Play size={13} />}
            <span>{autoTail ? 'Live Tail: ON' : 'Paused'}</span>
          </button>

          <button
            className="av-btn-secondary"
            onClick={handleExportLogs}
            style={{ fontSize: 12, padding: '6px 12px' }}
          >
            <Download size={13} />
            <span>{copiedNotice ? 'Copied to Clipboard!' : 'Export Logs'}</span>
          </button>

          {logs.length === 0 ? (
            <button className="av-btn-secondary" onClick={handleReset} style={{ fontSize: 12, padding: '6px 12px' }}>
              <RotateCw size={13} />
              <span>Reset Sample Logs</span>
            </button>
          ) : (
            <button className="av-btn-secondary danger" onClick={handleClear} style={{ fontSize: 12, padding: '6px 12px' }} title="Clear buffer">
              <Trash2 size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Filter Toolbar */}
      <section className="av-panel" style={{ marginBottom: 14 }}>
        <div className="av-filter-row">
          <div className="av-search-box">
            <Search size={14} color="var(--text-faint)" />
            <input
              type="text"
              placeholder="Search logs by keyword, component, node, or message..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}>
            <option value="all">All Log Levels</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
            <option value="DEBUG">DEBUG</option>
          </select>

          <select value={componentFilter} onChange={(e) => setComponentFilter(e.target.value)}>
            <option value="all">All Components</option>
            <option value="EdgeAgent">EdgeAgent</option>
            <option value="TensorRT">TensorRT</option>
            <option value="StreamDaemon">StreamDaemon</option>
            <option value="Deployer">Deployer</option>
          </select>
        </div>
      </section>

      {/* Terminal Log Console */}
      <div
        className="av-panel"
        style={{
          background: '#090d16',
          color: '#f8fafc',
          padding: 16,
          fontFamily: 'var(--font-mono)',
          fontSize: 12.5,
          lineHeight: 1.6,
          flex: 1,
          minHeight: 0,
          overflowY: 'auto',
          border: '1px solid var(--border-strong)',
          boxShadow: 'none'
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {filtered.map((log) => (
            <div
              key={log.id}
              style={{
                display: 'flex',
                gap: 12,
                padding: '4px 6px',
                borderRadius: 4,
                background: log.level === 'ERROR' ? 'rgba(239, 68, 68, 0.12)' : 'transparent'}}
            >
              <span style={{ color: '#64748b', userSelect: 'none' }}>{log.timestamp}</span>

              <span
                style={{
                  fontWeight: 700,
                  minWidth: 46,
                  color:
                    log.level === 'ERROR'
                      ? '#ef4444'
                      : log.level === 'WARN'
                      ? '#f59e0b'
                      : log.level === 'INFO'
                      ? '#10b981'
                      : '#38bdf8'}}
              >
                [{log.level}]
              </span>

              <span style={{ color: '#818cf8', fontWeight: 600, minWidth: 100 }}>
                {log.component}
              </span>

              <span style={{ color: '#94a3b8', minWidth: 90 }}>
                @{log.node}:
              </span>

              <span style={{ color: log.level === 'ERROR' ? '#fca5a5' : '#e2e8f0', wordBreak: 'break-all', flex: 1 }}>
                {log.message}
              </span>
            </div>
          ))}

          {filtered.length === 0 && (
            <div style={{ textAlign: 'center', padding: 36, color: '#64748b' }}>
              No log messages match the active search or level filter.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
