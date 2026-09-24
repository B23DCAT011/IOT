import { setupWorker } from 'msw/browser'
import { handlers, startMockLoops } from './handlers'

export async function startMockWorker() {
  const worker = setupWorker(...handlers)
  // bypass: request không có trong danh sách giả lập (ảnh, font, mã nguồn Vite) đi thẳng ra ngoài.
  await worker.start({ onUnhandledRequest: 'bypass' })
  startMockLoops()
}
