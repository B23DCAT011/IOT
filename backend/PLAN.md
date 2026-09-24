# KẾ HOẠCH CODE BACKEND

> Nguồn đặc tả: `docs/04-Database.md` v2.0 (schema) · `docs/05-API.md` v2.1 (hợp đồng API, WS, MQTT) ·
> `docs/03-Sequence.md` (luồng) · `CLAUDE.md` §5 (stack, 2 tiến trình).
> Frontend ở `frontend/` đang chạy bằng MSW theo đúng `05-API.md` v2.1 ⇒ backend phải trả **đúng từng tên trường**.

## 1. Bức tranh tổng thể

```
                  ┌──────────── Tiến trình 1: daphne config.asgi:application ────────────┐
Frontend ──HTTP──►│ config/urls.py → apps/*/views.py → apps/*/services.py → PostgreSQL   │
Frontend ◄──WS────│ apps/realtime/consumers.py  ◄── Redis (nhóm "realtime") ◄──┐          │
                  │ apps/devices/mqtt_publisher.py ──publish device_control──►  │  Broker  │
                  └──────────────────────────────────────────────────────────────┼─────────┘
                  ┌──────────── Tiến trình 2: python manage.py mqtt_worker ──────┼─────────┐
ESP8266 ──MQTT───►│ apps/mqtt/handlers.py → sensors/devices services → DB → realtime/events │
                  │ vòng quét 1 giây: devices.services.expire_pending_commands (BR-03)    │
                  └───────────────────────────────────────────────────────────────────────┘
```

**Quy tắc chia code** — mỗi app có cùng một bộ file, đọc tên file là biết tìm gì:

| File | Chứa gì | Không chứa gì |
|---|---|---|
| `models.py` | Bảng, ràng buộc, chỉ mục — chép từ `04-Database.md` §8 | Logic nghiệp vụ |
| `serializers.py` | Hình dạng JSON vào/ra — chép từ `05-API.md` §4 | Truy vấn |
| `filters.py` | Tham số lọc của bảng có phân trang (UC-04) | — |
| `services.py` | **Logic nghiệp vụ**, dùng chung cho API view **và** MQTT worker | Đối tượng `request` |
| `views.py` | Mỏng: đọc request → gọi service → trả serializer | SQL, MQTT |
| `admin.py` | Trang quản trị Django để xem/sửa dữ liệu khi demo | — |

## 2. Các module và thứ tự làm

| # | Module | File chính | Đặc tả | Trạng thái |
|---|---|---|---|---|
| M0 | **Khung dự án** — settings, `.env`, urls, asgi | `config/` | API §7.1, §7.2 | ✅ |
| M1 | **Lõi dùng chung** — lỗi thống nhất 9 mã, phân trang, sắp xếp có cột phá hoà, form kiểm khoảng lọc, Profile | `config/exceptions.py` · `config/pagination.py` · `apps/core/` | API §2.6–2.8, §4.7, §7.3, §7.5 | ✅ |
| M2 | **Người dùng + đăng nhập** — `User(AbstractUser)`, seed 2 tài khoản, login/logout token | `apps/users/` | DB §4.1, §8.1 · API §4.8, §4.9, §7.7 | ✅ |
| M3 | **Cảm biến** — danh mục + số đo, seed 3 cảm biến, 4 endpoint, ghi một chu kỳ | `apps/sensors/` | DB §4.2, §4.3, §6.4, §7.1 · API §4.0–4.3 | ✅ |
| M4 | **Thiết bị + lịch sử** — seed 2 thiết bị, điều khiển (202/409/503), xác nhận, timeout | `apps/devices/` | DB §4.4, §4.5, §5.3, §6 · API §4.4–4.6, §7.4 | ✅ |
| M5 | **Realtime** — WebSocket `?token=`, đóng `4401`, 2 sự kiện | `apps/realtime/` | API §5, §7.6 | ✅ |
| M6 | **MQTT worker** — tiến trình 2 + ESP8266 giả lập để test không cần mạch | `apps/mqtt/` | API §6 · SD-02, SD-03, SD-05 | ✅ |
| M7 | **Kiểm thử tự động** — các ca A-00 → A-23 chạy được không cần phần cứng | `apps/*/tests.py` | API §10 | ✅ |
| M8 | **Tài liệu vận hành** — README, cập nhật `CLAUDE.md` | `README.md` | — | ✅ |

## 3. Chi tiết từng module

### M0 — Khung dự án
- [x] `requirements.txt` ghim phiên bản (Django 5.2 — hỗ trợ Python 3.14, dùng `CheckConstraint(condition=)`)
- [x] `.env.example` (commit) + `.env` (không commit): DB, Redis, MQTT, Profile
- [x] `settings.py`: `AUTH_USER_MODEL` **trước lần migrate đầu**, `TIME_ZONE="UTC"`, chỉ `TokenAuthentication`, `LANGUAGE_CODE="vi"`
- [x] `urls.py`: `DefaultRouter(trailing_slash=False)` + login/logout/profile + Swagger
- [x] `asgi.py`: HTTP + WebSocket, `get_asgi_application()` gọi **trước** khi import middleware

### M1 — Lõi dùng chung
- [x] Bộ xử lý ngoại lệ: mọi lỗi → `{error:{code,message,details}}`; 9 mã; lỗi 500 cũng trả JSON
- [x] `INVALID_RANGE` nhận diện bằng **mã lỗi gắn vào ValidationError**, không so chuỗi thông báo (API §12 điểm 2b)
- [x] `StandardPagination`: `page_size` 1→100 tự hạ biên; sai kiểu → `400`; vượt trang → `404 PAGE_NOT_FOUND`
- [x] `TiebreakOrderingFilter`: luôn nối cột phá hoà (A-07f)
- [x] `GET /api/profile` đọc `.env`; biến trống → `null`

### M2 — Người dùng
- [x] Model + migration `0001`, seed `admin` / `operator` (mật khẩu băm bằng `make_password`)
- [x] `POST /api/auth/login`: `authentication_classes=[]`, `trim_whitespace=False`, sai → `400 INVALID_CREDENTIALS`
- [x] `POST /api/auth/logout`: xoá token → `204`

### M3 — Cảm biến
- [x] Model `SensorDevice`, `SensorData` (ordering `-recorded_at, sensor_id`; `db_index=False` cho FK)
- [x] Seed 3 cảm biến `room01_temp/humi/lux` kèm ngưỡng BR-02
- [x] `services.py`: `SensorCatalog` (nạp 1 lần), `record_cycle()` — **một** `recorded_at` cho cả chu kỳ, loại riêng số đo hỏng
- [x] `services.py`: `latest_readings()` (`DISTINCT ON`), `chart_cycles()` (chốt tập mốc trước rồi xoay bảng)
- [x] `GET /api/sensors/devices`, `/latest`, `/chart`, `/api/sensors` (lọc `sensor`, `node`, `value__*` bắt buộc kèm `sensor`, `recorded_at__*`)

### M4 — Thiết bị
- [x] Model `Device`, `ActionHistory` (`latency_ms` là property), seed `room01_lamp` D5, `room01_fan` D6
- [x] `mqtt_publisher.py`: client ngắn hạn, ID ngẫu nhiên, `loop_start()` trước `publish(qos=1)`, chờ PUBACK
- [x] `services.send_command()`: `transaction.atomic()` → kiểm bận (409) → ghi PENDING → publish (lỗi ⇒ cuộn ngược, 503)
- [x] `services.confirm_command()`: `select_for_update` + `status=PENDING`; chỉ cập nhật `current_state` khi SUCCESS
- [x] `services.expire_pending_commands()`: quá 5 giây → FAILED, đặt `responded_at`
- [x] `GET /api/devices` (không phân trang), `POST /api/devices/{id}/control`, `GET /api/actions` (lọc `user=none`)

### M5 — Realtime
- [x] `TokenAuthMiddleware` đọc `?token=`
- [x] Consumer: `accept()` **rồi** `close(4401)`; bỏ qua message từ client
- [x] `events.py`: dựng + phát `sensor.data`, `device.state` — một chỗ duy nhất định nghĩa hình dạng sự kiện

### M6 — MQTT worker
- [x] `client.py` + `topics.py`: một chỗ tạo client paho và giữ tên 3 topic
- [x] `handlers.py`: JSON hỏng → log, **không dừng worker** (NFR-16)
- [x] `mqtt_worker`: subscribe `data_sensors` (QoS 0), `device_respond` (QoS 1), tự đăng ký lại khi mất kết nối, vòng quét timeout 1 giây
- [x] `fake_esp`: giả lập ESP8266 — gửi số đo 2 giây/lần và trả lời lệnh — để demo/kiểm thử khi chưa cắm mạch

### M7 — Kiểm thử
- [x] `python manage.py test` — mock hàm publish, không cần broker/Redis
- [x] Chạy thật end-to-end: daphne + worker + fake_esp + WebSocket

### M8 — Tài liệu
- [x] `backend/README.md`: cài đặt, 3 terminal, bản đồ "cần sửa X thì mở file Y"
- [x] `CLAUDE.md` §0: ghi trạng thái phiên này

## 4. Chỗ cố ý lệch so với mã mẫu trong `05-API.md` §7

| Mã mẫu trong tài liệu | Code thật | Lý do |
|---|---|---|
| `TiebreakOrderingFilter` nối `sensor_id` | Nối `sensor_id` **rồi** `id` | Với `?ordering=-value`, hai số đo cùng cảm biến cùng giá trị vẫn hoà nhau nếu chỉ nối `sensor_id` → A-07f có thể trượt. `id` là duy nhất nên thứ tự luôn xác định |
| Handler trả `None` cho lỗi không phải của DRF (Django tự trả trang HTML 500) | Trả JSON `500 INTERNAL_ERROR` + ghi traceback ra log | Frontend chỉ hiểu một hình dạng lỗi; mã `INTERNAL_ERROR` có trong bảng 9 mã nhưng mã mẫu không bao giờ sinh ra nó |
| Phân biệt `INVALID_RANGE` bằng nội dung thông báo | Gắn `code="invalid_range"` vào lỗi của form | So chuỗi tiếng Việt thì đổi câu chữ là hỏng |
| `publish_control()` nằm **bên trong** `transaction.atomic()`; broker lỗi thì cuộn ngược | Commit bản ghi PENDING **trước**, rồi mới publish; broker lỗi thì **xoá** bản ghi vừa tạo | **Lỗi thật đã bắt được khi chạy end-to-end:** thiết bị trả lời (~20 ms) trước khi giao dịch commit → worker không thấy bản ghi PENDING, bỏ qua phản hồi, 5 giây sau đánh FAILED trong khi đèn đã bật. Kết quả với người dùng vẫn đúng UC-02 E2 (503, không để lại lịch sử). ⚠️ Cần sửa lại `05-API.md` §4.5, §7.4 và `03-Sequence.md` SD-01 §2.4 |
| `publish_control` gọi `publish()` ngay sau `connect()` | Chờ `CONNACK` trước, rồi mới publish | Sai mật khẩu MQTT thì `connect()` vẫn "thành công" (CONNACK đến sau); phải chờ nó mới biết để trả `503` |
