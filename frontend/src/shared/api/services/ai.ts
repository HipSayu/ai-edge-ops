import type { Deployment, InferenceSample, ModelArtifact } from '../types/ai'
import type { DeploymentRecord, ModelImageRecord } from '../types/ai'
import { apiClient } from '../client'

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

const mapDeployment = (d: DeploymentRecord): Deployment => {
  const status = d.status.toLowerCase()
  const shortImage = d.image.split('/').pop() ?? d.image
  return {
    id: String(d.id),
    modelName: shortImage,
    modelVersion: shortImage,
    targetDevices: [String(d.device_id)],
    strategy: 'Immediate',
    status: status === 'active' ? 'Active' : status === 'failed' ? 'Failed' : 'In Progress',
    progressPct: status === 'active' ? 100 : 0,
    deployedBy: 'Backend',
    deployedAt: d.activated_at ?? d.created_at,
  }
}

export const aiService = {
  listModels: async () => (await apiClient.get<ModelImageRecord[]>('/models')).map(mapModel),
  getModel: (tag: string) => apiClient.get<ModelImageRecord>(`/models/${encodeURIComponent(tag)}`).then(mapModel),
  listDeployments: async () => (await apiClient.get<{ items: DeploymentRecord[] }>('/deployments')).items.map(mapDeployment),
  createDeployment: (payload: { device_id: number; image: string; config?: Record<string, unknown>; activate_now?: boolean }) =>
    apiClient.post<DeploymentRecord>('/deployments', payload),
  getDeployment: (id: string) => apiClient.get<Deployment>(`/deployments/${id}`),
  listInferenceSamples: (cameraId?: string) => apiClient.get<InferenceSample[]>('/violations', { query: { device_id: cameraId } }),
  updateClassConfig: (payload: unknown) => apiClient.patch<unknown>('/models/class-config', payload),
}
