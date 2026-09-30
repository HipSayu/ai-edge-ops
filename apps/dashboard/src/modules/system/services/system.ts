import { apiClient } from '@/shared/api/client'
import type { AuditLog } from '@/modules/system/types/system'

export const systemService = {
  listAuditLogs: () => apiClient.get<AuditLog[]>('/system/audit-logs'),
  getSettings: () => apiClient.get<Record<string, unknown>>('/system/settings'),
  updateSettings: (payload: Record<string, unknown>) => apiClient.patch<Record<string, unknown>>('/system/settings', payload),
}
