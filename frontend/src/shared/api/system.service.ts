import type { AuditLog } from '@/modules/system/mock/system'
import { apiClient } from './client'

export const systemService = {
  listAuditLogs: () => apiClient.get<AuditLog[]>('/system/audit-logs'),
  getSettings: () => apiClient.get<Record<string, unknown>>('/system/settings'),
  updateSettings: (payload: Record<string, unknown>) =>
    apiClient.patch<Record<string, unknown>>('/system/settings', payload),
}
