import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/pages\Layout'
import Overview from '@/pages\Overview'
import ChatPage from '@/pages\ChatPage'

// FLEET
import DevicesPage from '@/pages\fleet\DevicesPage'
import CamerasPage from '@/pages\fleet\CamerasPage'
import SnapshotsPage from '@/pages\fleet\SnapshotsPage'
import CameraGroupsPage from '@/pages\fleet\CameraGroupsPage'

// AI
import ModelsPage from '@/pages\ai\ModelsPage'
import DeploymentsPage from '@/pages\ai\DeploymentsPage'
import InferencePage from '@/pages\ai\InferencePage'

// OBSERVABILITY
import MonitoringPage from '@/pages\observability\MonitoringPage'
import AlertsPage from '@/pages\observability\AlertsPage'
import EventsPage from '@/pages\observability\EventsPage'
import LogsPage from '@/pages\observability\LogsPage'

// SYSTEM
import UsersPage from '@/pages\system\UsersPage'
import SettingsPage from '@/pages\system\SettingsPage'
import AuditLogsPage from '@/pages\system\AuditLogsPage'

import '@/app\styles\theme.css'
import '@/app\styles\layout-extras.css'

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="chat" element={<ChatPage />} />

          {/* FLEET */}
          <Route path="fleet">
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
          <Route path="cameras" element={<Navigate to="/fleet/cameras" replace />} />
          <Route path="incidents" element={<Navigate to="/observability/alerts" replace />} />
          <Route path="analytics" element={<Navigate to="/observability/monitoring" replace />} />
          <Route path="edge-devices" element={<Navigate to="/fleet/devices" replace />} />
          <Route path="settings" element={<Navigate to="/system/settings" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}

export default App


