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
  }
}

export const mockCameras: Camera[] = [
  {
    id: 'CAM-01',
    name: 'Gate 01 — Main Entrance',
    zone: 'Perimeter Defense',
    online: true,
    alertCount: 2,
    thumbHue: 205,
    runtime: {
      resolution: '1920×1080',
      protocol: 'RTSP/H.264',
      model: 'YOLOv11-Enterprise',
      fps: 30,
      roiZones: 1,
      lastHeartbeat: '2s ago',
    },
  },
  {
    id: 'CAM-02',
    name: 'Assembly Line Alpha',
    zone: 'Production Sector B',
    online: true,
    alertCount: 0,
    thumbHue: 165,
    runtime: {
      resolution: '1920×1080',
      protocol: 'RTSP/H.264',
      model: 'YOLOv11-Enterprise',
      fps: 30,
      roiZones: 2,
      lastHeartbeat: '1s ago',
    },
  },
  {
    id: 'CAM-03',
    name: 'Main Factory Floor',
    zone: 'Production Sector C',
    online: true,
    alertCount: 5,
    thumbHue: 20,
    runtime: {
      resolution: '1920×1080',
      protocol: 'RTSP/H.264',
      model: 'YOLOv11-Enterprise',
      fps: 28,
      roiZones: 3,
      lastHeartbeat: '1s ago',
    },
  },
  {
    id: 'CAM-04',
    name: 'Logistics Warehouse',
    zone: 'Storage & Freight Bay',
    online: true,
    alertCount: 0,
    thumbHue: 260,
    runtime: {
      resolution: '1280×720',
      protocol: 'RTSP/H.265',
      model: 'YOLOv11-Enterprise',
      fps: 25,
      roiZones: 0,
      lastHeartbeat: '3s ago',
    },
  },
  {
    id: 'CAM-05',
    name: 'Restricted Server Vault',
    zone: 'Secure Zone D',
    online: false,
    alertCount: 0,
    thumbHue: 0,
    runtime: {
      resolution: '1920×1080',
      protocol: 'RTSP/H.264',
      model: 'YOLOv11-Enterprise',
      fps: 0,
      roiZones: 1,
      lastHeartbeat: '14m ago',
    },
  },
]
