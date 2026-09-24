# Backend — Django + DRF + Channels

Cài đặt đúng theo `docs/04-Database.md` v2.0 và `docs/05-API.md` v2.1. Kế hoạch từng module và
những chỗ cố ý lệch khỏi mã mẫu trong tài liệu: **`PLAN.md`**.

## 1. Cài lần đầu

Cần sẵn: Python 3.14, PostgreSQL (đã có DB `iot_room`), Redis, Mosquitto ở cổng 1884.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env          # rồi điền DB_PASSWORD, MQTT_PASSWORD, SECRET_KEY
.\.venv\Scripts\python manage.py migrate     # tạo 5 bảng + seed 2 tài khoản, 3 cảm biến, 2 thiết bị
```

Redis trên máy này là container `redis-dev` có sẵn (tự bật cùng Docker Desktop). Backend dùng
**database số 5** (`REDIS_URL=redis://localhost:6379/5`) để không đụng dữ liệu dự án khác.

| Tài khoản | Mật khẩu mặc định | Vai trò |
|---|---|---|
| `admin` | `doi-mat-khau-nay` | Lưu Đức Anh — `ADMIN` (vào được `/admin/`) |
| `operator` | `doi-mat-khau-nay` | Người vận hành — `OPERATOR` |

Đổi mật khẩu trước khi demo: `.\.venv\Scripts\python manage.py changepassword admin`

## 2. Chạy hệ thống — 2 tiến trình (+1 nếu chưa cắm mạch)

```powershell
# Terminal 1 — REST API + WebSocket, cổng 8000
.\.venv\Scripts\daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Terminal 2 — MQTT worker: nhận số đo, nhận phản hồi thiết bị, quét lệnh hết giờ
.\.venv\Scripts\python manage.py mqtt_worker

# Terminal 3 (tuỳ chọn) — ESP8266 giả lập, KHÔNG chạy cùng mạch thật
.\.venv\Scripts\python manage.py fake_esp                     # bình thường
.\.venv\Scripts\python manage.py fake_esp --no-respond        # lệnh nào cũng FAILED sau 5–6 giây
.\.venv\Scripts\python manage.py fake_esp --missing-humidity 5  # biểu đồ độ ẩm đứt nét
```

| Địa chỉ | Nội dung |
|---|---|
| <http://localhost:8000/api/schema/swagger-ui/> | Swagger — bấm **Authorize**, nhập `Token <token>` (có chữ `Token`) |
| <http://localhost:8000/admin/> | Trang quản trị — sửa ngưỡng cảm biến, xem lịch sử |
| `ws://localhost:8000/ws/realtime/?token=<token>` | WebSocket |

**Nối frontend:** đặt `VITE_USE_MOCK=false` trong `frontend/.env.development` rồi `npm run dev`.
Không phải sửa dòng code nào của frontend.

## 3. Kiểm thử

```powershell
.\.venv\Scripts\python manage.py test          # 52 ca, không cần Mosquitto / Redis
```

Tên hàm test mang mã ca của `05-API.md` §10 (`test_A07f_…`) để tra ngược.

## 4. Bản đồ code — cần sửa X thì mở file nào

```
backend/
├── config/
│   ├── settings.py        cấu hình; mọi thứ đổi theo máy đọc từ .env
│   ├── urls.py            bảng định tuyến 10 endpoint REST + Swagger + admin
│   ├── asgi.py            HTTP + WebSocket chung cổng 8000
│   ├── exceptions.py      lỗi thống nhất {error:{code,message,details}} — 9 mã
│   └── pagination.py      page / page_size (1→100), 404 PAGE_NOT_FOUND
└── apps/
    ├── core/              dùng chung: TiebreakOrderingFilter, RangeCheckForm, Profile, schema lỗi
    ├── users/             bảng users_user, đăng nhập / đăng xuất
    ├── sensors/           danh mục cảm biến + số đo; 4 endpoint /api/sensors*
    ├── devices/           thiết bị + lịch sử thao tác; điều khiển; publish MQTT
    ├── realtime/          WebSocket: xác thực ?token=, consumer, 2 sự kiện
    └── mqtt/              tiến trình 2: worker, xử lý message, ESP giả lập
```

Mỗi app có cùng bộ file: `models.py` (bảng) · `serializers.py` (hình dạng JSON) ·
`filters.py` (tham số lọc) · **`services.py` (logic nghiệp vụ)** · `views.py` (mỏng, chỉ gọi service) · `admin.py`.

| Muốn đổi… | Mở |
|---|---|
| Hình dạng JSON trả về | `apps/<app>/serializers.py` |
| Tham số lọc của bảng Data Sensor / Action History | `apps/sensors/filters.py` · `apps/devices/filters.py` |
| Cách tách một message cảm biến thành 3 bản ghi, ngưỡng BR-02 | `apps/sensors/services.py` → `record_cycle()` |
| Biểu đồ 20 chu kỳ | `apps/sensors/services.py` → `chart_cycles()` |
| Gửi lệnh / 409 / 503 | `apps/devices/services.py` → `send_command()` |
| Xử lý `device_respond`, cập nhật trạng thái đèn | `apps/devices/services.py` → `confirm_command()` |
| Timeout 5 giây | `apps/devices/services.py` → `expire_pending_commands()` · hằng số ở `settings.py` |
| Payload gửi xuống ESP (`device_control`) | `apps/devices/mqtt_publisher.py` |
| Tên topic, QoS | `apps/mqtt/topics.py` |
| Hình dạng sự kiện WebSocket | `apps/realtime/events.py` |
| Câu thông báo lỗi, mã lỗi | `config/exceptions.py` |
| Thông tin trang Profile | `.env` (các biến `PROFILE_*`, `LINK_*`) |
| Ngưỡng cảm biến, thêm cảm biến | Trang `/admin/` → **khởi động lại `mqtt_worker`** |

## 5. Bẫy đã gặp khi chạy thật

| Triệu chứng | Nguyên nhân | Đã xử lý |
|---|---|---|
| `POST .../control` mất ~2 giây | `localhost` → Windows thử IPv6 `::1` trước, Mosquitto chỉ nghe IPv4, mỗi lần bị từ chối tốn ~2 giây | `MQTT_HOST=127.0.0.1` — **đừng đổi về `localhost`** |
| Đèn đã bật mà lịch sử ghi FAILED | Thiết bị trả lời trước khi bản ghi PENDING kịp commit | `send_command()` commit trước rồi mới publish — `PLAN.md` §4 |
| Log tiếng Việt vỡ thành `Đ�` | Console Windows cp1252 khi xuất ra pipe/file | `config/__init__.py` ép UTF-8 |
| WebSocket bị từ chối khi demo trong LAN | Origin của trình duyệt không nằm trong `ALLOWED_HOSTS` | Thêm IP laptop vào `ALLOWED_HOSTS` **và** `CORS_ALLOWED_ORIGINS` trong `.env` |
| Worker chạy, HTTP chạy, nhưng Dashboard không bao giờ nhận số liệu mới | Redis không chạy, hoặc hai tiến trình dùng khác `REDIS_URL` | Kiểm `docker ps` thấy `redis-dev`; cả hai tiến trình đọc chung `.env` |
