import { useState } from 'react'
import { mockIncidents, type Incident } from '@/modules/observability/mock/incidents'

export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>(mockIncidents)
  const [selected, setSelected] = useState<Incident | null>(null)

  function markReviewed(id: number) {
    setIncidents((prev) => prev.map((i) => (i.id === id ? { ...i, status: 'Reviewed' } : i)))
    setSelected((s) => (s && s.id === id ? { ...s, status: 'Reviewed' } : s))
  }

  function escalate(id: number) {
    setIncidents((prev) => prev.map((i) => (i.id === id ? { ...i, status: 'Escalated' } : i)))
    setSelected((s) => (s && s.id === id ? { ...s, status: 'Escalated' } : s))
  }

  return { incidents, selected, setSelected, markReviewed, escalate }
}
