export interface ModelArtifact {
  id: string            // the image tag, e.g. "1.3.0"
  ref: string           // digest-pinned ref the edge pulls
  name: string
  version: string
  architecture: string  // base model
  format: string        // platforms, e.g. "linux/amd64 + linux/arm64"
  sizeMb: number
  mAP50: number         // mAP@50-95
  latencyBenchmarkMs: number
  inputResolution: string
  targetHardware: string
  tags: string[]
  registeredAt: string
  status: 'production' | 'staging' | 'deprecated'
}

export interface Deployment {
  id: string
  modelName: string
  modelVersion: string
  targetDevices: string[]
  strategy: 'Rolling Update' | 'Canary (20%)' | 'Immediate'
  status: 'Active' | 'In Progress' | 'Failed' | 'Rolled Back'
  progressPct: number
  deployedBy: string
  deployedAt: string
  rollbackVersion?: string
}

export interface InferenceSample {
  id: string
  timestamp: string
  camera: string
  objects: { label: string; confidence: number; color: string }[]
  fps: number
  latencyMs: number
  resolution: string
}

export type ClassCategory = 'PPE' | 'Vehicle' | 'Person' | 'Hazard' | 'Object' | 'Custom'

export interface PredictionClass {
  id: number
  label: string
  category: ClassCategory
  color: string
  confidenceThreshold: number
  enabled: boolean
  detectionCount: number
  lastDetected: string | null
  description: string
}

export interface ClassProfile {
  id: string
  name: string
  modelId: string
  modelName: string
  classes: PredictionClass[]
  createdAt: string
  updatedAt: string
}

export const DEFAULT_COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
