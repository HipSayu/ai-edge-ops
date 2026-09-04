import type { Deployment, InferenceSample, ModelArtifact } from '@/modules/ai/mock/ai'
import { apiClient } from './client'

export const aiService = {
  listModels: () => apiClient.get<ModelArtifact[]>('/ai/models'),
  getModel: (modelId: string) => apiClient.get<ModelArtifact>(`/ai/models/${modelId}`),
  listDeployments: () => apiClient.get<Deployment[]>('/ai/deployments'),
  getDeployment: (deploymentId: string) => apiClient.get<Deployment>(`/ai/deployments/${deploymentId}`),
  listInferenceSamples: (cameraId?: string) =>
    apiClient.get<InferenceSample[]>('/ai/inference/samples', { query: { cameraId } }),
  updateClassConfig: (payload: unknown) => apiClient.patch<unknown>('/ai/class-config', payload),
}
