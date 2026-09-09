export interface ModelArtifact { id: string; versionId?: string; name: string; version: string; architecture: string; format: 'TensorRT FP16' | 'ONNX FP16' | 'TensorRT INT8' | 'TorchScript'; sizeMb: number; mAP50: number; latencyBenchmarkMs: number; inputResolution: string; targetHardware: string; tags: string[]; registeredAt: string; status: 'production' | 'staging' | 'deprecated' }
export interface Deployment { id: string; modelName: string; modelVersion: string; targetDevices: string[]; strategy: 'Rolling Update' | 'Canary (20%)' | 'Immediate'; status: 'Active' | 'In Progress' | 'Failed' | 'Rolled Back'; progressPct: number; deployedBy: string; deployedAt: string; rollbackVersion?: string }
export interface InferenceSample { id: string; timestamp: string; camera: string; objects: { label: string; confidence: number; color: string }[]; fps: number; latencyMs: number; resolution: string }
export type ClassCategory = 'PPE' | 'Vehicle' | 'Person' | 'Hazard' | 'Object' | 'Custom'
export interface PredictionClass { id: number; label: string; category: ClassCategory; color: string; confidenceThreshold: number; enabled: boolean; detectionCount: number; lastDetected: string | null; description: string }
export interface ClassProfile { id: string; name: string; modelId: string; modelName: string; classes: PredictionClass[]; createdAt: string; updatedAt: string }
export type ModelRecord = { id: number; name: string; architecture: string; task: string; description: string | null; created_at: string }
export type ModelVersionRecord = { id: number; model_id: number; version: string; format: ModelArtifact['format']; status: string; size_mb: number | null; metrics: Record<string, number | string> }
export type ModelWithVersionsRecord = ModelRecord & { versions: ModelVersionRecord[] }
export type DeploymentRecord = { id: number; device_id: number; model_version_id: number; status: string; created_at: string; activated_at: string | null }
export type InferenceRecord = InferenceSample
export const DEFAULT_COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
