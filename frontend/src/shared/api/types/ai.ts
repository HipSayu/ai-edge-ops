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
export type DeploymentRecord = { device_id: string; name: string; desired_image: string | null; active_image: string | null; runtime_status: string; in_sync: boolean; updated_at: string | null }
export type InferenceRecord = InferenceSample
export const DEFAULT_COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
