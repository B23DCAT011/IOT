import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './auth/AuthContext'
import { USE_MOCK } from './config'
import './styles/global.css'

// MSW phải chạy xong TRƯỚC khi ứng dụng mở WebSocket hay gọi API đầu tiên,
// nếu không request đầu đi thẳng ra localhost:8000 (chưa có backend) và lỗi.
async function enableMocking() {
  if (!USE_MOCK) return
  const { startMockWorker } = await import('./mocks/browser')
  await startMockWorker()
}

enableMocking().then(() => {
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </StrictMode>,
  )
})
