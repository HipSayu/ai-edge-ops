import { useEffect, useRef, useState } from 'react'
import type { GridItem } from '@/api/types'
import { gridService } from '@/services/grid.service'


const POLL_MS = 3000

// A quick, cheap check before replacing the array: a list that is equal item-by-item means React (and everything
// hanging off `items`, like the grid of tiles) has nothing new to do, so skip the re-render that a fresh array would
// otherwise cause every 3 seconds even when the wall has not actually changed.
function sameItems(a: GridItem[], b: GridItem[]): boolean {
  if (a.length !== b.length) return false
  return a.every((item, i) => {
    const other = b[i]
    return (
      item.camera_id === other.camera_id &&
      item.person_count === other.person_count &&
      item.violation_count_recent === other.violation_count_recent &&
      item.score === other.score &&
      item.online === other.online
    )
  })
}

// The server decides which cameras are shown and in what order (people and violations first, with
// hysteresis against flicker). The client only keeps the camera the user has open from being swapped out.
export function useGrid(areaId: number | null, pinnedId: number | null) {
  const [items, setItems] = useState<GridItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const pinned = useRef(pinnedId)
  const last = useRef<GridItem[]>([])
  pinned.current = pinnedId

  useEffect(() => {
    let alive = true
    setLoading(true)

    async function load() {
      try {
        let next = await gridService.grid(areaId)
        const keep = pinned.current
        if (keep !== null && !next.some((i) => i.camera_id === keep)) {
          const previous = last.current.find((i) => i.camera_id === keep)
          if (previous) next = [...next.slice(0, Math.max(0, next.length - 1)), previous]
        }
        if (!alive) return
        const changed = !sameItems(last.current, next)
        last.current = next
        if (changed) setItems(next)
        setError(null)
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : 'Không tải được lưới camera')
      } finally {
        if (alive) setLoading(false)
      }
    }

    load()
    const timer = setInterval(load, POLL_MS)
    return () => {
      alive = false
      clearInterval(timer)
    }
  }, [areaId])

  return { items, loading, error }
}
