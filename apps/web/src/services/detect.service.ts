import { api } from '@/api/client'
import type { DetectionResult } from '@/api/types'

export const detectService = {
  run: (image: Blob) => api.postBinary<DetectionResult>('/detect', image),
}
