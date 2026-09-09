import type { Camera, CameraGroup, EdgeDevice, BackendCamera, BackendCameraGroup, BackendDevice, BackendMetricSample, CreateDevicePayload } from '../types/agent'
import { apiClient } from '../client'

const round = (n: number, d = 0) => Math.round(n * 10 ** d) / 10 ** d

const formatUptime = (seconds: number | null): string => {
  if (!seconds || seconds < 0) return 'Unknown'
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return `${d}d ${h}h`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

const mapDevice = (device: BackendDevice, latest?: BackendMetricSample): EdgeDevice => ({
  id: device.device_id, name: device.name, hardware: device.hardware,
  status: device.status === 'provisioning' ? 'offline' : device.status,
  ip: device.ip_address ?? 'Not assigned',
  agentVersion: device.agent_version ?? 'Unknown',
  uptime: formatUptime(device.uptime_s),
  cpuUsage: round(latest?.cpu_percent ?? 0),
  gpuUsage: round(latest?.gpu_percent ?? 0),
  ramUsedGb: round((latest?.mem_used_mb ?? 0) / 1024, 1),
  ramTotalGb: round((latest?.mem_total_mb ?? 0) / 1024, 1),
  diskUsage: round(latest?.disk_percent ?? 0),
  tempC: round(latest?.temperature_c ?? 0),
  assignedCameras: 0,
  modelRunning: device.active_image ? (device.active_image.split('/').pop() ?? device.active_image) : 'No model reported',
  lastHeartbeat: device.last_seen_at ? new Date(device.last_seen_at).toLocaleString() : 'Never',
})

const latestMetrics = async (deviceId: string): Promise<BackendMetricSample | undefined> => {
  try {
    const page = await apiClient.get<{ items: BackendMetricSample[] }>(
      `/agent/devices/${deviceId}/metrics`, { query: { page_size: 1 } },
    )
    return page.items[0]
  } catch {
    return undefined
  }
}

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
  listDevices: async () => {
    const { items } = await apiClient.get<{ items: BackendDevice[] }>('/agent/devices')
    return Promise.all(items.map(async (d) => mapDevice(d, await latestMetrics(d.device_id))))
  },
  getDevice: async (id: string) => {
    const device = await apiClient.get<BackendDevice>(`/agent/devices/${id}`)
    return mapDevice(device, await latestMetrics(device.device_id))
  },
  listDeviceMetrics: async (deviceId: string) => {
    const page = await apiClient.get<{ items: BackendMetricSample[] }>(
      `/agent/devices/${deviceId}/metrics`, { query: { page_size: 100 } },
    )
    return page.items
  },
  listCameras: async () => (await apiClient.get<BackendCamera[]>('/agent/cameras')).map(mapCamera),
  getCamera: async (id: string) => mapCamera(await apiClient.get<BackendCamera>(`/agent/cameras/${id}`)),
  listCameraGroups: async () => (await apiClient.get<BackendCameraGroup[]>('/agent/camera-groups')).map(mapGroup),
  createCameraGroup: async (payload: { name: string; description?: string; site: string; camera_ids: number[] }) =>
    mapGroup(await apiClient.post<BackendCameraGroup>('/agent/camera-groups', payload)),
  getCameraGroup: async (id: string) => mapGroup(await apiClient.get<BackendCameraGroup>(`/agent/camera-groups/${id}`)),
  listSnapshots: (cameraId?: string) => apiClient.get<unknown[]>('/agent/snapshots', { query: { cameraId } }),
}
