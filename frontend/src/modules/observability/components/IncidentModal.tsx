import { X, CheckCircle2, AlertTriangle, Video, Sparkles, Shield } from 'lucide-react'
import { SEVERITY_LABEL, STATUS_LABEL, type Incident } from '@/modules/observability/mock/incidents'

interface Props {
  incident: Incident
  onClose: () => void
  onMarkReviewed: (id: number) => void
  onEscalate: (id: number) => void
}

export default function IncidentModal({ incident, onClose, onMarkReviewed, onEscalate }: Props) {
  return (
    <div className="av-modal-backdrop" onClick={onClose}>
      <div className="av-incident-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <button className="av-modal-close" onClick={onClose} aria-label="Close dialog">
          <X size={16} />
        </button>

        <div className="av-incident-modal-frame">
          <div className="av-video-scanlines" />
          <div
            className="av-detect-box"
            style={{ top: '18%', left: '30%', width: '26%', height: '62%' }}
          >
            <span className="av-detect-tag violation">
              {incident.event.toUpperCase()} {incident.confidence}%
            </span>
          </div>
          <div className="av-overlay-topbar">
            <span className="av-overlay-chip">
              <Shield size={12} />
              <span>{incident.camera}</span>
            </span>
            <span className="av-overlay-chip mono">{incident.time}</span>
          </div>
        </div>

        <div className="av-incident-modal-body">
          <div className="av-incident-modal-header">
            <span className="av-incident-id">INCIDENT #{incident.id}</span>
            <span className={`av-severity-badge ${incident.severity}`}>
              {SEVERITY_LABEL[incident.severity]}
            </span>
          </div>
          <h2 className="av-incident-title">{incident.event}</h2>

          <div className="av-incident-fields">
            <Field label="Camera Stream" value={incident.camera} />
            <Field label="AI Confidence" value={`${incident.confidence}%`} />
            <Field label="Timestamp" value={incident.time} />
            <Field label="Subject Tracker" value={incident.personId} />
            <Field label="Facility Zone" value={incident.location} />
            <Field label="Triage Status" value={STATUS_LABEL[incident.status]} />
          </div>

          <div className="av-incident-explanation">
            <span className="av-panel-title">
              <Sparkles size={14} color="var(--accent)" />
              <span>AI Cause Analysis & Verification</span>
            </span>
            <p>{incident.explanation}</p>
          </div>

          <div className="av-incident-actions">
            <button
              className="av-btn-primary"
              onClick={() => onMarkReviewed(incident.id)}
            >
              <CheckCircle2 size={16} />
              <span>Mark as Reviewed</span>
            </button>
            <button
              className="av-btn-secondary danger"
              onClick={() => onEscalate(incident.id)}
            >
              <AlertTriangle size={16} />
              <span>Escalate Alert</span>
            </button>
            <button className="av-btn-secondary" onClick={onClose}>
              <Video size={16} />
              <span>Live Stream</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="av-incident-field">
      <span className="av-incident-field-label">{label}</span>
      <span className="av-incident-field-value">{value}</span>
    </div>
  )
}
