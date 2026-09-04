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
  tempC: number
  assignedCameras: number
  modelRunning: string
  lastHeartbeat: string
}

export const mockDevices: EdgeDevice[] = [
  {
    id: 'EDGE-NX-01',
    name: 'Jetson Orin NX Alpha',
    hardware: 'NVIDIA Jetson Orin NX 16GB',
    status: 'online',
    ip: '192.168.1.120',
    agentVersion: 'v2.4.1',
    uptime: '18d 6h 42m',
    cpuUsage: 48,
    gpuUsage: 78,
    ramUsedGb: 11.2,
    ramTotalGb: 16,
    tempC: 64,
    assignedCameras: 3,
    modelRunning: 'YOLOv11-Enterprise v2.1.0',
    lastHeartbeat: '2s ago',
  },
  {
    id: 'EDGE-AGX-02',
    name: 'Jetson AGX Orin Heavy',
    hardware: 'NVIDIA Jetson AGX Orin 64GB',
    status: 'online',
    ip: '192.168.1.121',
    agentVersion: 'v2.4.1',
    uptime: '42d 12h 10m',
    cpuUsage: 34,
    gpuUsage: 62,
    ramUsedGb: 28.4,
    ramTotalGb: 64,
    tempC: 58,
    assignedCameras: 6,
    modelRunning: 'RT-DETR-Large v1.4.0',
    lastHeartbeat: '1s ago',
  },
  {
    id: 'EDGE-BOX-03',
    name: 'Industrial AI Box 03',
    hardware: 'Rockchip RK3588 NPU 6TOPS',
    status: 'degraded',
    ip: '192.168.1.125',
    agentVersion: 'v2.3.8',
    uptime: '4d 2h 15m',
    cpuUsage: 89,
    gpuUsage: 94,
    ramUsedGb: 7.4,
    ramTotalGb: 8,
    tempC: 78,
    assignedCameras: 2,
    modelRunning: 'YOLOv11n-Nano v2.0.0',
    lastHeartbeat: '8s ago',
  },
  {
    id: 'EDGE-RPI-04',
    name: 'Perimeter Sensor Gateway',
    hardware: 'Raspberry Pi 5 + Hailo-8 NPU',
    status: 'online',
    ip: '192.168.1.130',
    agentVersion: 'v2.4.1',
    uptime: '9d 14h 50m',
    cpuUsage: 26,
    gpuUsage: 45,
    ramUsedGb: 3.8,
    ramTotalGb: 8,
    tempC: 52,
    assignedCameras: 1,
    modelRunning: 'ByteTrack-ReID v1.2.0',
    lastHeartbeat: '3s ago',
  },
  {
    id: 'EDGE-NX-05',
    name: 'Warehouse Node Vault',
    hardware: 'NVIDIA Jetson Orin Nano 8GB',
    status: 'offline',
    ip: '192.168.1.142',
    agentVersion: 'v2.4.0',
    uptime: '0m',
    cpuUsage: 0,
    gpuUsage: 0,
    ramUsedGb: 0,
    ramTotalGb: 8,
    tempC: 0,
    assignedCameras: 0,
    modelRunning: 'None',
    lastHeartbeat: '28m ago',
  },
]

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

export const mockCameraGroups: CameraGroup[] = [
  {
    id: 'GRP-01',
    name: 'Manufacturing Sector Bay A',
    description: 'Robotic assembly line, CNC cells and personnel corridors',
    site: 'Facility Site 1 — North Wing',
    cameraIds: ['CAM-01', 'CAM-02'],
    totalCameras: 2,
    onlineCameras: 2,
    activeAlerts: 2,
    aggregateFps: 60,
    primaryModel: 'YOLOv11-Enterprise',
  },
  {
    id: 'GRP-02',
    name: 'Heavy Assembly & Foundry',
    description: 'High-temperature casting bays, crane operation zones and PPE checkpoints',
    site: 'Facility Site 1 — Central Hall',
    cameraIds: ['CAM-03'],
    totalCameras: 1,
    onlineCameras: 1,
    activeAlerts: 5,
    aggregateFps: 28,
    primaryModel: 'YOLOv11-Enterprise',
  },
  {
    id: 'GRP-03',
    name: 'Logistics & Automated Freight',
    description: 'Forklift transit aisles, automated palletizers and loading docks',
    site: 'Logistics Distribution Center',
    cameraIds: ['CAM-04'],
    totalCameras: 1,
    onlineCameras: 1,
    activeAlerts: 0,
    aggregateFps: 25,
    primaryModel: 'YOLOv11-Enterprise',
  },
  {
    id: 'GRP-04',
    name: 'High-Security Perimeter Vault',
    description: 'Server room access, biometric perimeter and hazardous chemical storage',
    site: 'Facility Site 2 — Secure Zone',
    cameraIds: ['CAM-05'],
    totalCameras: 1,
    onlineCameras: 0,
    activeAlerts: 0,
    aggregateFps: 0,
    primaryModel: 'ByteTrack-ReID',
  },
]
