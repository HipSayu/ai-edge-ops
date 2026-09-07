import { apiClient } from '../client'
import type { AuditLog } from '../types/system'

export const systemService = {
  listAuditLogs: () => apiClient.get<AuditLog[]>('/system/audit-logs'),
  getSettings: () => apiClient.get<Record<string, unknown>>('/system/settings'),
  updateSettings: (payload: Record<string, unknown>) => apiClient.patch<Record<string, unknown>>('/system/settings', payload),
}
