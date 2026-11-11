import { useCallback, useEffect, useState } from 'react'

// Loads a list once and exposes `reload` for after a create/update/delete
export function useResource<T>(load: () => Promise<T>, initial: T) {
  const [data, setData] = useState<T>(initial)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    try {
      setData(await load())
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không tải được dữ liệu')
    } finally {
      setLoading(false)
    }
  }, [load])

  useEffect(() => {
    reload()
  }, [reload])

  return { data, loading, error, reload }
}
