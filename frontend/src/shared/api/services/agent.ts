import type { Camera, CameraGroup, EdgeDevice, BackendCamera, BackendCameraGroup, BackendDevice, CreateDevicePayload } from '../types/agent'
import { apiClient } from '../client'

const mapDevice = (device: BackendDevice): EdgeDevice => ({
  id: String(device.id), name: device.name, hardware: device.hardware,
  status: device.status === 'provisioning' ? 'offline' : device.status,
  ip: device.ip_address ?? 'Not assigned', agentVersion: 'Unknown', uptime: 'Unknown',
  cpuUsage: 0, gpuUsage: 0, ramUsedGb: 0, ramTotalGb: 0, tempC: 0,
  assignedCameras: 0, modelRunning: 'No model reported',
  lastHeartbeat: device.last_seen_at ? new Date(device.last_seen_at).toLocaleString() : 'Never',
})

const mapCamera = (camera: BackendCamera): Camera => ({
  id: String(camera.id), name: camera.name, zone: camera.zone, online: camera.enabled,
  alertCount: 0, thumbHue: 0,
  runtime: { resolution: 'Unknown', protocol: camera.source.split(':')[0].toUpperCase(), model: 'Unknown', fps: 0, roiZones: 0, lastHeartbeat: 'Unknown', streamUrl: camera.source },
})

const mapGroup = (group: BackendCameraGroup): CameraGroup => ({
  id: String(group.id), name: group.name, description: group.description ?? '', site: group.site,
  cameraIds: group.camera_ids.map(String), totalCameras: group.camera_ids.length,
  onlineCameras: 0, activeAlerts: 0, aggregateFps: 0, primaryModel: 'Unknown',
})

export const agentService = {
  createDevice: async (payload: CreateDevicePayload) => mapDevice(await apiClient.post<BackendDevice>('/agent/devices', payload)),
  listDevices: async () => (await apiClient.get<{ items: BackendDevice[] }>('/agent/devices')).items.map(mapDevice),
  getDevice: async (id: string) => mapDevice(await apiClient.get<BackendDevice>(`/agent/devices/${id}`)),
  listCameras: async () => (await apiClient.get<BackendCamera[]>('/agent/cameras')).map(mapCamera),
  getCamera: async (id: string) => mapCamera(await apiClient.get<BackendCamera>(`/agent/cameras/${id}`)),
  listCameraGroups: async () => (await apiClient.get<BackendCameraGroup[]>('/agent/camera-groups')).map(mapGroup),
  getCameraGroup: async (id: string) => mapGroup(await apiClient.get<BackendCameraGroup>(`/agent/camera-groups/${id}`)),
  listSnapshots: (cameraId?: string) => apiClient.get<unknown[]>('/agent/snapshots', { query: { cameraId } }),
}
