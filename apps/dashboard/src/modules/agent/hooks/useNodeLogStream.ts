import { useEffect, useMemo, useState } from 'react'
import type { LogLevel, NodeLogEntry, RuntimeId } from '@/modules/agent/types/logs'
import { useEdgeOps } from '@/core/edge-ops/EdgeOpsContext'

/**
 * Live view over a node's runtimes and logs held in EdgeOpsContext.
 * Pausing freezes the visible log list at the moment it was paused.
 */
export function useNodeLogStream(nodeId: string | undefined, runtime: RuntimeId | 'all', level: LogLevel | 'ALL') {
  const { getNodeRuntimes, getNodeLogs, loadNodeLogs, clearNodeLogs } = useEdgeOps()
  const [pausedLogs, setPausedLogs] = useState<NodeLogEntry[] | null>(null)

  // Recent history from the Cloud when a node is opened; realtime appends from there
  useEffect(() => {
    if (nodeId) loadNodeLogs(nodeId)
  }, [nodeId, loadNodeLogs])

  const runtimes = nodeId ? getNodeRuntimes(nodeId) : []
  const liveLogs = nodeId ? getNodeLogs(nodeId) : []
  const isLive = pausedLogs === null
  const source = pausedLogs ?? liveLogs

  const logs = useMemo(() => source.filter((l) =>
    (runtime === 'all' || l.runtime === runtime) && (level === 'ALL' || l.level === level)
  ), [source, runtime, level])

  const toggleLive = () => setPausedLogs(isLive ? liveLogs : null)
  const clear = () => {
    if (nodeId) clearNodeLogs(nodeId)
    if (!isLive) setPausedLogs([])
  }

  return { runtimes, logs, isLive, toggleLive, clear }
}
