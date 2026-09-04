export type ClassCategory = 'PPE' | 'Vehicle' | 'Person' | 'Hazard' | 'Object' | 'Custom'

export interface PredictionClass {
  id: number
  label: string
  category: ClassCategory
  color: string
  confidenceThreshold: number
  enabled: boolean
  detectionCount: number
  lastDetected: string | null
  description: string
}

export interface ClassProfile {
  id: string
  name: string
  modelId: string
  modelName: string
  classes: PredictionClass[]
  createdAt: string
  updatedAt: string
}

export const DEFAULT_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
  '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
  '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
  '#ec4899', '#f43f5e',
]

export const mockClassProfiles: ClassProfile[] = [
  {
    id: 'CP-001',
    name: 'PPE Detection - Full Config',
    modelId: 'MOD-001',
    modelName: 'YOLOv11-Enterprise v2.1.0',
    createdAt: '2026-08-28',
    updatedAt: '2026-09-02',
    classes: [
      {
        id: 0,
        label: 'person',
        category: 'Person',
        color: '#3b82f6',
        confidenceThreshold: 0.5,
        enabled: true,
        detectionCount: 18420,
        lastDetected: '2026-09-04T10:22:00Z',
        description: 'Human worker presence',
      },
      {
        id: 1,
        label: 'hard_hat',
        category: 'PPE',
        color: '#f59e0b',
        confidenceThreshold: 0.6,
        enabled: true,
        detectionCount: 14320,
        lastDetected: '2026-09-04T10:21:58Z',
        description: 'Safety helmet / hard hat worn by worker',
      },
      {
        id: 2,
        label: 'safety_vest',
        category: 'PPE',
        color: '#22c55e',
        confidenceThreshold: 0.55,
        enabled: true,
        detectionCount: 13100,
        lastDetected: '2026-09-04T10:21:55Z',
        description: 'High-visibility safety vest',
      },
      {
        id: 3,
        label: 'no_hard_hat',
        category: 'Hazard',
        color: '#ef4444',
        confidenceThreshold: 0.65,
        enabled: true,
        detectionCount: 482,
        lastDetected: '2026-09-04T09:14:12Z',
        description: 'Worker detected without hard hat — safety violation',
      },
      {
        id: 4,
        label: 'no_safety_vest',
        category: 'Hazard',
        color: '#f97316',
        confidenceThreshold: 0.65,
        enabled: true,
        detectionCount: 315,
        lastDetected: '2026-09-04T08:57:30Z',
        description: 'Worker detected without safety vest — safety violation',
      },
      {
        id: 5,
        label: 'safety_gloves',
        category: 'PPE',
        color: '#06b6d4',
        confidenceThreshold: 0.5,
        enabled: false,
        detectionCount: 0,
        lastDetected: null,
        description: 'Protective gloves (disabled — experimental)',
      },
      {
        id: 6,
        label: 'safety_goggles',
        category: 'PPE',
        color: '#8b5cf6',
        confidenceThreshold: 0.5,
        enabled: false,
        detectionCount: 0,
        lastDetected: null,
        description: 'Safety goggles / eye protection (disabled)',
      },
    ],
  },
  {
    id: 'CP-002',
    name: 'Perimeter & Vehicle Monitoring',
    modelId: 'MOD-002',
    modelName: 'RT-DETR-Large v1.4.0',
    createdAt: '2026-08-15',
    updatedAt: '2026-09-01',
    classes: [
      {
        id: 0,
        label: 'person',
        category: 'Person',
        color: '#3b82f6',
        confidenceThreshold: 0.55,
        enabled: true,
        detectionCount: 9210,
        lastDetected: '2026-09-04T10:18:00Z',
        description: 'Unauthorized person in restricted zone',
      },
      {
        id: 1,
        label: 'vehicle',
        category: 'Vehicle',
        color: '#f59e0b',
        confidenceThreshold: 0.6,
        enabled: true,
        detectionCount: 4350,
        lastDetected: '2026-09-04T10:15:20Z',
        description: 'General vehicle class',
      },
      {
        id: 2,
        label: 'heavy_machinery',
        category: 'Vehicle',
        color: '#ef4444',
        confidenceThreshold: 0.7,
        enabled: true,
        detectionCount: 1820,
        lastDetected: '2026-09-04T09:40:00Z',
        description: 'Excavators, forklifts, cranes',
      },
      {
        id: 3,
        label: 'truck',
        category: 'Vehicle',
        color: '#84cc16',
        confidenceThreshold: 0.6,
        enabled: true,
        detectionCount: 2100,
        lastDetected: '2026-09-04T10:10:00Z',
        description: 'Delivery or cargo trucks',
      },
    ],
  },
]
