export interface Camera {
  id: string
  name: string
  zone: string
  online: boolean
  alertCount: number
  thumbHue: number
  runtime: {
    resolution: string
    protocol: string
    model: string
    fps: number
    roiZones: number
    lastHeartbeat: string
    streamUrl?: string
  }
}

export interface EdgeDevice {
  id: string
  name: string
  hardware: string
  status: 'online' | 'degraded' | 'offline'
  ip: string
  agentVersion: string
  uptime: string
  cpuUsage: number
  gpuUsage: number
  ramUsedGb: number
  ramTotalGb: number
  diskUsage: number
  tempC: number
  assignedCameras: number
  modelRunning: string
  lastHeartbeat: string
}

export interface CameraGroup {
  id: string
  name: string
  description: string
  site: string
  cameraIds: string[]
  totalCameras: number
  onlineCameras: number
  activeAlerts: number
  aggregateFps: number
  primaryModel: string
}
