// localStorage có thể bị trình duyệt chặn (cửa sổ ẩn danh, chính sách công ty):
// mọi lần đọc/ghi đều bọc try/catch để trang vẫn chạy, chỉ là không nhớ được đăng nhập.
export const storage = {
  get(key) {
    try {
      const raw = window.localStorage.getItem(key)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  },
  set(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value))
    } catch {
      /* không lưu được: phiên chỉ sống tới khi tải lại trang */
    }
  },
  remove(key) {
    try {
      window.localStorage.removeItem(key)
    } catch {
      /* bỏ qua */
    }
  },
}
