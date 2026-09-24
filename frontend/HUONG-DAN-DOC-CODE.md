# Hướng dẫn đọc code Frontend

> Cách chạy và danh sách quy tắc nghiệp vụ đã cài: `README.md`. File này chỉ trả lời hai câu:
> **file này để làm gì** và **component này được dùng ở đâu**.

## 1. Nên đọc theo thứ tự nào

| Bước | Đọc | Để hiểu |
|---|---|---|
| 1 | `src/main.jsx` → `src/App.jsx` | Ứng dụng khởi động ra sao, có những trang nào |
| 2 | `src/config.js`, `src/constants.js` | Các con số và hằng dùng khắp nơi |
| 3 | `src/api/client.js` → `src/api/endpoints.js` | Mọi lời gọi tới backend đi qua đâu |
| 4 | `src/auth/AuthContext.jsx`, `src/realtime/RealtimeContext.jsx` | Hai thứ **dùng chung toàn app**: đăng nhập và WebSocket |
| 5 | `src/components/Layout.jsx` | Khung sidebar + tiêu đề bọc quanh mọi trang |
| 6 | `src/pages/*` | Từng màn hình — đọc trang nào cần sửa |

`src/mocks/` **không cần đọc**: chỉ chạy khi bật dữ liệu giả (`VITE_USE_MOCK=true`).

## 2. Ứng dụng khởi động như thế nào

```
index.html
└── src/main.jsx                       (nếu VITE_USE_MOCK=true thì bật dữ liệu giả MSW trước)
    └── <BrowserRouter>                thư viện react-router: đổi trang không tải lại trình duyệt
        └── <AuthProvider>             auth/AuthContext.jsx — giữ token, biết ai đang đăng nhập
            └── <App>                  App.jsx — bảng định tuyến
                ├── /login             → pages/LoginPage.jsx          (không cần đăng nhập)
                └── <ProtectedArea>    chưa đăng nhập → đẩy về /login
                    └── <RealtimeProvider>   realtime/RealtimeContext.jsx — MỘT WebSocket cho cả app
                        ├── /                → pages/DashboardPage.jsx
                        ├── /data-sensor     → pages/DataSensorPage.jsx
                        ├── /action-history  → pages/ActionHistoryPage.jsx
                        └── /profile         → pages/ProfilePage.jsx
```

**Vì sao `RealtimeProvider` nằm trong `ProtectedArea`:** WebSocket cần token. Đặt ở đây thì chỉ mở
kết nối **sau khi** đăng nhập, và chuyển giữa 4 trang **không** mở lại kết nối mới.

## 3. Từng thư mục, từng file

### `src/` — gốc

| File | Làm gì |
|---|---|
| `main.jsx` | Điểm vào. Bật MSW nếu cần, rồi gắn `<App>` vào trang |
| `App.jsx` | Bảng định tuyến: đường dẫn nào → trang nào; bọc 4 trang chính trong `ProtectedArea` |
| `config.js` | Đọc biến môi trường (`VITE_API_BASE_URL`, `VITE_WS_URL`, `VITE_USE_MOCK`) và các con số nghiệp vụ: 20 điểm biểu đồ (BR-10), 10 dòng/trang (BR-08), **30 giây ngoại tuyến (BR-07)**, thử kết nối lại WebSocket sau 5 giây, bộ đếm dự phòng 7 giây |
| `constants.js` | Khóa `temperature/humidity/light`, màu 3 đường biểu đồ, nhãn tiếng Việt của vai trò, danh sách trạng thái/hành động cho dropdown |

### `src/api/` — nói chuyện với backend qua HTTP

| File | Làm gì |
|---|---|
| `client.js` | Tạo **một** đối tượng Axios dùng chung. Tự gắn header `Authorization: Token …` vào mọi request. Biến mọi lỗi của backend thành một `ApiError` có `status`, `code`, `message`, `details`. Gặp `401` thì gọi hàm "hết phiên" để đưa về trang đăng nhập |
| `endpoints.js` | Danh sách **mọi** lời gọi API, nhóm theo tài nguyên: `authApi`, `sensorApi`, `deviceApi`, `actionApi`, `profileApi`. Muốn biết trang nào gọi endpoint nào thì tìm tên hàm ở đây |

> Không trang nào gọi `axios`/`fetch` trực tiếp — tất cả đi qua `endpoints.js`. Đổi đường dẫn API chỉ sửa đúng một chỗ.

### `src/auth/` — đăng nhập

| File | Làm gì | Dùng ở đâu |
|---|---|---|
| `AuthContext.jsx` → `AuthProvider` | Giữ `{ token, user }`, lưu vào `localStorage` để tải lại trang vẫn còn đăng nhập. Cung cấp `login()`, `logout()`, `expireSession()`. Đồng bộ giữa các tab: tab này đăng xuất thì tab kia cũng đăng xuất | `main.jsx` (bọc cả app) |
| → `useAuth()` | Hook để component lấy thông tin đăng nhập | `LoginPage`, `Layout` (tên + nút đăng xuất), `ActionHistoryPage` (lọc "Của tôi"), `RealtimeContext` (lấy token) |
| → `RequireAuth` | Chưa đăng nhập thì chuyển về `/login`, **nhớ trang đang xem** để đăng nhập xong quay lại đúng chỗ | `App.jsx` |

### `src/realtime/` — WebSocket

| File | Làm gì | Dùng ở đâu |
|---|---|---|
| `RealtimeContext.jsx` → `RealtimeProvider` | Mở **một** kết nối `ws://…/ws/realtime/?token=…`. Mất kết nối thì thử lại sau 5 giây; bị đóng mã `4401` (token sai) thì **không** thử lại mà về trang đăng nhập | `App.jsx` |
| → `useRealtime()` | Lấy trạng thái kết nối (`connecting`/`open`/`closed`) | `DashboardPage` (dòng chữ góc trên + dải "Mất kết nối máy chủ") |
| → `useRealtimeEvent(fn)` | Đăng ký nhận sự kiện `sensor.data` / `device.state` | `DashboardPage` (số liệu mới), `DevicePanel` (kết quả bấm công tắc), `ActionHistoryPage` (dòng PENDING kết thúc) |

### `src/pages/` — 5 màn hình

| Trang | Làm gì | Gọi API | Nghe WebSocket |
|---|---|---|---|
| `LoginPage.jsx` | Form đăng nhập, hiện lỗi sai mật khẩu | `authApi.login` (qua `useAuth`) | — |
| `DashboardPage.jsx` | 3 thẻ số liệu + biểu đồ 20 chu kỳ + bảng điều khiển thiết bị. Đếm 30 giây không có số liệu → "Thiết bị ngoại tuyến" | `sensorApi.catalog/latest/chart`, `deviceApi.list` — gọi song song 4 cái khi mở trang | `sensor.data` → cập nhật thẻ và biểu đồ |
| `DataSensorPage.jsx` | Bảng số đo: tìm kiếm, lọc cảm biến + khoảng giá trị + khoảng ngày, sắp xếp, phân trang | `sensorApi.catalog` (dropdown), `sensorApi.list` | — |
| `ActionHistoryPage.jsx` | Bảng lịch sử bật/tắt: lọc thiết bị, trạng thái, hành động, người thao tác, ngày | `deviceApi.list` (dropdown), `actionApi.list` | `device.state` → chỉ tải lại khi một dòng PENDING **đang hiện** vừa kết thúc |
| `ProfilePage.jsx` | Thông tin sinh viên, đề tài, 4 liên kết bàn giao; liên kết chưa có thì nút mờ "Đang cập nhật" | `profileApi.get` | — |

Mỗi trang có file `.module.css` riêng nếu cần kiểu riêng (`Login.module.css`, `Profile.module.css`);
Dashboard dùng `components/dashboard/Dashboard.module.css`.

### `src/components/` — mảnh giao diện dùng lại

| Component | Làm gì | Dùng ở đâu |
|---|---|---|
| `Layout.jsx` | Khung chung: sidebar 4 mục + tên người dùng + nút đăng xuất, thanh tiêu đề (`title`, phần bên phải `right`) | **Cả 4 trang chính** (không dùng ở Login) |
| `Banner.jsx` | Dải thông báo lỗi màu đỏ, có nhãn nhỏ (`HTTP 503`, `Mạng`…) và nút hành động | Cả 4 trang chính (lỗi tải dữ liệu); Dashboard thêm dải "Mất kết nối máy chủ" và thông báo timeout |
| `Filters.jsx` → `Field` | Nhãn nhỏ phía trên một ô lọc | `DataSensorPage`, `ActionHistoryPage` |
| → `SearchInput` | Ô tìm kiếm có biểu tượng kính lúp | `DataSensorPage`, `ActionHistoryPage` |
| → `EmptyState` | Bảng rỗng: "Không có dữ liệu", hoặc khi đang lọc thì "Không tìm thấy bản ghi nào khớp bộ lọc" + nút "Xóa bộ lọc" | `DataSensorPage`, `ActionHistoryPage` |
| `SortHeader.jsx` | Tiêu đề cột bấm được để sắp xếp tăng/giảm, có mũi tên | `DataSensorPage`, `ActionHistoryPage` |
| `Pagination.jsx` | Thanh chuyển trang `‹ 1 2 3 … 12 ›` | `DataSensorPage`, `ActionHistoryPage` |
| `Icons.jsx` | Toàn bộ biểu tượng SVG: `NavIcon` (sidebar), `DeviceIcon` (bóng đèn/quạt), `LinkIcon` (Profile), `SearchIcon`, `InfoIcon`, `LogoutIcon`, 3 icon sắp xếp | `Layout`, `DevicePanel`, `ProfilePage`, `Filters`, `SortHeader`, 2 trang bảng |
| `dashboard/StatCard.jsx` | Một thẻ số liệu: tên, giá trị lớn, đơn vị, biến thiên 20 giây, đường mini (sparkline) | Chỉ `DashboardPage` (3 thẻ) |
| `dashboard/SensorChart.jsx` | Biểu đồ đường Recharts: 2 trục (°C/% bên trái, lux bên phải), điểm `null` → đường đứt | Chỉ `DashboardPage` |
| `dashboard/DevicePanel.jsx` | Danh sách công tắc. Bấm → gọi API → khoá "ĐANG GỬI…" → chờ `device.state` → mở khoá. Có bộ đếm dự phòng 7 giây nếu sự kiện không tới | Chỉ `DashboardPage` |

### `src/hooks/`, `src/utils/` — hàm tiện ích

| File | Làm gì | Dùng ở đâu |
|---|---|---|
| `hooks/useDebouncedValue.js` | Chờ người dùng ngừng gõ 400 ms mới đổi giá trị → không gọi API theo từng phím | Ô tìm kiếm và 2 ô giá trị ở `DataSensorPage`; ô tìm kiếm ở `ActionHistoryPage` |
| `utils/format.js` | Đổi giờ UTC của API sang **giờ Việt Nam**; định dạng số (`28.5`, lux làm tròn), số đếm (`36.134`); `dayStartVN`/`dayEndVN` tạo mốc lọc ngày kèm `+07:00` | Mọi trang có hiện giờ hoặc số |
| `utils/errors.js` | `errorChip(err)` → nhãn nhỏ `HTTP 503` hoặc `Mạng` trên dải lỗi | Các trang và `DevicePanel` |
| `utils/storage.js` | Đọc/ghi `localStorage` có bọc `try/catch` (trình duyệt chặn thì app vẫn chạy) | `AuthContext` |

### `src/styles/` — giao diện chung

| File | Làm gì |
|---|---|
| `global.css` | **Bảng màu** (biến CSS `--…`), font, nền — chép từ bản vẽ `docs/wireframe/`. Muốn đổi màu cả app thì sửa ở đây |
| `ui.module.css` | Kiểu dùng chung: thẻ (`card`), nút (`btn`), ô nhập, bảng, nhãn trạng thái SUCCESS/FAILED/PENDING, thanh phân trang |

**CSS Modules là gì:** `import ui from '../styles/ui.module.css'` rồi viết `className={ui.btn}`. Vite đổi tên lớp
thành dạng `_btn_x7k2a` để hai file CSS khác nhau không đè kiểu lên nhau. Khi soi bằng F12 sẽ thấy tên lớp bị đổi — bình thường.

### `src/mocks/` và `public/mockServiceWorker.js` — dữ liệu giả

Chỉ chạy khi `VITE_USE_MOCK=true`. Giả lập đủ 10 endpoint + WebSocket của backend để làm giao diện khi chưa có Django.
`db.js` chứa bộ dữ liệu mẫu, `handlers.js` trả lời từng request. Hiện đang **tắt** — frontend gọi backend thật.

## 4. Ba luồng chạy nên hiểu

### ① Đăng nhập
```
LoginPage  --useAuth().login()-->  AuthContext  --authApi.login-->  POST /api/auth/login
   token + user lưu vào localStorage và vào client.js (gắn vào mọi request sau)
   → RequireAuth cho qua → RealtimeProvider mở WebSocket → quay về trang đang xem trước đó
Bất kỳ request nào nhận 401 → client.js gọi expireSession() → xoá token → về /login
```

### ② Mở Dashboard và nhận số liệu trực tiếp
```
DashboardPage mở → gọi song song 4 API (danh mục cảm biến, số đo mới nhất, biểu đồ, thiết bị)
   → dựng 3 StatCard từ DANH MỤC, điền giá trị từ số đo mới nhất
Mỗi 2 giây: backend đẩy sensor.data → useRealtimeEvent trong DashboardPage
   → cập nhật thẻ, thêm 1 điểm vào biểu đồ (giữ 20 điểm), đặt lại bộ đếm 30 giây ngoại tuyến
```

### ③ Bấm công tắc
```
DevicePanel.toggle() → khoá công tắc "ĐANG GỬI…" → deviceApi.control → POST …/control → 202 + request_id
   backend gửi MQTT → mạch bật đèn → mạch trả lời → backend đẩy device.state qua WebSocket
DevicePanel nhận device.state có request_id khớp → mở khoá, hiện trạng thái mới
   FAILED (mạch không trả lời 5–6 giây) → trả công tắc về cũ + dải thông báo timeout
   7 giây không có gì (WebSocket đứt) → tự mở khoá và gọi lại deviceApi.list
Sự kiện device.state KHÔNG kèm request_id (mạch vừa cắm lại tự báo trạng thái) → chỉ cập nhật công tắc
```

## 5. Muốn sửa X thì mở file nào

| Muốn… | Mở |
|---|---|
| Đổi địa chỉ backend (demo trong LAN) | `.env` — `VITE_API_BASE_URL`, `VITE_WS_URL` |
| Bật/tắt dữ liệu giả | `.env.development` — `VITE_USE_MOCK` |
| Đổi 30 giây ngoại tuyến, 20 điểm biểu đồ, 10 dòng/trang | `src/config.js` |
| Đổi màu 3 đường biểu đồ | `src/constants.js` — `METRIC_COLOR` |
| Đổi màu/kiểu cả app | `src/styles/global.css` |
| Thêm một mục vào sidebar | `src/components/Layout.jsx` (mảng `NAV` ở đầu file) + thêm route ở `src/App.jsx` |
| Thêm một endpoint mới | `src/api/endpoints.js` |
| Đổi cột bảng Data Sensor / Action History | `src/pages/DataSensorPage.jsx` / `ActionHistoryPage.jsx` (phần `<thead>` và `<tbody>`) |
| Đổi cách hiện ngày giờ | `src/utils/format.js` |
| Đổi hành vi công tắc (khoá, timeout) | `src/components/dashboard/DevicePanel.jsx` |
| Đổi thông báo lỗi | Câu lỗi phần lớn do **backend** trả về (`backend/config/exceptions.py`); frontend chỉ hiển thị |
