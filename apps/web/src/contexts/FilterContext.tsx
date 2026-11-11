import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

interface FilterState {
  clusterId: number | null
  nodeId: number | null
  cameraId: number | null
  // Cluster -> Node -> Camera hierarchy: choosing a level clears the levels below it.
  setClusterId: (id: number | null) => void
  setNodeId: (id: number | null) => void
  setCameraId: (id: number | null) => void
}

const FilterContext = createContext<FilterState | null>(null)

export function FilterProvider({ children }: { children: ReactNode }) {
  const [clusterId, setCluster] = useState<number | null>(null)
  const [nodeId, setNode] = useState<number | null>(null)
  const [cameraId, setCameraId] = useState<number | null>(null)

  const setClusterId = useCallback((id: number | null) => {
    setCluster(id)
    setNode(null)
    setCameraId(null)
  }, [])
  const setNodeId = useCallback((id: number | null) => {
    setNode(id)
    setCameraId(null)
  }, [])

  const value = useMemo(
    () => ({ clusterId, nodeId, cameraId, setClusterId, setNodeId, setCameraId }),
    [clusterId, nodeId, cameraId, setClusterId, setNodeId],
  )
  return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>
}

export function useFilters(): FilterState {
  const ctx = useContext(FilterContext)
  if (!ctx) throw new Error('useFilters must be used inside FilterProvider')
  return ctx
}
