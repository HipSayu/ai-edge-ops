import type { Deployment, InferenceSample, ModelArtifact } from '../types/ai'
import type { DeploymentRecord, ModelRecord } from '../types/ai'
import { apiClient } from '../client'

const mapModel = (model: ModelRecord): ModelArtifact => ({
  id: String(model.id), name: model.name, version: 'unversioned', architecture: model.architecture,
  format: 'TorchScript', sizeMb: 0, mAP50: 0, latencyBenchmarkMs: 0, inputResolution: 'Unknown',
  targetHardware: 'Unknown', tags: [model.task], registeredAt: model.created_at, status: 'staging',
})

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
  listModels: async () => (await apiClient.get<{ items: ModelRecord[] }>('/models')).items.map(mapModel),
  getModel: (id: string) => apiClient.get<ModelArtifact>(`/models/${id}`),
  listDeployments: async () => (await apiClient.get<{ items: DeploymentRecord[] }>('/deployments')).items.map(mapDeployment),
  getDeployment: (id: string) => apiClient.get<Deployment>(`/deployments/${id}`),
  listInferenceSamples: (cameraId?: string) => apiClient.get<InferenceSample[]>('/violations', { query: { device_id: cameraId } }),
  updateClassConfig: (payload: unknown) => apiClient.patch<unknown>('/models/class-config', payload),
}
