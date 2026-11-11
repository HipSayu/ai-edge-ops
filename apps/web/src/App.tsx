import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import CamerasTab from '@/components/admin/CamerasTab'
import ClustersTab from '@/components/admin/ClustersTab'
import NodesTab from '@/components/admin/NodesTab'
import UsersTab from '@/components/admin/UsersTab'
import RequireAuth from '@/components/common/RequireAuth'
import { AuthProvider } from '@/contexts/AuthContext'
import { FilterProvider } from '@/contexts/FilterContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import AdminPage from '@/pages/AdminPage'
import DetectPage from '@/pages/DetectPage'
import LoginPage from '@/pages/LoginPage'
import MonitorPage from '@/pages/MonitorPage'
import TopologyPage from '@/pages/TopologyPage'

export default function App() {
  return (
    <ThemeProvider>
    <AuthProvider>
    <FilterProvider>
      <BrowserRouter>
        <Routes>
          <Route path="login" element={<LoginPage />} />
          <Route path="/" element={<RequireAuth><MonitorPage /></RequireAuth>} />

          <Route path="topology" element={<RequireAuth><TopologyPage /></RequireAuth>} />

          <Route path="detect" element={<RequireAuth><DetectPage /></RequireAuth>} />

          {/* Admin Nested Routes: Clusters -> Nodes -> Cameras Hierarchy */}
          <Route
            path="admin"
            element={
              <RequireAuth operatorOnly>
                <AdminPage />
              </RequireAuth>
            }
          >
            <Route index element={<Navigate to="clusters" replace />} />
            <Route path="clusters" element={<ClustersTab />} />
            <Route path="nodes" element={<NodesTab />} />
            <Route path="cameras" element={<CamerasTab canManage={true} />} />
            <Route path="users" element={<UsersTab />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </FilterProvider>
    </AuthProvider>
    </ThemeProvider>
  )
}
