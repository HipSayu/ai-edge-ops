export interface MonitoringPoint {
  time: string
  cpuAvg: number
  gpuAvg: number
  ramAvg: number
  fpsAvg: number
  latencyP50: number
  latencyP95: number
  networkMbps: number
}

export const mockMonitoringTimeline: MonitoringPoint[] = Array.from({ length: 24 }, (_, i) => {
  const h = String(Math.floor(i)).padStart(2, '0') + ':00'
  return {
    time: h,
    cpuAvg: Math.round(35 + Math.sin(i * 0.5) * 15 + (i % 3) * 4),
    gpuAvg: Math.round(65 + Math.cos(i * 0.4) * 16 + (i % 2) * 5),
    ramAvg: Math.round(58 + (i % 4) * 3),
    fpsAvg: Math.round(28 + Math.sin(i * 0.3) * 2),
    latencyP50: Math.round(14 + (i % 2) * 2),
    latencyP95: Math.round(24 + (i % 3) * 4),
    networkMbps: Math.round(45 + Math.sin(i * 0.6) * 12),
  }
})

export interface TimelineEvent {
  id: string
  timestamp: string
  source: 'Edge Device' | 'AI Inference' | 'Camera' | 'Deployment' | 'Security'
  severity: 'info' | 'warning' | 'critical' | 'success'
  title: string
  details: string
  targetNode: string
}

export const mockEvents: TimelineEvent[] = [
  {
    id: 'EVT-1092',
    timestamp: '11:45:32',
    source: 'AI Inference',
    severity: 'critical',
    title: 'Critical PPE Violation Triggered',
    details: 'Missing hard hat detected on subject #128 in Sector C Bay 4 (96.2% confidence)',
    targetNode: 'EDGE-NX-01 (CAM-03)',
  },
  {
    id: 'EVT-1091',
    timestamp: '11:40:15',
    source: 'Deployment',
    severity: 'info',
    title: 'Canary Rollout Started',
    details: 'Deploying YOLOv11-HazardDetection v2.2.0-rc1 to 1 canary node',
    targetNode: 'EDGE-NX-01',
  },
  {
    id: 'EVT-1090',
    timestamp: '11:32:04',
    source: 'Edge Device',
    severity: 'warning',
    title: 'GPU Thermal Threshold Warning',
    details: 'Core temperature reached 78°C on Industrial AI Box 03 — fan boost engaged',
    targetNode: 'EDGE-BOX-03',
  },
  {
    id: 'EVT-1089',
    timestamp: '11:15:20',
    source: 'Camera',
    severity: 'success',
    title: 'RTSP Stream Reconnected',
    details: 'Stream synchronized for Assembly Line Alpha (1080p60 RTSP/H.264)',
    targetNode: 'CAM-02',
  },
  {
    id: 'EVT-1088',
    timestamp: '10:50:11',
    source: 'Security',
    severity: 'critical',
    title: 'Perimeter Boundary Breach',
    details: 'Virtual geofenced intrusion without RFID credential event in last 60s',
    targetNode: 'CAM-02',
  },
  {
    id: 'EVT-1087',
    timestamp: '10:30:00',
    source: 'Edge Device',
    severity: 'success',
    title: 'Daily Node Heartbeat Audit Completed',
    details: '4 of 5 Edge Nodes reported healthy metrics, 0 zombie inference processes',
    targetNode: 'Cluster Master',
  },
]

export interface LogEntry {
  id: string
  timestamp: string
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  component: 'EdgeAgent' | 'TensorRT' | 'StreamDaemon' | 'Deployer'
  node: string
  message: string
}

export const mockLogs: LogEntry[] = [
  {
    id: 'LOG-501',
    timestamp: '11:45:33.204',
    level: 'INFO',
    component: 'TensorRT',
    node: 'EDGE-NX-01',
    message: '[CUDA:0] Engine YOLOv11-Enterprise execution completed in 14.28ms | Detections: 3',
  },
  {
    id: 'LOG-502',
    timestamp: '11:45:32.410',
    level: 'WARN',
    component: 'EdgeAgent',
    node: 'EDGE-NX-01',
    message: 'Event dispatch: Alert #128 queued for notification webhook -> HTTP 200 OK',
  },
  {
    id: 'LOG-503',
    timestamp: '11:44:18.012',
    level: 'INFO',
    component: 'StreamDaemon',
    node: 'EDGE-NX-01',
    message: 'RTSP buffer CAM-01 healthy, 0 dropped frames in past 10,000 packets',
  },
  {
    id: 'LOG-504',
    timestamp: '11:42:01.890',
    level: 'DEBUG',
    component: 'Deployer',
    node: 'Cluster',
    message: 'Syncing SHA256 checksum for model artifact yolo11_hazard_rc1.engine (0x9a8f1b2c)',
  },
  {
    id: 'LOG-505',
    timestamp: '11:40:15.550',
    level: 'INFO',
    component: 'Deployer',
    node: 'EDGE-NX-01',
    message: 'Warmup inference completed for canary model YOLOv11-HazardDetection: 16.4ms avg',
  },
  {
    id: 'LOG-506',
    timestamp: '11:32:04.110',
    level: 'WARN',
    component: 'EdgeAgent',
    node: 'EDGE-BOX-03',
    message: 'Hardware thermal sensor alert: GPU temp 78C > warn limit 75C, adjusting PWM fan speed to 90%',
  },
  {
    id: 'LOG-507',
    timestamp: '11:15:20.300',
    level: 'ERROR',
    component: 'StreamDaemon',
    node: 'EDGE-NX-05',
    message: 'RTSP socket connection timeout (192.168.1.142:554) after 30000ms: Host unreachable',
  },
  {
    id: 'LOG-508',
    timestamp: '11:10:05.105',
    level: 'DEBUG',
    component: 'TensorRT',
    node: 'EDGE-AGX-02',
    message: 'VRAM memory allocated: 28.4 GB / 64.0 GB (Peak usage: 44.3%)',
  },
]
