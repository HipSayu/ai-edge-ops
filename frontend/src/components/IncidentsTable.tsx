import { useMemo, useState } from 'react'
import { SEVERITY_LABEL, STATUS_LABEL, type Incident, type IncidentStatus, type Severity } from '../mock/incidents'
import { mockCameras } from '../mock/cameras'

type SortKey = 'time' | 'confidence' | 'severity'

interface Props {
  data: Incident[]
  onSelect: (incident: Incident) => void
}

const SEVERITY_ORDER: Record<Severity, number> = { critical: 2, warning: 1, info: 0 }

export default function IncidentsTable({ data, onSelect }: Props) {
  const [camera, setCamera] = useState('all')
  const [event, setEvent] = useState('all')
  const [severity, setSeverity] = useState('all')
  const [status, setStatus] = useState('all')
  const [sortKey, setSortKey] = useState<SortKey>('time')
  const [sortDesc, setSortDesc] = useState(true)

  const eventTypes = useMemo(() => [...new Set(data.map((d) => d.event))], [data])

  const filtered = useMemo(() => {
    let rows = data.filter(
      (r) =>
        (camera === 'all' || r.camera === camera) &&
        (event === 'all' || r.event === event) &&
        (severity === 'all' || r.severity === severity) &&
        (status === 'all' || r.status === status),
    )
    rows = [...rows].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'time') cmp = a.time.localeCompare(b.time)
      else if (sortKey === 'confidence') cmp = a.confidence - b.confidence
      else cmp = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
      return sortDesc ? -cmp : cmp
    })
    return rows
  }, [data, camera, event, severity, status, sortKey, sortDesc])

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
        <span className="av-panel-title">Sự cố gần đây</span>
      </div>

      <div className="av-filter-row">
        <select value={camera} onChange={(e) => setCamera(e.target.value)}>
          <option value="all">Tất cả camera</option>
          {mockCameras.map((c) => (
            <option key={c.id} value={c.id}>
              {c.id}
            </option>
          ))}
        </select>
        <select value={event} onChange={(e) => setEvent(e.target.value)}>
          <option value="all">Tất cả loại sự cố</option>
          {eventTypes.map((e) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="all">Tất cả mức độ</option>
          <option value="critical">Nghiêm trọng</option>
          <option value="warning">Cảnh báo</option>
          <option value="info">Thông tin</option>
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="all">Tất cả trạng thái</option>
          <option value="New">Mới</option>
          <option value="Reviewed">Đã xem xét</option>
          <option value="Escalated">Đã chuyển cấp</option>
        </select>
        <select disabled defaultValue="all">
          <option value="all">2 giờ qua</option>
        </select>
      </div>

      <div className="av-table-wrap">
        <table className="av-table">
          <thead>
            <tr>
              <th className="sortable" onClick={() => toggleSort('time')}>
                Thời gian {sortKey === 'time' && (sortDesc ? '↓' : '↑')}
              </th>
              <th>Camera</th>
              <th>Sự kiện</th>
              <th className="sortable" onClick={() => toggleSort('confidence')}>
                Độ tin cậy {sortKey === 'confidence' && (sortDesc ? '↓' : '↑')}
              </th>
              <th className="sortable" onClick={() => toggleSort('severity')}>
                Mức độ {sortKey === 'severity' && (sortDesc ? '↓' : '↑')}
              </th>
              <th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.id} onClick={() => onSelect(row)} className="av-clickable-row">
                <td className="av-mono">{row.time}</td>
                <td>{row.camera}</td>
                <td>{row.event}</td>
                <td className="av-mono">{row.confidence}%</td>
                <td>
                  <span className={`av-severity-badge ${row.severity}`}>{SEVERITY_LABEL[row.severity]}</span>
                </td>
                <td>
                  <StatusPill status={row.status} />
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="av-table-empty">
                  Không có sự cố nào khớp với bộ lọc hiện tại.
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
