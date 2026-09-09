import type { Deployment, InferenceSample, ModelArtifact } from '../types/ai'
import type { DeploymentRecord, ModelRecord, ModelWithVersionsRecord } from '../types/ai'
import { apiClient } from '../client'

const mapModel = (model: ModelWithVersionsRecord): ModelArtifact => {
  const version = model.versions[0]
  const metricNumber = (key: string) => typeof version?.metrics?.[key] === 'number' ? version.metrics[key] as number : 0
  const metricText = (key: string) => typeof version?.metrics?.[key] === 'string' ? version.metrics[key] as string : 'Unknown'
  return {
  id: String(model.id), versionId: version ? String(version.id) : undefined, name: model.name, version: version?.version ?? '—', architecture: model.architecture,
  format: version?.format ?? 'TorchScript', sizeMb: version?.size_mb ?? 0, mAP50: metricNumber('mAP50'),
  latencyBenchmarkMs: metricNumber('latency_ms'), inputResolution: metricText('input_resolution'),
  targetHardware: metricText('target_hardware'), tags: [model.task], registeredAt: model.created_at,
  status: version?.status === 'production' ? 'production' : version?.status === 'deprecated' ? 'deprecated' : 'staging',
  }
}

const mapDeployment = (deployment: DeploymentRecord): Deployment => {
  const status = deployment.status.toLowerCase()
  return {
    id: String(deployment.id), modelName: `Model version ${deployment.model_version_id}`,
    modelVersion: String(deployment.model_version_id), targetDevices: [String(deployment.device_id)],
    strategy: 'Immediate', status: status === 'active' ? 'Active' : status === 'failed' ? 'Failed' : 'In Progress',
    progressPct: status === 'active' ? 100 : 0, deployedBy: 'Backend', deployedAt: deployment.activated_at ?? deployment.created_at,
  }
}

export const aiService = {
  listModels: async () => Promise.all((await apiClient.get<{ items: ModelRecord[] }>('/models')).items.map(async (model) => mapModel(await apiClient.get<ModelWithVersionsRecord>(`/models/${model.id}`)))),
  createModel: (payload: { name: string; task: string; architecture: string; description?: string }) => apiClient.post<ModelRecord>('/models', payload),
  getModel: (id: string) => apiClient.get<ModelArtifact>(`/models/${id}`),
  listDeployments: async () => (await apiClient.get<{ items: DeploymentRecord[] }>('/deployments')).items.map(mapDeployment),
  createDeployment: (payload: { device_id: number; model_version_id: number; config?: Record<string, unknown>; activate_now?: boolean }) => apiClient.post<DeploymentRecord>('/deployments', payload),
  getDeployment: (id: string) => apiClient.get<Deployment>(`/deployments/${id}`),
  listInferenceSamples: (cameraId?: string) => apiClient.get<InferenceSample[]>('/violations', { query: { device_id: cameraId } }),
  updateClassConfig: (payload: unknown) => apiClient.patch<unknown>('/models/class-config', payload),
}
