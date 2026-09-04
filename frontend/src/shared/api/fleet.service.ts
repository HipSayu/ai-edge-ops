import type { Camera } from '@/modules/fleet/mock/cameras'
import type { CameraGroup, EdgeDevice } from '@/modules/fleet/mock/fleet'
import { apiClient } from './client'

export const fleetService = {
  listDevices: () => apiClient.get<EdgeDevice[]>('/fleet/devices'),
  getDevice: (deviceId: string) => apiClient.get<EdgeDevice>(`/fleet/devices/${deviceId}`),
  listCameras: () => apiClient.get<Camera[]>('/fleet/cameras'),
  getCamera: (cameraId: string) => apiClient.get<Camera>(`/fleet/cameras/${cameraId}`),
  listCameraGroups: () => apiClient.get<CameraGroup[]>('/fleet/camera-groups'),
  getCameraGroup: (groupId: string) => apiClient.get<CameraGroup>(`/fleet/camera-groups/${groupId}`),
  listSnapshots: (cameraId?: string) => apiClient.get<unknown[]>('/fleet/snapshots', { query: { cameraId } }),
}
