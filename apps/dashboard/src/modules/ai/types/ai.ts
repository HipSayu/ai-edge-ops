export interface ModelArtifact { id: string; ref: string; name: string; version: string; architecture: string; format: string; sizeMb: number; mAP50: number; latencyBenchmarkMs: number; inputResolution: string; targetHardware: string; tags: string[]; registeredAt: string; status: 'production' | 'staging' | 'deprecated' }
export interface Deployment { id: string; modelName: string; modelVersion: string; targetDevices: string[]; strategy: 'Rolling Update' | 'Canary (20%)' | 'Immediate'; status: 'Active' | 'In Progress' | 'Failed' | 'Rolled Back'; progressPct: number; deployedBy: string; deployedAt: string; rollbackVersion?: string }
export interface InferenceSample { id: string; timestamp: string; camera: string; objects: { label: string; confidence: number; color: string }[]; fps: number; latencyMs: number; resolution: string }
export type ClassCategory = 'PPE' | 'Vehicle' | 'Person' | 'Hazard' | 'Object' | 'Custom'
export interface PredictionClass { id: number; label: string; category: ClassCategory; color: string; confidenceThreshold: number; enabled: boolean; detectionCount: number; lastDetected: string | null; description: string }
export interface ClassProfile { id: string; name: string; modelId: string; modelName: string; classes: PredictionClass[]; createdAt: string; updatedAt: string }
/** GET /models — read live from the OCI registry, one entry per image tag. */
export type ModelImageRecord = {
  name: string
  tag: string
  ref: string
  digest: string
  pinned_ref: string
  created_at: string | null
  platforms: string[]
  size_bytes: number
  task: string | null
  classes: string[]
  map50_95: number | null
  params_m: number | null
  latency_ms: number | null
  base: string | null
}
/** Cloud API v1 DeploymentOut. */
export type DeploymentRecord = {
  id: string; cluster_id: string; node_id: string; runtime_id: string; spec: Record<string, unknown>
  status: 'PENDING' | 'IN_PROGRESS' | 'SUCCEEDED' | 'FAILED' | 'REMOVING' | 'REMOVED'
  last_command_id: string | null; message: string | null; created_at: string | null; updated_at: string | null
}
/** Cloud API v1 DeploymentRequest. */
export type DeploymentCreate = {
  node_id: string; name: string; image_uri: string; image_tag?: string; model_id?: string | null; model_uri?: string | null
  config?: Record<string, unknown>; environment?: Record<string, string>; resource_limits?: Record<string, unknown>
}
export type InferenceRecord = InferenceSample
export const DEFAULT_COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
export interface ModelRegistryItem {
  id: string
  name: string
  version: string
  task: 'detection' | 'pose' | 'segmentation' | 'classification'
  framework: string
  precision: string
  inputResolution: string
  latencyOrinMs: number
  mAP: number
  fileSizeMb: number
  classes: string[]
  description: string
  activeDeployments: number
  updatedAt: string
}
/** Per-class runtime config (thresholds, alerting) plus live detection stats. */
export interface ClassConfigItem {
  id: number
  name: string
  displayName: string
  category: ClassCategory
  color: string
  minConfidence: number
  enabled: boolean
  alertOnDetection: boolean
  detectionCount24h: number
  lastSeen?: string
}
/** One fleet-wide telemetry sample (aggregated over all online nodes). */
export interface FleetMetricPoint {
  time: string
  fps: number
  latency: number
  throughput: number
  gpu: number
  alert: number
  healthyClusters: number
  onlineNodes: number
  onlineCameras: number
}
