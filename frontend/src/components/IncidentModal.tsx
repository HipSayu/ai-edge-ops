import { SEVERITY_LABEL, STATUS_LABEL, type Incident } from '../mock/incidents'

interface Props {
  incident: Incident
  onClose: () => void
  onMarkReviewed: (id: number) => void
  onEscalate: (id: number) => void
}

export default function IncidentModal({ incident, onClose, onMarkReviewed, onEscalate }: Props) {
  return (
    <div className="av-modal-backdrop" onClick={onClose}>
      <div className="av-incident-modal" onClick={(e) => e.stopPropagation()}>
        <button className="av-modal-close" onClick={onClose} aria-label="Đóng">
          ✕
        </button>

        <div className="av-incident-modal-frame">
          <div className="av-video-scanlines" />
          <div className="av-detect-box" style={{ top: '18%', left: '30%', width: '26%', height: '62%' }}>
            <span className="av-detect-tag violation">{incident.event.toUpperCase()} {incident.confidence}%</span>
          </div>
          <div className="av-overlay-topbar">
            <span className="av-overlay-chip">{incident.camera}</span>
            <span className="av-overlay-chip mono">{incident.time}</span>
          </div>
        </div>

        <div className="av-incident-modal-body">
          <div className="av-incident-modal-header">
            <span className="av-incident-id">SỰ CỐ #{incident.id}</span>
            <span className={`av-severity-badge ${incident.severity}`}>{SEVERITY_LABEL[incident.severity]}</span>
          </div>
          <h2 className="av-incident-title">Phát hiện: {incident.event}</h2>

          <div className="av-incident-fields">
            <Field label="Camera" value={incident.camera} />
            <Field label="Độ tin cậy" value={`${incident.confidence}%`} />
            <Field label="Thời điểm" value={incident.time} />
            <Field label="Đối tượng" value={incident.personId} />
            <Field label="Vị trí" value={incident.location} />
            <Field label="Trạng thái" value={STATUS_LABEL[incident.status]} />
          </div>

          <div className="av-incident-explanation">
            <span className="av-panel-title">Giải thích của AI</span>
            <p>{incident.explanation}</p>
          </div>

          <div className="av-incident-actions">
            <button className="av-btn-secondary" onClick={() => onMarkReviewed(incident.id)}>
              Đánh dấu đã xem xét
            </button>
            <button className="av-btn-secondary danger" onClick={() => onEscalate(incident.id)}>
              Chuyển cấp xử lý
            </button>
            <button className="av-btn-primary">Xem camera</button>
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
