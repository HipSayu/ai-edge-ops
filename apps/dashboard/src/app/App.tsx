import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/app/pages/Layout'
import LoginPage from '@/app/pages/LoginPage'
import RequireAuth from '@/app/components/RequireAuth'
import Overview from '@/modules/overview/pages/Overview'
import ChatPage from '@/modules/assistant/pages/ChatPage'

// AGENT
import DevicesPage from '@/modules/agent/pages/DevicesPage'
import CamerasPage from '@/modules/agent/pages/CamerasPage'
import SnapshotsPage from '@/modules/agent/pages/SnapshotsPage'
import CameraGroupsPage from '@/modules/agent/pages/CameraGroupsPage'
import ClustersPage from '@/modules/cluster/pages/ClustersPage'
import ClusterDetailPage from '@/modules/cluster/pages/ClusterDetailPage'
import NodeLogsPage from '@/modules/agent/pages/NodeLogsPage'
import NodeDetailPage from '@/modules/agent/pages/NodeDetailPage'

// MODEL (formerly AI)
import ModelsPage from '@/modules/ai/pages/ModelsPage'
import ClassConfigPage from '@/modules/ai/pages/ClassConfigPage'

import '@/app/styles/index.css'
import { RealtimeProvider } from '@/core/realtime/RealtimeContext'
import { EdgeOpsProvider } from '@/core/edge-ops/EdgeOpsContext'

// Data providers mount only once signed in, so they load with a valid token (and reload after re-login).
const protectedShell = (
  <RequireAuth>
    <RealtimeProvider>
      <EdgeOpsProvider>
        <Layout />
      </EdgeOpsProvider>
    </RealtimeProvider>
  </RequireAuth>
)

function App() {
  return (
        <HashRouter>
          <Routes>
            <Route path="login" element={<LoginPage />} />
            <Route element={protectedShell}>
              <Route index element={<Overview />} />
              <Route path="chat" element={<ChatPage />} />
              <Route path="chat/:conversationId" element={<ChatPage />} />

              {/* AGENT */}
              <Route path="agent">
                <Route path="clusters" element={<ClustersPage />} />
                <Route path="clusters/:id" element={<ClusterDetailPage />} />
                <Route path="nodes" element={<DevicesPage />} />
                <Route path="nodes/:id" element={<NodeDetailPage />} />
                <Route path="devices" element={<Navigate to="/agent/nodes" replace />} />
                <Route path="devices/:id" element={<NodeDetailPage />} />
                <Route path="cameras" element={<CamerasPage />} />
                <Route path="logs" element={<NodeLogsPage />} />
                <Route path="snapshots" element={<SnapshotsPage />} />
                <Route path="camera-groups" element={<CameraGroupsPage />} />
              </Route>

              {/* MODEL */}
              <Route path="models">
                <Route index element={<Navigate to="/models/registry" replace />} />
                <Route path="registry" element={<ModelsPage />} />
                <Route path="deployments" element={<Navigate to="/models/registry" replace />} />
                <Route path="class-config" element={<ClassConfigPage />} />
              </Route>

              {/* Backward compatibility for /ai/* routes */}
              <Route path="ai">
                <Route path="models" element={<Navigate to="/models/registry" replace />} />
                <Route path="deployments" element={<Navigate to="/models/registry" replace />} />
                <Route path="inference" element={<Navigate to="/agent/cameras" replace />} />
                <Route path="class-config" element={<Navigate to="/models/class-config" replace />} />
                <Route path="*" element={<Navigate to="/models/registry" replace />} />
              </Route>

              {/* Legacy route redirects */}
              <Route path="live" element={<Navigate to="/agent/cameras" replace />} />
              <Route path="cameras" element={<Navigate to="/agent/cameras" replace />} />
              <Route path="incidents" element={<Navigate to="/agent/cameras" replace />} />
              <Route path="analytics" element={<Navigate to="/agent/cameras" replace />} />
              <Route path="edge-devices" element={<Navigate to="/agent/nodes" replace />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </HashRouter>
  )
}

export default App
