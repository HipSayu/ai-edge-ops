import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/app/pages/Layout'
import Overview from '@/modules/overview/pages/Overview'
import ChatPage from '@/modules/assistant/pages/ChatPage'

// AGENT
import DevicesPage from '@/modules/agent/pages/DevicesPage'
import CamerasPage from '@/modules/agent/pages/CamerasPage'
import SnapshotsPage from '@/modules/agent/pages/SnapshotsPage'
import CameraGroupsPage from '@/modules/agent/pages/CameraGroupsPage'

// AI
import ModelsPage from '@/modules/ai/pages/ModelsPage'
import DeploymentsPage from '@/modules/ai/pages/DeploymentsPage'
import InferencePage from '@/modules/ai/pages/InferencePage'
import ClassConfigPage from '@/modules/ai/pages/ClassConfigPage'

// OBSERVABILITY
import MonitoringPage from '@/modules/observability/pages/MonitoringPage'
import AlertsPage from '@/modules/observability/pages/AlertsPage'
import EventsPage from '@/modules/observability/pages/EventsPage'
import LogsPage from '@/modules/observability/pages/LogsPage'

// SYSTEM
import UsersPage from '@/modules/system/pages/UsersPage'
import SettingsPage from '@/modules/system/pages/SettingsPage'
import AuditLogsPage from '@/modules/system/pages/AuditLogsPage'

import '@/app/styles/theme.css'
import '@/app/styles/layout-extras.css'
import { RealtimeProvider } from '@/shared/contexts/RealtimeContext'

function App() {
  return (
    <RealtimeProvider>
      <HashRouter>
        <Routes>
        <Route element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="chat" element={<ChatPage />} />

          {/* AGENT */}
          <Route path="agent">
            <Route path="devices" element={<DevicesPage />} />
            <Route path="cameras" element={<CamerasPage />} />
            <Route path="snapshots" element={<SnapshotsPage />} />
            <Route path="camera-groups" element={<CameraGroupsPage />} />
          </Route>

          {/* AI */}
          <Route path="ai">
            <Route path="models" element={<ModelsPage />} />
            <Route path="deployments" element={<DeploymentsPage />} />
            <Route path="inference" element={<InferencePage />} />
            <Route path="class-config" element={<ClassConfigPage />} />
          </Route>

          {/* OBSERVABILITY */}
          <Route path="observability">
            <Route path="monitoring" element={<MonitoringPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="events" element={<EventsPage />} />
            <Route path="logs" element={<LogsPage />} />
          </Route>

          {/* SYSTEM */}
          <Route path="system">
            <Route path="users" element={<UsersPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="audit-logs" element={<AuditLogsPage />} />
          </Route>

          {/* Legacy route redirects */}
          <Route path="live" element={<Navigate to="/ai/inference" replace />} />
          <Route path="cameras" element={<Navigate to="/agent/cameras" replace />} />
          <Route path="incidents" element={<Navigate to="/observability/alerts" replace />} />
          <Route path="analytics" element={<Navigate to="/observability/monitoring" replace />} />
          <Route path="edge-devices" element={<Navigate to="/agent/devices" replace />} />
          <Route path="settings" element={<Navigate to="/system/settings" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
        </Routes>
      </HashRouter>
    </RealtimeProvider>
  )
}

export default App


