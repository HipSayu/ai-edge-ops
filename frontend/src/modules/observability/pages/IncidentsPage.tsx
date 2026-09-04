import { useIncidents } from '@/modules/observability/hooks/useIncidents'
import IncidentsTable from '@/modules/observability/components/IncidentsTable'
import IncidentModal from '@/modules/observability/components/IncidentModal'

export default function IncidentsPage() {
  const { incidents, selected, setSelected, markReviewed, escalate } = useIncidents()

  return (
    <div>
      
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
