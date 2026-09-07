import { useEffect, useState } from 'react'
import type { Incident } from '@/modules/observability/types'
import { observabilityService } from '@/shared/api/services/observability'

export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [selected, setSelected] = useState<Incident | null>(null)

  useEffect(() => {
    observabilityService.listIncidents().then(setIncidents).catch(() => setIncidents([]))
  }, [])

  function markReviewed(id: number) {
    setIncidents((prev) => prev.map((i) => (i.id === id ? { ...i, status: 'Reviewed' } : i)))
    setSelected((s) => (s && s.id === id ? { ...s, status: 'Reviewed' } : s))
    void observabilityService.acknowledgeIncident(id)
  }

  function escalate(id: number) {
    setIncidents((prev) => prev.map((i) => (i.id === id ? { ...i, status: 'Escalated' } : i)))
    setSelected((s) => (s && s.id === id ? { ...s, status: 'Escalated' } : s))
    void observabilityService.resolveIncident(id)
  }

  return { incidents, selected, setSelected, markReviewed, escalate }
}
