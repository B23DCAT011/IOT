# Frontend — Room01 Monitor

React + Vite + React Router + Recharts + Axios. Giao diện dựng theo `docs/wireframe/*.html`,
gọi API theo đúng hợp đồng `docs/05-API.md` **v2.1** (có đăng nhập bằng token).

> 📖 **Mới đọc code?** Xem `HUONG-DAN-DOC-CODE.md` — file nào làm gì, component nào dùng ở đâu.

## Chạy

```powershell
cd frontend
npm install        # lần đầu
npm run dev        # http://localhost:5173
```

Mặc định `npm run dev` gọi **backend Django thật** (`.env.development` đặt `VITE_USE_MOCK=false`) —
bật daphne + `mqtt_worker` trước, xem `backend/README.md`. Muốn làm giao diện khi không bật backend thì
đặt `VITE_USE_MOCK=true`: **MSW** giả lập toàn bộ API và WebSocket bằng bộ dữ liệu mẫu bên dưới.

| Tài khoản | Mật khẩu | Vai trò |
|---|---|---|
| `admin` | `doi-mat-khau-nay` | Lưu Đức Anh — `ADMIN` |
| `operator` | `doi-mat-khau-nay` | Người vận hành — `OPERATOR` |

Dữ liệu giả là **bộ dữ liệu mẫu chuẩn** (`CLAUDE.md` §0.2f): 36.134 bản ghi cảm biến, 88 thao tác,
Dashboard mở ra ở mốc 17:30:02 với đèn OFF, quạt ON. Số đo mới được đẩy qua WebSocket mỗi 2 giây.

### Giả lập tình huống lỗi

Gõ trong Console của trình duyệt (F12):

```js
localStorage.setItem('room01.mock.deviceOffline', '1') // bấm công tắc → FAILED sau 5–6 giây
localStorage.setItem('room01.mock.brokerDown', '1')    // bấm công tắc → 503 BROKER_UNAVAILABLE
localStorage.setItem('room01.mock.sensorOffline', '1') // 30 giây sau Dashboard báo "Thiết bị ngoại tuyến"
localStorage.removeItem('room01.mock.brokerDown')      // tắt lại
```

Lệnh `id 88` trong dữ liệu mẫu đang `PENDING`, nên **5–6 giây đầu sau khi tải trang**, bấm công tắc
**đèn** sẽ nhận `409 DEVICE_BUSY` — đúng quy tắc BR-04, không phải lỗi.

## Nối với backend thật

1. Đổi `VITE_USE_MOCK=false` trong `.env.development` (hoặc xoá dòng đó).
2. Kiểm tra `VITE_API_BASE_URL`, `VITE_WS_URL` trong `.env`. Demo trong LAN thì thay `localhost` bằng IP laptop
   và thêm `http://<IP>:5173` vào `CORS_ALLOWED_ORIGINS` của Django (`05-API.md` §2.9).

Không phải sửa dòng code gọi API nào.

## Cấu trúc

```
src/
├── api/            client.js (Axios, token, lỗi thống nhất) · endpoints.js
├── auth/           AuthContext.jsx — đăng nhập, đăng xuất, chặn trang khi chưa đăng nhập
├── realtime/       RealtimeContext.jsx — một kết nối WebSocket, tự kết nối lại mỗi 5 giây
├── components/     Layout, Pagination, SortHeader, Banner, Filters, Icons, dashboard/*
├── pages/          Login · Dashboard · DataSensor · ActionHistory · Profile
├── mocks/          db.js (dữ liệu mẫu) · handlers.js (REST + WebSocket) · browser.js
└── styles/         global.css (bảng màu) · ui.module.css (thành phần dùng chung)
```

## Quy tắc đã cài đặt

| Quy tắc | Ở đâu |
|---|---|
| BR-04 — khóa công tắc khi lệnh còn chờ; xử lý `409` | `components/dashboard/DevicePanel.jsx` |
| Bộ đếm dự phòng 7 giây mở khóa công tắc | `DevicePanel.jsx` |
| BR-07 — 30 giây không có `sensor.data` → "Thiết bị ngoại tuyến" | `pages/DashboardPage.jsx` |
| BR-10 — biểu đồ 20 chu kỳ, chu kỳ thiếu số đo làm đường đứt nét | `DashboardPage.jsx`, `SensorChart.jsx` |
| `401` → về trang đăng nhập rồi quay lại đúng trang đang xem | `api/client.js`, `auth/AuthContext.jsx` |
| WebSocket đóng mã `4401` → không kết nối lại, về trang đăng nhập | `realtime/RealtimeContext.jsx` |
| Bộ lọc ngày gửi kèm `+07:00`; hiển thị giờ Việt Nam | `utils/format.js` |
| Hai ô giá trị chỉ mở khi đã chọn cảm biến (UC-04 E4) | `pages/DataSensorPage.jsx` |
| `404 PAGE_NOT_FOUND` coi là rỗng, quay về trang 1 | `DataSensorPage.jsx`, `ActionHistoryPage.jsx` |
| Người thao tác `null` hiển thị `—` (BR-12) | `pages/ActionHistoryPage.jsx` |
| Màn lịch sử không tự chèn dòng; chỉ làm mới khi dòng `PENDING` đang hiện kết thúc | `ActionHistoryPage.jsx` |
