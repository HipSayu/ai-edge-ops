import type { Deployment, InferenceSample, ModelArtifact, ModelRegistryItem, ClassConfigItem } from '@/modules/ai/types/ai'
import type { DeploymentCreate, DeploymentRecord, ModelImageRecord } from '@/modules/ai/types/ai'
import { apiClient } from '@/shared/api/client'

const registryTasks: ModelRegistryItem['task'][] = ['detection', 'pose', 'segmentation', 'classification']

const mapRegistryItem = (m: ModelImageRecord): ModelRegistryItem => ({
  id: m.tag,
  name: m.name,
  version: m.tag,
  task: registryTasks.find((t) => m.task?.toLowerCase().startsWith(t.slice(0, 4))) ?? 'detection',
  framework: m.base ?? '—',
  precision: '—',
  inputResolution: m.params_m ? `${m.params_m}M params` : '—',
  latencyOrinMs: m.latency_ms ?? 0,
  mAP: m.map50_95 ?? 0,
  fileSizeMb: Math.round(m.size_bytes / 1e5) / 10,
  classes: m.classes,
  description: m.pinned_ref,
  activeDeployments: 0,
  updatedAt: m.created_at ?? '',
})

const mapModel = (m: ModelImageRecord): ModelArtifact => ({
  id: m.tag,
  ref: m.pinned_ref,
  name: m.name,
  version: m.tag,
  architecture: m.base ?? '—',
  format: m.platforms.join(' + ') || 'multi-arch',
  sizeMb: Math.round(m.size_bytes / 1e5) / 10,
  mAP50: m.map50_95 ?? 0,
  latencyBenchmarkMs: m.latency_ms ?? 0,
  inputResolution: m.params_m ? `${m.params_m}M params` : '—',
  targetHardware: m.platforms.join(', ') || '—',
  tags: [m.task ?? 'model', ...m.classes],
  registeredAt: m.created_at ?? '',
  status: 'production',
})

const deploymentStatus: Record<DeploymentRecord['status'], Deployment['status']> = {
  PENDING: 'In Progress', IN_PROGRESS: 'In Progress', SUCCEEDED: 'Active',
  FAILED: 'Failed', REMOVING: 'Rolled Back', REMOVED: 'Rolled Back',
}
const deploymentProgress: Record<DeploymentRecord['status'], number> = {
  PENDING: 0, IN_PROGRESS: 50, SUCCEEDED: 100, FAILED: 0, REMOVING: 50, REMOVED: 100,
}

const mapDeployment = (d: DeploymentRecord): Deployment => {
  const image = String(d.spec.image_uri ?? '-').split('/').pop() ?? '-'
  return {
    id: d.id,
    modelName: String(d.spec.model_id ?? d.spec.name ?? image),
    modelVersion: `${image}:${String(d.spec.image_tag ?? 'latest')}`,
    targetDevices: [d.node_id],
    strategy: 'Immediate',
    status: deploymentStatus[d.status] ?? 'In Progress',
    progressPct: deploymentProgress[d.status] ?? 0,
    deployedBy: 'Cloud API',
    deployedAt: d.updated_at ?? d.created_at ?? '',
  }
}

export const aiService = {
  listModels: async () => (await apiClient.get<ModelImageRecord[]>('/models')).map(mapModel),
  listRegistry: async (): Promise<ModelRegistryItem[]> => (await apiClient.get<ModelImageRecord[]>('/models')).map(mapRegistryItem),
  listClassConfig: () => apiClient.get<ClassConfigItem[]>('/models/class-config'),
  getModel: (tag: string) => apiClient.get<ModelImageRecord>(`/models/${encodeURIComponent(tag)}`).then(mapModel),
  listDeployments: async () => (await apiClient.get<DeploymentRecord[]>('/deployments')).map(mapDeployment),
  createDeployment: (payload: DeploymentCreate) => apiClient.post<DeploymentRecord>('/deployments', payload),
  removeDeployment: (id: string) => apiClient.delete<DeploymentRecord>(`/deployments/${id}`),
  listInferenceSamples: (cameraId?: string) => apiClient.get<InferenceSample[]>('/violations', { query: { device_id: cameraId } }),
  updateClassConfig: (payload: unknown) => apiClient.patch<unknown>('/models/class-config', payload),
}
