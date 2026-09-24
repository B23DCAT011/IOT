import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Cổng 5173 là cổng backend đã khai sẵn trong CORS_ALLOWED_ORIGINS (05-API.md §2.9).
// strictPort: cổng bận thì báo lỗi, không tự nhảy sang 5174 rồi bị CORS chặn.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
})
