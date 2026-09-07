import { useEffect, useMemo, useState } from 'react'
import {
  Search,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  ArrowUpDown,
} from 'lucide-react'
import {
  SEVERITY_LABEL,
  STATUS_LABEL,
  type Incident,
  type IncidentStatus,
  type Severity,
} from '@/modules/observability/types'
import { agentService } from '@/shared/api/services/agent'
import type { Camera } from '@/modules/agent/types'

type SortKey = 'time' | 'confidence' | 'severity'

interface Props {
  data: Incident[]
  onSelect: (incident: Incident) => void
}

const SEVERITY_ORDER: Record<Severity, number> = { critical: 2, warning: 1, info: 0 }

export default function IncidentsTable({ data, onSelect }: Props) {
  const [search, setSearch] = useState('')
  const [camera, setCamera] = useState('all')
  const [event, setEvent] = useState('all')
  const [severity, setSeverity] = useState('all')
  const [status, setStatus] = useState('all')
  const [sortKey, setSortKey] = useState<SortKey>('time')
  const [sortDesc, setSortDesc] = useState(true)
  const [cameras, setCameras] = useState<Camera[]>([])

  useEffect(() => {
    agentService.listCameras().then(setCameras).catch(() => setCameras([]))
  }, [])

  const eventTypes = useMemo(() => [...new Set(data.map((d) => d.event))], [data])

  const filtered = useMemo(() => {
    let rows = data.filter((r) => {
      const matchSearch =
        search === '' ||
        r.event.toLowerCase().includes(search.toLowerCase()) ||
        r.camera.toLowerCase().includes(search.toLowerCase()) ||
        r.personId.toLowerCase().includes(search.toLowerCase()) ||
        r.location.toLowerCase().includes(search.toLowerCase())

      return (
        matchSearch &&
        (camera === 'all' || r.camera === camera) &&
        (event === 'all' || r.event === event) &&
        (severity === 'all' || r.severity === severity) &&
        (status === 'all' || r.status === status)
      )
    })

    rows = [...rows].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'time') cmp = a.time.localeCompare(b.time)
      else if (sortKey === 'confidence') cmp = a.confidence - b.confidence
      else cmp = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
      return sortDesc ? -cmp : cmp
    })
    return rows
  }, [data, search, camera, event, severity, status, sortKey, sortDesc])

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDesc((d) => !d)
    else {
      setSortKey(key)
      setSortDesc(true)
    }
  }

  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">
          <AlertTriangle size={15} />
          <span>Recent Incident Log & Triage</span>
        </span>
        <span className="av-panel-sub">{filtered.length} Recorded Events</span>
      </div>

      <div className="av-filter-row">
        <div className="av-search-box">
          <Search size={14} color="var(--text-faint)" />
          <input
            type="text"
            placeholder="Search by event, camera, ID, or zone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select value={camera} onChange={(e) => setCamera(e.target.value)}>
          <option value="all">All Cameras</option>
          {cameras.map((c) => (
            <option key={c.id} value={c.id}>
              {c.id} — {c.name}
            </option>
          ))}
        </select>

        <select value={event} onChange={(e) => setEvent(e.target.value)}>
          <option value="all">All Event Types</option>
          {eventTypes.map((e) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>

        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>

        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="all">All Statuses</option>
          <option value="New">New</option>
          <option value="Reviewed">Reviewed</option>
          <option value="Escalated">Escalated</option>
        </select>

        <select disabled defaultValue="all">
          <option value="all">Past 2 Hours</option>
        </select>
      </div>

      <div className="av-table-wrap">
        <table className="av-table">
          <thead>
            <tr>
              <th className="sortable" onClick={() => toggleSort('time')}>
                Timestamp{' '}
                {sortKey === 'time' ? (
                  sortDesc ? (
                    <ChevronDown size={12} style={{ display: 'inline' }} />
                  ) : (
                    <ChevronUp size={12} style={{ display: 'inline' }} />
                  )
                ) : (
                  <ArrowUpDown size={11} style={{ display: 'inline', opacity: 0.4 }} />
                )}
              </th>
              <th>Camera</th>
              <th>Incident Event</th>
              <th className="sortable" onClick={() => toggleSort('confidence')}>
                AI Confidence{' '}
                {sortKey === 'confidence' ? (
                  sortDesc ? (
                    <ChevronDown size={12} style={{ display: 'inline' }} />
                  ) : (
                    <ChevronUp size={12} style={{ display: 'inline' }} />
                  )
                ) : (
                  <ArrowUpDown size={11} style={{ display: 'inline', opacity: 0.4 }} />
                )}
              </th>
              <th className="sortable" onClick={() => toggleSort('severity')}>
                Severity{' '}
                {sortKey === 'severity' ? (
                  sortDesc ? (
                    <ChevronDown size={12} style={{ display: 'inline' }} />
                  ) : (
                    <ChevronUp size={12} style={{ display: 'inline' }} />
                  )
                ) : (
                  <ArrowUpDown size={11} style={{ display: 'inline', opacity: 0.4 }} />
                )}
              </th>
              <th>Triage Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.id} onClick={() => onSelect(row)} className="av-clickable-row">
                <td className="av-mono">{row.time}</td>
                <td>
                  <strong>{row.camera}</strong>
                </td>
                <td>{row.event}</td>
                <td className="av-mono">{row.confidence}%</td>
                <td>
                  <span className={`av-severity-badge ${row.severity}`}>
                    {SEVERITY_LABEL[row.severity]}
                  </span>
                </td>
                <td>
                  <StatusPill status={row.status} />
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="av-table-empty">
                  No incidents match the active search or filter criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function StatusPill({ status }: { status: IncidentStatus }) {
  const cls = status === 'New' ? 'new' : status === 'Escalated' ? 'escalated' : 'reviewed'
  return <span className={`av-status-pill ${cls}`}>{STATUS_LABEL[status]}</span>
}
