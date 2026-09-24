// Nhãn nhỏ trên dải thông báo lỗi: mã HTTP nếu máy chủ có trả lời, "Mạng" nếu không tới được máy chủ.
// Để riêng ở đây vì file component chỉ nên export component (Vite Fast Refresh).
export const errorChip = (err) => (err?.status ? `HTTP ${err.status}` : 'Mạng')
