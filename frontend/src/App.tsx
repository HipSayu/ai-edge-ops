import { HashRouter, Routes, Route } from 'react-router-dom'
import Layout from './pages/Layout'
import Overview from './pages/Overview'
import LiveMonitor from './pages/LiveMonitor'
import Cameras from './pages/Cameras'
import IncidentsPage from './pages/IncidentsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import AiAssistantPage from './pages/AiAssistantPage'
import EdgeDevicesPage from './pages/EdgeDevicesPage'
import Settings from './pages/Settings'
import './theme.css'
import './layout-extras.css'

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="live" element={<LiveMonitor />} />
          <Route path="cameras" element={<Cameras />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="assistant" element={<AiAssistantPage />} />
          <Route path="edge-devices" element={<EdgeDevicesPage />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}

export default App
