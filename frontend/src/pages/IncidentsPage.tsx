import { useIncidents } from '../hooks/useIncidents'
import IncidentsTable from '../components/IncidentsTable'
import IncidentModal from '../components/IncidentModal'

export default function IncidentsPage() {
  const { incidents, selected, setSelected, markReviewed, escalate } = useIncidents()

  return (
    <div>
      <div className="av-section-title">Sự cố</div>
      <IncidentsTable data={incidents} onSelect={setSelected} />

      {selected && (
        <IncidentModal
          incident={selected}
          onClose={() => setSelected(null)}
          onMarkReviewed={markReviewed}
          onEscalate={escalate}
        />
      )}
    </div>
  )
}
