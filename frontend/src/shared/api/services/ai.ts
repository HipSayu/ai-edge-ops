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
  const short = (r: string | null) => r?.split('/').pop()?.split('@')[0] ?? '-'
  const status: Deployment['status'] = d.in_sync
    ? 'Active'
    : d.runtime_status === 'failed'
      ? 'Failed'
      : 'In Progress'
  return {
    id: d.device_id,
    modelName: short(d.desired_image),
    modelVersion: short(d.active_image),
    targetDevices: [d.name],
    strategy: 'Immediate',
    status,
    progressPct: d.in_sync ? 100 : d.runtime_status === 'applying' ? 50 : 0,
    deployedBy: 'Backend',
    deployedAt: d.updated_at ?? '',
  }
}

export const aiService = {
  listModels: async () => (await apiClient.get<ModelImageRecord[]>('/models')).map(mapModel),
  getModel: (tag: string) => apiClient.get<ModelImageRecord>(`/models/${encodeURIComponent(tag)}`).then(mapModel),
  listDeployments: async () => (await apiClient.get<DeploymentRecord[]>('/deployments')).map(mapDeployment),
  createDeployment: (payload: { device_id: string; image: string; config?: Record<string, unknown> }) =>
    apiClient.post<DeploymentRecord>('/deployments', payload),
  listInferenceSamples: (cameraId?: string) => apiClient.get<InferenceSample[]>('/violations', { query: { device_id: cameraId } }),
  updateClassConfig: (payload: unknown) => apiClient.patch<unknown>('/models/class-config', payload),
}
