import { AlertCircle, AlertTriangle, Info, BellRing, ArrowUpRight } from 'lucide-react'
import { SEVERITY_LABEL, type Incident, type Severity } from '@/modules/observability/mock/incidents'

interface Props {
  data: Incident[]
  onSelect: (incident: Incident) => void
}

function SeverityIcon({ severity }: { severity: Severity }) {
  switch (severity) {
    case 'critical':
      return <AlertCircle size={15} color="var(--critical)" />
    case 'warning':
      return <AlertTriangle size={15} color="var(--warning)" />
    case 'info':
      return <Info size={15} color="var(--info)" />
  }
}

export default function AlertsPanel({ data, onSelect }: Props) {
  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">
          <BellRing size={15} />
          <span>Real-Time Incident Stream</span>
        </span>
        <span className="av-panel-sub">Auto-Triage Active</span>
      </div>

      <ul className="av-alert-list">
        {data.map((a) => (
          <li key={a.id}>
            <button className={`av-alert-row ${a.severity}`} onClick={() => onSelect(a)}>
              <span className="av-alert-dot">
                <SeverityIcon severity={a.severity} />
              </span>
              <span className="av-alert-time av-mono">{a.time}</span>
              <span className="av-alert-camera">{a.camera}</span>
              <span className="av-alert-event">{a.event}</span>
              <span className="av-alert-person av-mono">{a.personId}</span>
              <span className={`av-severity-badge ${a.severity}`}>
                {SEVERITY_LABEL[a.severity]}
              </span>
              <ArrowUpRight size={14} color="var(--text-faint)" />
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
