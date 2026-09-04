import { SEVERITY_LABEL, type Incident, type Severity } from '../mock/incidents'

const SEVERITY_DOT: Record<Severity, string> = {
  critical: '🔴',
  warning: '🟠',
  info: '🟡',
}

interface Props {
  data: Incident[]
  onSelect: (incident: Incident) => void
}

export default function AlertsPanel({ data, onSelect }: Props) {
  return (
    <section className="av-panel">
      <div className="av-panel-header">
        <span className="av-panel-title">Cảnh báo trực tiếp</span>
      </div>
      <ul className="av-alert-list">
        {data.map((a) => (
          <li key={a.id}>
            <button className={`av-alert-row ${a.severity}`} onClick={() => onSelect(a)}>
              <span className="av-alert-dot">{SEVERITY_DOT[a.severity]}</span>
              <span className="av-alert-time av-mono">{a.time}</span>
              <span className="av-alert-camera">{a.camera}</span>
              <span className="av-alert-event">{a.event}</span>
              <span className="av-alert-person">{a.personId}</span>
              <span className={`av-severity-badge ${a.severity}`}>{SEVERITY_LABEL[a.severity]}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
