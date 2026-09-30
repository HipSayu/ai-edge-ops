/**
 * EdgeOpsContext — single source of truth for every dashboard page.
 *
 * 1. On mount, loads the initial state from the REST services.
 * 2. Subscribes to realtime topics and folds each envelope into state.
 * 3. Actions call the REST API, then reload state from it.
 *
 * Pages only read from here; they never call services for fleet data.
 */
import { createContext, useContext, useState, useEffect, useCallback, useMemo, type Dispatch, type ReactNode, type SetStateAction } from 'react'
import type { Cluster, NodeAgent, CameraOnNode, ClusterSummary } from '@/modules/cluster/types/cluster'
import type { NodeLogEntry, RuntimeProcess } from '@/modules/agent/types/logs'
import type { CameraGroup, DetectionEvent, Snapshot } from '@/modules/agent/types/agent'
import type { ClassConfigItem, Deployment, FleetMetricPoint, ModelRegistryItem } from '@/modules/ai/types/ai'
import { clusterService } from '@/modules/cluster/services/cluster'
import { agentService } from '@/modules/agent/services/agent'
import { aiService } from '@/modules/ai/services/ai'
import { metricsService } from '@/modules/overview/services/metrics'
import { logsService } from '@/modules/agent/services/logs'
import { useRealtime, type RealtimeEnvelope } from '@/core/realtime/RealtimeContext'
import type { CameraStatusPayload, ClassStatsPayload, NodeStatusPayload, TelemetryPayload } from '@/core/edge-ops/realtimePayloads'

const MAX_LOGS_PER_NODE = 300
const MAX_EVENTS = 50
const MAX_METRIC_POINTS = 30
const MAX_SNAPSHOTS = 200

export interface ModelDeploymentPayload {
  nodeId: string
  modelName: string
  tag: string
  precision: string
  confidenceThreshold: number
}

interface EdgeOpsContextType {
  clusters: Cluster[]
  summary: ClusterSummary | null
  loading: boolean
  models: ModelRegistryItem[]
  /** Latest detection events across all nodes, newest first */
  events: DetectionEvent[]
  /** Rolling window of fleet-wide telemetry samples, oldest first */
  fleetMetrics: FleetMetricPoint[]
  classConfig: ClassConfigItem[]
  setClassConfig: Dispatch<SetStateAction<ClassConfigItem[]>>
  deployments: Deployment[]
  /** Camera groups with online/alert/fps aggregates derived from live cluster state */
  cameraGroups: CameraGroup[]
  createCameraGroup: (payload: { name: string; site: string; description?: string }) => Promise<void>
  /** Captured violation snapshots, newest first */
  snapshots: Snapshot[]
  // Actions — each calls the API, then reloads state
  createCluster: (clusterData: Partial<Cluster>) => Promise<void>
  provisionNode: (clusterId: string, nodeData: NodeAgent) => Promise<void>
  addCameraToNode: (nodeId: string, cameraData: Partial<CameraOnNode> & { streamUrl?: string }) => Promise<void>
  // Runtime & logs
  getNodeRuntimes: (nodeId: string) => RuntimeProcess[]
  getNodeLogs: (nodeId: string) => NodeLogEntry[]
  loadNodeLogs: (nodeId: string) => Promise<void>
  clearNodeLogs: (nodeId: string) => void
  updateRuntimeConfig: (nodeId: string, runtimeId: string, newConfig: Record<string, unknown>) => Promise<void>
  deployModelToNode: (payload: ModelDeploymentPayload) => Promise<void>
  restartRuntime: (nodeId: string, runtimeId: string) => Promise<void>
  refreshData: () => Promise<void>
}

const EdgeOpsContext = createContext<EdgeOpsContextType | undefined>(undefined)

// ─── Derivations ──────────────────────────────────────────────────────────────

const avg = (xs: number[]) => (xs.length ? Math.round(xs.reduce((a, b) => a + b, 0) / xs.length) : 0)

/** Recomputes every aggregate field of a cluster from its nodes and cameras. */
function withAggregates(c: Cluster): Cluster {
  const cams = c.nodes.flatMap((n) => n.cameras)
  const online = c.nodes.filter((n) => n.status !== 'offline')
  const onlineNodes = c.nodes.filter((n) => n.status === 'online').length
  const status: Cluster['status'] =
    c.nodes.length > 0 && online.length === 0 ? 'offline'
      : online.length < c.nodes.length || c.nodes.some((n) => n.status === 'degraded') ? 'degraded'
        : 'healthy'
  return {
    ...c,
    status,
    totalNodes: c.nodes.length,
    onlineNodes,
    totalCameras: cams.length,
    onlineCameras: cams.filter((x) => x.online).length,
    totalAlerts: cams.reduce((s, x) => s + x.alertCount, 0),
    avgCpuUsage: avg(online.map((n) => n.cpuUsage)),
    avgGpuUsage: avg(online.map((n) => n.gpuUsage)),
    avgTempC: avg(online.map((n) => n.tempC)),
    aggregateFps: cams.reduce((s, x) => s + (x.online ? x.fps : 0), 0),
  }
}

function summarize(cls: Cluster[]): ClusterSummary {
  const count = (s: Cluster['status']) => cls.filter((c) => c.status === s).length
  const sum = (k: 'totalNodes' | 'onlineNodes' | 'totalCameras' | 'onlineCameras' | 'totalAlerts') =>
    cls.reduce((s, c) => s + c[k], 0)
  return {
    totalClusters: cls.length,
    healthyClusters: count('healthy'),
    degradedClusters: count('degraded'),
    criticalClusters: count('critical'),
    offlineClusters: count('offline'),
    totalNodes: sum('totalNodes'),
    onlineNodes: sum('onlineNodes'),
    totalCameras: sum('totalCameras'),
    onlineCameras: sum('onlineCameras'),
    totalAlerts: sum('totalAlerts'),
  }
}

function withGroupAggregates(g: CameraGroup, clusters: Cluster[]): CameraGroup {
  const ids = new Set(g.cameraIds)
  const hits = clusters.flatMap((c) => c.nodes.flatMap((n) =>
    n.cameras.filter((cam) => ids.has(cam.id)).map((cam) => ({ cam, n }))))
  const modelVotes = new Map<string, number>()
  hits.forEach(({ n }) => { if (n.modelRunning) modelVotes.set(n.modelRunning, (modelVotes.get(n.modelRunning) ?? 0) + 1) })
  const primaryModel = [...modelVotes.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? g.primaryModel
  return {
    ...g,
    totalCameras: g.cameraIds.length,
    onlineCameras: hits.filter(({ cam }) => cam.online).length,
    activeAlerts: hits.reduce((s, { cam }) => s + cam.alertCount, 0),
    aggregateFps: hits.reduce((s, { cam }) => s + (cam.online ? cam.fps : 0), 0),
    primaryModel,
  }
}

const upsertBy = <T, K>(key: (x: T) => K) => (prev: T[], item: T): T[] =>
  prev.some((x) => key(x) === key(item)) ? prev.map((x) => (key(x) === key(item) ? item : x)) : [...prev, item]

const upsertCluster = upsertBy<Cluster, string>((c) => c.id)
const upsertModel = upsertBy<ModelRegistryItem, string>((m) => m.id)
const upsertClass = upsertBy<ClassConfigItem, number>((c) => c.id)
const upsertDeployment = upsertBy<Deployment, string>((d) => d.id)
const upsertGroup = upsertBy<CameraGroup, string>((g) => g.id)

const mapNode = (cls: Cluster[], nodeId: string, fn: (n: NodeAgent) => NodeAgent): Cluster[] =>
  cls.map((c) => (c.nodes.some((n) => n.id === nodeId)
    ? { ...c, updatedAt: new Date().toISOString(), nodes: c.nodes.map((n) => (n.id === nodeId ? fn(n) : n)) }
    : c))

const mapCamera = (cls: Cluster[], nodeId: string, cameraId: string, fn: (cam: CameraOnNode) => CameraOnNode) =>
  mapNode(cls, nodeId, (n) => ({ ...n, cameras: n.cameras.map((cam) => (cam.id === cameraId ? fn(cam) : cam)) }))

// ─── Provider ─────────────────────────────────────────────────────────────────

export function EdgeOpsProvider({ children }: { children: ReactNode }) {
  const { subscribe } = useRealtime()

  const [rawClusters, setRawClusters] = useState<Cluster[]>([])
  const [loading, setLoading] = useState(true)
  const [models, setModels] = useState<ModelRegistryItem[]>([])
  const [events, setEvents] = useState<DetectionEvent[]>([])
  /** nodeId → runtimeId → process */
  const [runtimes, setRuntimes] = useState<Record<string, Record<string, RuntimeProcess>>>({})
  const [logs, setLogs] = useState<Record<string, NodeLogEntry[]>>({})
  const [fleetMetrics, setFleetMetrics] = useState<FleetMetricPoint[]>([])
  const [classConfig, setClassConfig] = useState<ClassConfigItem[]>([])
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [rawGroups, setRawGroups] = useState<CameraGroup[]>([])
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])

  const clusters = useMemo(() => rawClusters.map(withAggregates), [rawClusters])
  const summary = useMemo(() => summarize(clusters), [clusters])
  const cameraGroups = useMemo(() => rawGroups.map((g) => withGroupAggregates(g, clusters)), [rawGroups, clusters])

  // ── 1. Initial load from API ──
  const refreshData = useCallback(async () => {
    try {
      // An endpoint that is missing or failing must not block the others
      const orEmpty = <T,>(p: Promise<T[]>) => p.catch((): T[] => [])
      const [cls, mdl, evs, metrics, classes, deps, groups, snaps, procs] = await Promise.all([
        orEmpty(clusterService.listClusters()),
        orEmpty(aiService.listRegistry()),
        orEmpty(agentService.listDetectionEvents()),
        orEmpty(metricsService.listFleetMetrics()),
        orEmpty(aiService.listClassConfig()),
        orEmpty(aiService.listDeployments()),
        orEmpty(agentService.listCameraGroups()),
        orEmpty(agentService.listSnapshots()),
        orEmpty(logsService.listRuntimes()),
      ])
      setRawClusters(cls)
      setModels(mdl)
      setEvents(evs)
      setFleetMetrics(metrics)
      setClassConfig(classes)
      setDeployments(deps)
      setRawGroups(groups)
      setSnapshots(snaps)
      const byNode: Record<string, Record<string, RuntimeProcess>> = {}
      procs.forEach(({ nodeId, ...p }) => { (byNode[nodeId] ??= {})[p.id] = p })
      setRuntimes(byNode)
    } catch (err) {
      console.error('Failed to load initial data:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refreshData() }, [refreshData])

  // ── 2. Realtime reducers ──
  const onCluster = useCallback((m: RealtimeEnvelope<Cluster>) => {
    if (m.type === 'snapshot') setRawClusters((prev) => upsertCluster(prev, m.payload))
  }, [])

  const onModel = useCallback((m: RealtimeEnvelope<ModelRegistryItem>) => {
    if (m.type === 'snapshot') setModels((prev) => upsertModel(prev, m.payload))
  }, [])

  const onNode = useCallback((m: RealtimeEnvelope<NodeStatusPayload>) => {
    setRawClusters((prev) => mapNode(prev, m.source, (n) => ({
      ...n,
      ...m.payload,
      ...(m.payload.status === 'offline' ? { cpuUsage: 0, gpuUsage: 0, ramUsedGb: 0, tempC: 0 } : {}),
    })))
  }, [])

  const onTelemetry = useCallback((m: RealtimeEnvelope<TelemetryPayload>) => {
    setRawClusters((prev) => mapNode(prev, m.source, (n) => ({ ...n, ...m.payload, lastHeartbeat: 'just now' })))
  }, [])

  const onCamera = useCallback((m: RealtimeEnvelope<CameraStatusPayload>) => {
    const cameraId = m.topic.slice('camera:'.length)
    setRawClusters((prev) => mapCamera(prev, m.payload.nodeId, cameraId, (cam) => ({ ...cam, online: m.payload.online, fps: m.payload.fps })))
  }, [])

  const onRuntime = useCallback((m: RealtimeEnvelope<RuntimeProcess | NodeLogEntry>) => {
    const nodeId = m.source
    if (m.type === 'status') {
      const proc = m.payload as RuntimeProcess
      setRuntimes((prev) => ({ ...prev, [nodeId]: { ...prev[nodeId], [proc.id]: proc } }))
    } else if (m.type === 'log') {
      const entry = m.payload as NodeLogEntry
      setLogs((prev) => ({ ...prev, [nodeId]: [...(prev[nodeId] ?? []).slice(-(MAX_LOGS_PER_NODE - 1)), entry] }))
    }
  }, [])

  const onAlert = useCallback((m: RealtimeEnvelope<DetectionEvent>) => {
    if (m.type !== 'detection') return
    const ev = m.payload
    setEvents((prev) => [ev, ...prev].slice(0, MAX_EVENTS))
    if (ev.status === 'UNSAFE') {
      setRawClusters((prev) => mapCamera(prev, ev.nodeId, ev.cameraId, (cam) => ({ ...cam, alertCount: cam.alertCount + 1 })))
    }
  }, [])

  const onSnapshot = useCallback((m: RealtimeEnvelope<Snapshot>) => {
    if (m.type === 'captured') setSnapshots((prev) => [m.payload, ...prev].slice(0, MAX_SNAPSHOTS))
  }, [])

  const onClass = useCallback((m: RealtimeEnvelope<ClassConfigItem | ClassStatsPayload>) => {
    const id = Number(m.source)
    if (m.type === 'snapshot') setClassConfig((prev) => upsertClass(prev, m.payload as ClassConfigItem))
    else if (m.type === 'stats') setClassConfig((prev) => prev.map((c) => (c.id === id ? { ...c, ...(m.payload as ClassStatsPayload) } : c)))
  }, [])

  const onDeployment = useCallback((m: RealtimeEnvelope<Deployment>) => {
    if (m.type === 'progress') setDeployments((prev) => upsertDeployment(prev, m.payload))
    // An edge reported a deployment result: its record changed server-side, reload the list
    else if (m.type === 'changed') aiService.listDeployments().then(setDeployments).catch(() => undefined)
  }, [])

  const onGroup = useCallback((m: RealtimeEnvelope<CameraGroup>) => {
    if (m.type === 'snapshot') setRawGroups((prev) => upsertGroup(prev, m.payload))
  }, [])

  const onFleetMetric = useCallback((m: RealtimeEnvelope<FleetMetricPoint>) => {
    if (m.type === 'sample') setFleetMetrics((prev) => [...prev, m.payload].slice(-MAX_METRIC_POINTS))
  }, [])

  useEffect(() => {
    const unsubs = [
      subscribe<Cluster>('cluster:', onCluster),
      subscribe<ModelRegistryItem>('model:', onModel),
      subscribe<NodeStatusPayload>('node:', onNode),
      subscribe<TelemetryPayload>('telemetry:', onTelemetry),
      subscribe<CameraStatusPayload>('camera:', onCamera),
      subscribe<RuntimeProcess | NodeLogEntry>('runtime:', onRuntime),
      subscribe<DetectionEvent>('alert:', onAlert),
      subscribe<Snapshot>('snapshot:', onSnapshot),
      subscribe<ClassConfigItem | ClassStatsPayload>('class:', onClass),
      subscribe<Deployment>('deployment:', onDeployment),
      subscribe<CameraGroup>('group:', onGroup),
      subscribe<FleetMetricPoint>('metrics:fleet', onFleetMetric),
    ]
    return () => unsubs.forEach((u) => u())
  }, [subscribe, onCluster, onModel, onNode, onTelemetry, onCamera, onRuntime, onAlert,
    onSnapshot, onClass, onDeployment, onGroup, onFleetMetric])

  // ── 3. Actions: call the API, then reload (realtime pushes keep it fresh after) ──
  const createCluster = async ({ name, site, description }: Partial<Cluster>) => {
    await clusterService.createCluster({ name: name || 'NEW-CLUSTER', location: site, description })
    await refreshData()
  }

  const provisionNode = async (clusterId: string, nodeData: NodeAgent) => {
    await clusterService.registerNode({ cluster_id: clusterId, name: nodeData.name })
    await refreshData()
  }

  const addCameraToNode = async (nodeId: string, cameraData: Partial<CameraOnNode> & { streamUrl?: string }) => {
    await agentService.createCamera({
      node_id: nodeId,
      name: cameraData.name || 'NEW-CAM',
      zone: cameraData.zone,
      stream_url: cameraData.streamUrl,
      resolution: cameraData.resolution,
      fps: cameraData.fps,
      model: cameraData.model,
    })
    await refreshData()
  }

  const getNodeRuntimes = useCallback((nodeId: string) => Object.values(runtimes[nodeId] ?? {}), [runtimes])
  const getNodeLogs = useCallback((nodeId: string) => logs[nodeId] ?? [], [logs])

  /** Seeds a node's log view with the recent lines kept by the Cloud; live lines keep appending after. */
  const loadNodeLogs = useCallback(async (nodeId: string) => {
    const recent = await logsService.listNodeLogs({ nodeId, limit: MAX_LOGS_PER_NODE }).catch((): NodeLogEntry[] => [])
    setLogs((prev) => {
      const seen = new Set(recent.map((l) => l.id))
      const live = (prev[nodeId] ?? []).filter((l) => !seen.has(l.id))
      return { ...prev, [nodeId]: [...recent, ...live].slice(-MAX_LOGS_PER_NODE) }
    })
  }, [])

  // Fleet charts are computed server-side from telemetry history; poll them (no realtime topic)
  useEffect(() => {
    const id = setInterval(() => {
      metricsService.listFleetMetrics().then(setFleetMetrics).catch(() => undefined)
    }, 10_000)
    return () => clearInterval(id)
  }, [])
  const clearNodeLogs = (nodeId: string) => setLogs((prev) => ({ ...prev, [nodeId]: [] }))

  const updateRuntimeConfig = async (_nodeId: string, runtimeId: string, _newConfig: Record<string, unknown>) => {
    await logsService.controlRuntime(runtimeId, 'update')
    await refreshData()
  }

  const restartRuntime = async (_nodeId: string, runtimeId: string) => {
    await logsService.controlRuntime(runtimeId, 'restart')
    await refreshData()
  }

  const createCameraGroup = async ({ name, site, description }: { name: string; site: string; description?: string }) => {
    await agentService.createCameraGroup({ name, site, description, camera_ids: [] })
    await refreshData()
  }

  const deployModelToNode = async ({ nodeId, modelName, tag, precision, confidenceThreshold }: ModelDeploymentPayload) => {
    await aiService.createDeployment({
      node_id: nodeId,
      name: modelName,
      image_uri: modelName,
      image_tag: tag,
      model_id: tag,
      config: { precision, confidence_threshold: confidenceThreshold },
    })
    await refreshData()
  }

  return (
    <EdgeOpsContext.Provider
      value={{
        clusters, summary, loading, models, events,
        fleetMetrics, classConfig, setClassConfig, deployments, cameraGroups, createCameraGroup, snapshots,
        createCluster, provisionNode, addCameraToNode,
        getNodeRuntimes, getNodeLogs, loadNodeLogs, clearNodeLogs,
        updateRuntimeConfig, deployModelToNode, restartRuntime,
        refreshData,
      }}
    >
      {children}
    </EdgeOpsContext.Provider>
  )
}

export function useEdgeOps() {
  const context = useContext(EdgeOpsContext)
  if (!context) {
    throw new Error('useEdgeOps must be used within an EdgeOpsProvider')
  }
  return context
}
