import { useState } from 'react'
import { Search, Download } from 'lucide-react'
import { mockAuditLogs } from '@/modules/system/mock/system'

export default function AuditLogsPage() {
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [copiedNotice, setCopiedNotice] = useState(false)

  const filtered = mockAuditLogs.filter((log) => {
    const matchSearch =
      search === '' ||
      log.actor.toLowerCase().includes(search.toLowerCase()) ||
      log.action.toLowerCase().includes(search.toLowerCase()) ||
      log.targetResource.toLowerCase().includes(search.toLowerCase()) ||
      log.ipAddress.includes(search) ||
      log.detail.toLowerCase().includes(search.toLowerCase())

    const matchCategory = categoryFilter === 'all' || log.category === categoryFilter
    const matchStatus = statusFilter === 'all' || log.status === statusFilter

    return matchSearch && matchCategory && matchStatus
  })

  function handleExport() {
    const csv = [
      'Timestamp,Actor,Email,Action,Category,Target,IP,Status,Detail',
      ...filtered.map(
        (l) =>
          `"${l.timestamp}","${l.actor}","${l.actorEmail}","${l.action}","${l.category}","${l.targetResource}","${l.ipAddress}","${l.status}","${l.detail}"`
      ),
    ].join('/n')

    navigator.clipboard.writeText(csv)
    setCopiedNotice(true)
    setTimeout(() => setCopiedNotice(false), 2000)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        
        <button className="av-btn-secondary" onClick={handleExport} style={{ fontSize: 12 }}>
          <Download size={14} />
          <span>{copiedNotice ? 'Exported CSV to Clipboard!' : 'Export Audit CSV'}</span>
        </button>
      </div>

      {/* Filter and Search */}
      <section className="av-panel" style={{ marginBottom: 18 }}>
        <div className="av-filter-row">
          <div className="av-search-box">
            <Search size={14} color="var(--text-faint)" />
            <input
              type="text"
              placeholder="Search audit trail by actor, action, IP, or resource..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="all">All Action Categories</option>
            <option value="Deployment">Deployment</option>
            <option value="Hardware">Hardware Control</option>
            <option value="Config">Config Modification</option>
            <option value="Triage">Incident Triage</option>
            <option value="Security">Security</option>
          </select>

          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">All Outcomes</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="DENIED">DENIED</option>
            <option value="FAILED">FAILED</option>
          </select>
        </div>

        {/* Audit Log Table */}
        <div className="av-table-wrap">
          <table className="av-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target Resource</th>
                <th>Outcome</th>
                <th>Client IP</th>
                <th>Audit Details</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((log) => (
                <tr key={log.id}>
                  <td className="av-mono" style={{ whiteSpace: 'nowrap' }}>{log.timestamp}</td>
                  <td>
                    <div>
                      <div style={{ fontWeight: 700 }}>{log.actor}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-faint)' }}>{log.actorEmail}</div>
                    </div>
                  </td>
                  <td>
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: 11,
                        fontWeight: 700,
                        padding: '3px 8px',
                        borderRadius: 4,
                        background: 'var(--panel-2)',
                        border: '1px solid var(--border)',
                        color: 'var(--accent)',
                        display: 'inline-block'}}
                    >
                      {log.action}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600 }}>{log.targetResource}</span>
                  </td>
                  <td>
                    <span
                      className={`av-status-pill ${
                        log.status === 'SUCCESS' ? 'reviewed' : 'escalated'
                      }`}
                    >
                      {log.status}
                    </span>
                  </td>
                  <td className="av-mono" style={{ fontSize: 11.5 }}>{log.ipAddress}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-dim)', maxWidth: 320 }}>
                    {log.detail}
                  </td>
                </tr>
              ))}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="av-table-empty">
                    No audit log records match the selected criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
