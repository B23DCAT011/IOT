import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './auth/AuthContext'
import ActionHistoryPage from './pages/ActionHistoryPage'
import DashboardPage from './pages/DashboardPage'
import DataSensorPage from './pages/DataSensorPage'
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'
import { RealtimeProvider } from './realtime/RealtimeContext'

function ProtectedArea() {
  return (
    <RequireAuth>
      <RealtimeProvider>
        <Outlet />
      </RealtimeProvider>
    </RequireAuth>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedArea />}>
        <Route index element={<DashboardPage />} />
        <Route path="data-sensor" element={<DataSensorPage />} />
        <Route path="action-history" element={<ActionHistoryPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
