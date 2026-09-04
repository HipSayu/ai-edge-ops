export interface ModelArtifact {
  id: string
  name: string
  version: string
  architecture: string
  format: 'TensorRT FP16' | 'ONNX FP16' | 'TensorRT INT8' | 'TorchScript'
  sizeMb: number
  mAP50: number
  latencyBenchmarkMs: number
  inputResolution: string
  targetHardware: string
  tags: string[]
  registeredAt: string
  status: 'production' | 'staging' | 'deprecated'
}

export const mockModels: ModelArtifact[] = [
  {
    id: 'MOD-001',
    name: 'YOLOv11-Enterprise',
    version: 'v2.1.0',
    architecture: 'YOLOv11x-PPE-Custom',
    format: 'TensorRT FP16',
    sizeMb: 48.6,
    mAP50: 94.8,
    latencyBenchmarkMs: 14.2,
    inputResolution: '640×640',
    targetHardware: 'NVIDIA Orin / Jetson',
    tags: ['PPE', 'Hard Hat', 'Safety Vest', 'Worker'],
    registeredAt: '2026-08-28',
    status: 'production',
  },
  {
    id: 'MOD-002',
    name: 'RT-DETR-Large',
    version: 'v1.4.0',
    architecture: 'RT-DETR-ResNet50',
    format: 'TensorRT FP16',
    sizeMb: 112.4,
    mAP50: 96.2,
    latencyBenchmarkMs: 22.8,
    inputResolution: '640×640',
    targetHardware: 'NVIDIA Orin AGX',
    tags: ['Perimeter', 'Vehicle', 'Heavy Machinery'],
    registeredAt: '2026-08-15',
    status: 'production',
  },
  {
    id: 'MOD-003',
    name: 'YOLOv11n-Nano',
    version: 'v2.0.0',
    architecture: 'YOLOv11n-Pruned',
    format: 'ONNX FP16',
    sizeMb: 9.8,
    mAP50: 87.5,
    latencyBenchmarkMs: 8.4,
    inputResolution: '416×416',
    targetHardware: 'Rockchip RK3588 / RPi5',
    tags: ['Low-Power', 'Intrusion', 'Person'],
    registeredAt: '2026-08-20',
    status: 'production',
  },
  {
    id: 'MOD-004',
    name: 'ByteTrack-ReID',
    version: 'v1.2.0',
    architecture: 'OSNet-AIN-ReID',
    format: 'TensorRT FP16',
    sizeMb: 24.1,
    mAP50: 91.4,
    latencyBenchmarkMs: 11.6,
    inputResolution: '256×128',
    targetHardware: 'NVIDIA Orin / Jetson',
    tags: ['ReID', 'Multi-Camera', 'Tracking'],
    registeredAt: '2026-08-10',
    status: 'production',
  },
  {
    id: 'MOD-005',
    name: 'YOLOv11-HazardDetection',
    version: 'v2.2.0-rc1',
    architecture: 'YOLOv11l-Multiclass',
    format: 'TensorRT FP16',
    sizeMb: 54.2,
    mAP50: 95.1,
    latencyBenchmarkMs: 16.5,
    inputResolution: '640×640',
    targetHardware: 'NVIDIA Orin Series',
    tags: ['Chemical Spill', 'Smoke', 'Fire Hazard'],
    registeredAt: '2026-09-02',
    status: 'staging',
  },
]

export interface Deployment {
  id: string
  modelName: string
  modelVersion: string
  targetDevices: string[]
  strategy: 'Rolling Update' | 'Canary (20%)' | 'Immediate'
  status: 'Active' | 'In Progress' | 'Failed' | 'Rolled Back'
  progressPct: number
  deployedBy: string
  deployedAt: string
  rollbackVersion?: string
}

export const mockDeployments: Deployment[] = [
  {
    id: 'DEP-8401',
    modelName: 'YOLOv11-Enterprise',
    modelVersion: 'v2.1.0',
    targetDevices: ['EDGE-NX-01', 'EDGE-AGX-02'],
    strategy: 'Rolling Update',
    status: 'Active',
    progressPct: 100,
    deployedBy: 'Hop Do (Lead Operations)',
    deployedAt: 'Today, 08:30',
    rollbackVersion: 'v2.0.4',
  },
  {
    id: 'DEP-8402',
    modelName: 'RT-DETR-Large',
    modelVersion: 'v1.4.0',
    targetDevices: ['EDGE-AGX-02'],
    strategy: 'Immediate',
    status: 'Active',
    progressPct: 100,
    deployedBy: 'Alex Chen (MLOps)',
    deployedAt: 'Yesterday, 16:45',
    rollbackVersion: 'v1.3.2',
  },
  {
    id: 'DEP-8403',
    modelName: 'YOLOv11-HazardDetection',
    modelVersion: 'v2.2.0-rc1',
    targetDevices: ['EDGE-NX-01'],
    strategy: 'Canary (20%)',
    status: 'In Progress',
    progressPct: 65,
    deployedBy: 'Hop Do (Lead Operations)',
    deployedAt: 'Today, 10:15',
    rollbackVersion: 'v2.1.0',
  },
  {
    id: 'DEP-8399',
    modelName: 'ByteTrack-ReID',
    modelVersion: 'v1.2.1',
    targetDevices: ['EDGE-RPI-04'],
    strategy: 'Rolling Update',
    status: 'Failed',
    progressPct: 40,
    deployedBy: 'System Auto-Rollout',
    deployedAt: '2 days ago',
    rollbackVersion: 'v1.2.0',
  },
]

export interface InferenceSample {
  id: string
  timestamp: string
  camera: string
  objects: { label: string; confidence: number; color: string }[]
  fps: number
  latencyMs: number
  resolution: string
}

export const mockInferenceSamples: InferenceSample[] = [
  {
    id: 'INF-901',
    timestamp: '11:45:32.410',
    camera: 'CAM-03',
    objects: [
      { label: 'Person #409', confidence: 98.7, color: 'var(--accent)' },
      { label: 'No Hard Hat', confidence: 96.2, color: 'var(--critical)' },
      { label: 'Forklift #02', confidence: 99.1, color: 'var(--info)' },
    ],
    fps: 28,
    latencyMs: 14.8,
    resolution: '1920×1080',
  },
  {
    id: 'INF-902',
    timestamp: '11:45:31.980',
    camera: 'CAM-01',
    objects: [
      { label: 'Person #091', confidence: 97.4, color: 'var(--accent)' },
      { label: 'Hard Hat', confidence: 96.4, color: 'var(--good)' },
      { label: 'No Safety Vest', confidence: 94.8, color: 'var(--warning)' },
    ],
    fps: 30,
    latencyMs: 13.2,
    resolution: '1920×1080',
  },
  {
    id: 'INF-903',
    timestamp: '11:45:30.550',
    camera: 'CAM-02',
    objects: [
      { label: 'Intrusion Polygon', confidence: 98.1, color: 'var(--critical)' },
      { label: 'Person #077', confidence: 99.0, color: 'var(--accent)' },
    ],
    fps: 30,
    latencyMs: 12.6,
    resolution: '1920×1080',
  },
  {
    id: 'INF-904',
    timestamp: '11:45:29.120',
    camera: 'CAM-04',
    objects: [
      { label: 'Pallet Stacker', confidence: 97.8, color: 'var(--good)' },
      { label: 'Person #112', confidence: 96.5, color: 'var(--accent)' },
      { label: 'Safety Vest', confidence: 98.2, color: 'var(--good)' },
      { label: 'Hard Hat', confidence: 95.8, color: 'var(--good)' },
    ],
    fps: 25,
    latencyMs: 16.4,
    resolution: '1280×720',
  },
]
