# ĐẶC TẢ GIAO DIỆN LẬP TRÌNH (API)
## Hệ thống giám sát và điều khiển môi trường phòng dựa trên IoT

| | |
|---|---|
| **Phiên bản** | 2.1 |
| **Ngày** | 14/09/2026 |
| **Tài liệu liên quan** | `01-SRS.md` v0.5 (§4.3, §4.4, §5), `02-UseCase.md` v2.0 (§5, §6), `04-Database.md` **v2.0** (§4, §7), `03-Sequence.md` |
| **Vị trí trong báo cáo** | Chương 3 — Thiết kế chi tiết |

---

## MỤC LỤC

1. [Giới thiệu](#1-giới-thiệu)
2. [Quy ước chung](#2-quy-ước-chung)
3. [Bảng tổng hợp endpoint](#3-bảng-tổng-hợp-endpoint)
4. [Đặc tả chi tiết REST API](#4-đặc-tả-chi-tiết-rest-api)
5. [Giao diện WebSocket](#5-giao-diện-websocket)
6. [Giao diện MQTT](#6-giao-diện-mqtt)
7. [Gợi ý cài đặt](#7-gợi-ý-cài-đặt-tuần-3)
8. [OpenAPI, Swagger và Postman](#8-openapi-swagger-và-postman)
9. [Ma trận truy vết](#9-ma-trận-truy-vết)
10. [Kịch bản kiểm thử API](#10-kịch-bản-kiểm-thử-api)
11. [Quyết định chốt tại tài liệu này](#11-quyết-định-chốt-tại-tài-liệu-này)
12. [Điểm còn cần chốt](#12-điểm-còn-cần-chốt)
13. [Lịch sử phiên bản](#13-lịch-sử-phiên-bản)

---

## 1. GIỚI THIỆU

### 1.1 Mục đích

Tài liệu này đặc tả **hợp đồng giao tiếp** giữa các thành phần của hệ thống, ở mức đủ chi tiết để lập trình Frontend và Backend độc lập với nhau. Nó bao gồm ba nhóm giao diện:

| Nhóm | Bên gọi → bên phục vụ | Số lượng |
|---|---|---|
| **REST API** | Frontend → Backend (P1) | 10 endpoint chính (8 nghiệp vụ + đăng nhập, đăng xuất) |
| **WebSocket** | Backend (P1) → Frontend | 1 kênh, 2 sự kiện |
| **MQTT** | ESP8266 ↔ Broker ↔ Backend | 3 topic |

Mỗi endpoint ở đây bắt nguồn từ một mũi tên HTTP đã vẽ trong `03-Sequence.md`; mỗi tên trường JSON lấy đúng tên cột đã chốt ở `04-Database.md` §4. Tài liệu **không** phát sinh khái niệm dữ liệu mới.

### 1.2 Quan hệ với các tài liệu khác

| Tài liệu | Vai trò đối với tài liệu này |
|---|---|
| `01-SRS.md` §4.4 | Danh sách endpoint ở mức tóm tắt — tài liệu này là bản chi tiết hóa |
| `01-SRS.md` §4.3 | Payload MQTT gốc; §6 của tài liệu này chuẩn hóa lại kiểu và ràng buộc |
| `02-UseCase.md` §5 | Luồng ngoại lệ E1→E5 của mỗi UC quyết định mã lỗi HTTP |
| `02-UseCase.md` §6 | BR-08, BR-09, BR-10 quyết định giá trị mặc định của tham số truy vấn |
| `03-Sequence.md` §8 | Bảng tổng hợp thông điệp — nguồn của §3 |
| `03-Sequence.md` §10 | 5 điểm còn treo; tài liệu này chốt 3 điểm ①③⑤ (xem §11) |
| `04-Database.md` §4 | Tên trường và kiểu dữ liệu của mọi response |

Khi mâu thuẫn: `04-Database.md` là bản có hiệu lực về **tên và kiểu dữ liệu**; tài liệu này là bản có hiệu lực về **đường dẫn, tham số, mã trạng thái và hình dạng JSON**.

### 1.3 Phạm vi

Đặc tả áp dụng cho phiên bản đồ án: **một phòng, mạng LAN nội bộ, người dùng phải đăng nhập** (từ bản 2.1 — §2.2). Các nội dung sau **nằm ngoài phạm vi** và được ghi lại ở §12 để trả lời khi vấn đáp: phân quyền theo vai trò, giới hạn tần suất gọi (rate limit), đánh phiên bản API, HTTPS.

> ⚠️ **Bản 2.1 đi trước các tài liệu khác.** `01-SRS.md` §8.2 vẫn ghi "không đăng nhập", và các mã **UC-08**, **FR-19**, **BR-13** mà tài liệu này tham chiếu chưa có trong `01-SRS.md` / `02-UseCase.md`. Danh sách việc cần đồng bộ ở §12 điểm 7.

---

## 2. QUY ƯỚC CHUNG

### 2.1 Địa chỉ gốc

| Môi trường | REST | WebSocket |
|---|---|---|
| Phát triển | `http://localhost:8000/api` | `ws://localhost:8000/ws/realtime/` |
| Demo trong LAN | `http://<IP-LAN-laptop>:8000/api` | `ws://<IP-LAN-laptop>:8000/ws/realtime/` |

Frontend đọc địa chỉ từ biến môi trường `VITE_API_BASE_URL` và `VITE_WS_URL`, không viết cứng trong mã (NFR-11).

Cả hai đều do **cùng một tiến trình `daphne`** phục vụ (P1, `01-SRS.md` §2.2.1) nên chỉ có một cổng duy nhất là `8000`.

### 2.2 Xác thực bằng token *(từ bản 2.1)*

Mọi endpoint REST và kênh WebSocket đều **yêu cầu đăng nhập**, trừ `POST /api/auth/login` và ba đường dẫn tài liệu ở §3.3.

| Mục | Quy ước |
|---|---|
| Cơ chế | Token của DRF (`rest_framework.authtoken`) |
| Lấy token | `POST /api/auth/login` với `username` + `password` (§4.8) |
| Gửi token (REST) | Header `Authorization: Token <token>` — có chữ `Token` và **một dấu cách** đứng trước |
| Gửi token (WebSocket) | Tham số `?token=<token>` trên đường dẫn (§5.1) |
| Thời hạn | Không hết hạn. Token chỉ mất hiệu lực khi gọi `POST /api/auth/logout` (§4.9) |
| Thiếu / sai / đã thu hồi token | `401 UNAUTHENTICATED` → Frontend xoá token đã lưu và chuyển về trang đăng nhập |
| Phân quyền | **Chưa phân quyền theo vai trò**: tài khoản `ADMIN` và `OPERATOR` gọi được mọi endpoint. Cột `role` vẫn chỉ mang tính mô tả (§12 điểm 3b) |
| Frontend lưu token ở đâu | `localStorage`, cùng đối tượng `user` nhận được lúc đăng nhập |

> **Vì sao token chứ không phải session cookie.** Frontend (`:5173`) và Backend (`:8000`) khác origin (§2.9). Dùng session thì phải bật `CORS_ALLOW_CREDENTIALS`, gửi kèm CSRF token cho mọi `POST` và xử lý thuộc tính `SameSite` của cookie — ba chỗ dễ sai mà lỗi chỉ hiện ra là `403` chung chung. Token đi trong header nên không dính tới cookie lẫn CSRF, lại gọi thử bằng Postman hay Swagger được ngay.
>
> **Vì sao không dùng JWT.** JWT cần thêm thư viện (`djangorestframework-simplejwt`) và luồng làm mới token. Lợi ích chính của nó là máy chủ không phải tra CSDL ở mỗi request — không đáng kể với hệ thống một phòng trong LAN. Ngược lại, token của DRF **thu hồi được ngay** khi đăng xuất, còn JWT thì không.
>
> **Cái giá phải chấp nhận.** Token lưu ở `localStorage` đọc được bằng JavaScript, nên nếu trang bị chèn mã độc (XSS) thì token bị lộ. Chấp nhận ở phạm vi LAN; đưa ra Internet thì phải chuyển sang cookie `HttpOnly` kèm HTTPS. Xác thực ở tầng MQTT (NFR-09) là chuyện riêng, không đổi.

> ⚠️ **Bẫy cấu hình: chỉ khai `TokenAuthentication`.** Nếu `DEFAULT_AUTHENTICATION_CLASSES` có `SessionAuthentication` đứng đầu, request thiếu token nhận **`403`** thay vì `401`. DRF chỉ trả `401` khi lớp xác thực **đầu tiên** biết sinh header `WWW-Authenticate`, mà `SessionAuthentication` thì không. Frontend chờ `401` nên sẽ không chuyển về trang đăng nhập (§7.1, ca kiểm thử A-21).

### 2.3 Định dạng dữ liệu

| Mục | Quy ước |
|---|---|
| Kiểu nội dung | `application/json; charset=utf-8` cho cả request và response |
| Tên trường | `snake_case`, giữ nguyên tên cột CSDL (§6 `CLAUDE.md`) |
| Số thực | `temperature`, `humidity` — kiểu `float`, có thể `null` |
| Số nguyên | `light` — kiểu `int` (lux), có thể `null` |
| Chuỗi liệt kê | Viết **HOA**: `ON`, `OFF`, `PENDING`, `SUCCESS`, `FAILED`, `LIGHT`, `FAN`, `OTHER` |
| Nhãn tiếng Việt | **Không** trả về từ API. Frontend tự ánh xạ `ON → "Bật"`, `LIGHT → "Đèn"`… vì Frontend vốn đã sở hữu toàn bộ chuỗi hiển thị (tiêu đề cột, thông báo rỗng) |

### 2.4 Mốc thời gian — quy ước quan trọng nhất của tài liệu

**Mọi mốc thời gian trong API đều là ISO-8601 theo giờ UTC, kết thúc bằng `Z`:**

```
2026-08-17T10:30:02.451231Z
```

Điều này đòi hỏi `settings.py` đặt **`TIME_ZONE = "UTC"`** kèm `USE_TZ = True`. Lý do: DRF chuyển `datetime` sang `settings.TIME_ZONE` trước khi tuần tự hóa — nếu đặt `TIME_ZONE = "Asia/Ho_Chi_Minh"` thì API sẽ trả `2026-08-17T17:30:02+07:00`, lệch với toàn bộ ví dụ trong `01-SRS.md`, `03-Sequence.md` và tài liệu này. Việc đổi sang giờ Việt Nam để hiển thị là **trách nhiệm của Frontend** (`toLocaleString("vi-VN")`), đúng quy ước số 4 của `04-Database.md` §2.

**Chiều ngược lại — tham số lọc theo thời gian phải kèm múi giờ.** Frontend gửi `recorded_at__gte=2026-08-17T00:00:00+07:00`, **không** gửi `2026-08-17T00:00:00` hay `2026-08-17`. Chuỗi thiếu múi giờ sẽ được Django hiểu là giờ UTC (do `TIME_ZONE = "UTC"`), khiến khoảng "từ 0h ngày 17" thực chất bắt đầu từ 7h sáng giờ Việt Nam — sai lệch 7 tiếng mà không có thông báo lỗi nào. Đây là lỗi kinh điển khi ghép bộ chọn ngày của Frontend với django-filter.

### 2.5 Không có dấu gạch chéo ở cuối đường dẫn

Toàn bộ endpoint viết **không** kèm `/` cuối: `/api/sensors`, `/api/devices/1/control`. Router phải khai báo `DefaultRouter(trailing_slash=False)`.

**Vì sao phải nói rõ:** mặc định `DefaultRouter` sinh ra `/api/sensors/`. Khi đó gọi `POST /api/devices/1/control` (thiếu `/`) sẽ kích hoạt `APPEND_SLASH` của Django — Django trả về chuyển hướng `301` tới đường dẫn có `/`, và **trình duyệt gửi lại request dưới dạng GET, mất toàn bộ body**. Lệnh điều khiển biến mất một cách im lặng. Chốt `trailing_slash=False` để đường dẫn trong Postman, trong mã Frontend và trong tài liệu này khớp nhau tuyệt đối.

> Ngoại lệ duy nhất: đường dẫn WebSocket `/ws/realtime/` **có** dấu gạch chéo cuối, vì nó khai báo thủ công trong `routing.py` và giữ nguyên như `01-SRS.md` §4.4.

### 2.6 Cấu trúc lỗi thống nhất

Mọi phản hồi có mã trạng thái ≥ 400 đều mang đúng một hình dạng:

```json
{
  "error": {
    "code": "DEVICE_BUSY",
    "message": "Thiết bị đang chờ phản hồi cho lệnh trước đó.",
    "details": null
  }
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `code` | string | Mã lỗi ổn định, viết HOA kèm gạch dưới. Frontend rẽ nhánh theo trường này, **không** so khớp theo `message` |
| `message` | string | Câu tiếng Việt hiển thị được ngay cho người dùng |
| `details` | object \| null | Lỗi theo từng trường khi dữ liệu gửi lên sai; `null` với các lỗi còn lại |

Ví dụ lỗi kiểm tra dữ liệu đầu vào (`details` có nội dung):

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dữ liệu gửi lên không hợp lệ.",
    "details": { "action": ["Giá trị phải là \"ON\" hoặc \"OFF\"."] }
  }
}
```

**Vì sao không dùng thẳng định dạng mặc định của DRF:** DRF trả `{"detail": "..."}` cho ngoại lệ nhưng lại trả `{"action": ["..."]}` cho lỗi serializer — hai hình dạng khác nhau trong cùng một API. Frontend sẽ phải viết hai nhánh xử lý và vẫn không có mã lỗi ổn định để so sánh. Một bộ xử lý ngoại lệ dài khoảng 20 dòng (§7.5) gộp cả hai về một dạng duy nhất.

### 2.7 Bảng mã trạng thái HTTP

| Mã | Khi nào dùng | Xuất hiện ở |
|---|---|---|
| `200 OK` | Đọc dữ liệu thành công | Mọi endpoint `GET` |
| `202 Accepted` | Lệnh điều khiển đã được tiếp nhận, **chưa** hoàn tất | `POST /api/devices/{id}/control` |
| `204 No Content` | Đăng xuất thành công, không có nội dung trả về | `POST /api/auth/logout` |
| `400 Bad Request` | Tham số hoặc body sai kiểu, sai giá trị; sai tên đăng nhập hoặc mật khẩu | `POST .../control`, bộ lọc ngày sai, `POST /api/auth/login` |
| `401 Unauthorized` | Thiếu token, token sai hoặc đã bị thu hồi | Mọi endpoint, trừ `POST /api/auth/login` và §3.3 |
| `404 Not Found` | Không tồn tại tài nguyên, hoặc số trang vượt quá tổng số trang | `POST .../control`, mọi endpoint có phân trang |
| `409 Conflict` | Thiết bị còn một lệnh `PENDING` chưa kết thúc | `POST .../control` |
| `500 Internal Server Error` | Lỗi không lường trước ở phía máy chủ | — |
| `503 Service Unavailable` | Không kết nối được MQTT broker | `POST .../control` |

Danh sách mã lỗi (`error.code`) dùng trong toàn hệ thống:

| `code` | HTTP | Ý nghĩa | Nguồn |
|---|---|---|---|
| `VALIDATION_ERROR` | 400 | Body hoặc tham số truy vấn không hợp lệ | UC-02 E4, UC-04 E2 |
| `INVALID_RANGE` | 400 | `…__gte` lớn hơn `…__lte` — dùng chung cho **cả khoảng thời gian lẫn khoảng giá trị số**; `details` chỉ ra đúng cặp tham số bị sai | UC-04 E2 |
| `INVALID_CREDENTIALS` | 400 | Sai tên đăng nhập, sai mật khẩu, hoặc tài khoản đã khóa (`is_active = false`) — **cùng một thông báo** cho cả ba trường hợp | UC-08 E1 |
| `UNAUTHENTICATED` | 401 | Thiếu token, token sai hoặc đã bị thu hồi | BR-13 |
| `NOT_FOUND` | 404 | Không có tài nguyên tương ứng | UC-02 E3 |
| `PAGE_NOT_FOUND` | 404 | Số trang vượt quá tổng số trang | UC-03 A2 |
| `DEVICE_BUSY` | 409 | Thiết bị đang có lệnh `PENDING` | BR-04 |
| `BROKER_UNAVAILABLE` | 503 | Không kết nối/publish được tới Mosquitto | UC-02 E2 |
| `INTERNAL_ERROR` | 500 | Ngoại lệ không xác định | — |

**Tổng 9 mã** (bản 2.0 có 7; bản 2.1 thêm `INVALID_CREDENTIALS` và `UNAUTHENTICATED`).

> **Vì sao sai mật khẩu là `400` chứ không phải `401`.** Frontend có **một** bộ chặn chung cho mọi request: gặp `401` thì xoá token và chuyển về trang đăng nhập (§2.2). Nếu sai mật khẩu cũng trả `401`, bộ chặn này sẽ kích hoạt ngay trên chính trang đăng nhập, và phải viết thêm ngoại lệ cho riêng đường dẫn đó. Giữ `401` với đúng một nghĩa *"chưa đăng nhập hoặc phiên đã hết"* thì bộ chặn không cần điều kiện nào.
>
> **Vì sao không báo riêng "sai tên đăng nhập" và "sai mật khẩu".** Báo riêng thì người ngoài dò ra được tên tài khoản nào đang tồn tại.

### 2.8 Phân trang, tìm kiếm, lọc, sắp xếp

Áp dụng chung cho `GET /api/sensors` và `GET /api/actions` (UC-04 `«extend»` UC-03 và UC-05).

| Tham số | Kiểu | Mặc định | Ràng buộc | Nguồn |
|---|---|---|---|---|
| `page` | int | `1` | ≥ 1; vượt tổng số trang → `404 PAGE_NOT_FOUND` | BR-08 |
| `page_size` | int | `10` | 1 → 100; lớn hơn 100 thì **tự hạ về 100** | BR-08, UC-04 E3 |
| `search` | string | — | Không phân biệt hoa thường, khớp một phần | FR-10 |
| `ordering` | string | Theo từng endpoint | Chỉ nhận các trường được liệt kê; tiền tố `-` là giảm dần | BR-09, FR-11 |

**Cấu trúc phản hồi phân trang** (`PageNumberPagination` mặc định của DRF):

```json
{
  "count": 36134,
  "next": "http://localhost:8000/api/sensors?page=2",
  "previous": null,
  "results": [ /* … */ ]
}
```

**Quy tắc xử lý tham số sai:**

| Tình huống | Xử lý | Lý do |
|---|---|---|
| Giá trị **ngoài khoảng** cho phép (`page_size=500`) | Tự hạ về biên (100), vẫn trả `200` | Đúng UC-04 E3; người dùng không mất thao tác |
| Giá trị **sai kiểu** (`page_size=abc`, `limit=abc`) | `400 VALIDATION_ERROR` | Đây là lỗi lập trình phía gọi, im lặng bỏ qua sẽ khó truy vết |
| `ordering` chứa trường không được phép | **Bỏ qua**, dùng thứ tự mặc định | Hành vi sẵn có của `OrderingFilter`; không cần chặn |
| `…__gte` > `…__lte` | `400 INVALID_RANGE` | UC-04 E2 — giao diện tô đỏ đúng cặp ô nhập bị sai |

**Về `404` khi vượt số trang.** DRF trả `404` cho `?page=999` khi chỉ có 12 trang. Frontend **phải coi đây là trạng thái rỗng**, hiển thị "Không còn dữ liệu, quay lại trang 1" theo UC-03 A2, chứ không phải màn hình lỗi. Đây cũng là lý do `03-Sequence.md` §7.3 yêu cầu đặt lại `page = 1` mỗi khi đổi bộ lọc.

### 2.9 CORS và nguồn gốc kết nối

Frontend chạy ở `http://localhost:5173` (Vite), Backend ở `http://localhost:8000` — **khác cổng nên là khác origin**. Cần cấu hình:

```python
# settings.py
CORS_ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
```

Hai điểm dễ mất thời gian khi ghép Frontend:

1. **WebSocket không đi qua CORS** mà đi qua `AllowedHostsOriginValidator` của Channels (`asgi.py`). Nếu bọc router bằng validator này thì `ALLOWED_HOSTS` phải chứa host của Frontend, nếu không kết nối bị đóng ngay với mã `403` mà trình duyệt chỉ báo chung chung là "WebSocket closed".
2. Khi demo bằng IP LAN, phải thêm cả `http://<IP-LAN>:5173` vào `CORS_ALLOWED_ORIGINS` và `<IP-LAN>` vào `ALLOWED_HOSTS`.
3. **Header `Authorization` không cần cấu hình CORS thêm**: `django-cors-headers` đã cho phép sẵn header này trong `CORS_ALLOW_HEADERS` mặc định. Cũng **không** bật `CORS_ALLOW_CREDENTIALS`, vì token không đi bằng cookie (§2.2).

### 2.10 Yêu cầu hiệu năng áp lên API

| Ràng buộc | Giá trị | Ghi chú |
|---|---|---|
| NFR-03 | Mọi endpoint `GET` trả kết quả ≤ **500 ms** với bảng ≤ 100.000 bản ghi | Đo bằng tab Network của trình duyệt hoặc Postman |
| NFR-01 | `POST .../control` trả `202` trong ≤ **200 ms** | Vì không chờ phần cứng — xem §4.5 |
| NFR-02 | Từ lúc ESP publish tới lúc Frontend nhận sự kiện WebSocket ≤ **1 giây** | Không đo được bằng Postman, đo ở UAT |

---

## 3. BẢNG TỔNG HỢP ENDPOINT

### 3.1 Endpoint chính

| # | Phương thức | Đường dẫn | Chức năng | UC | Sequence |
|---|---|---|---|---|---|
| 1 | `GET` | `/api/sensors/devices` | **Danh mục cảm biến** | UC-01, UC-03 | SD-04 |
| 2 | `GET` | `/api/sensors/latest` | Số đo mới nhất **của từng cảm biến** *(mảng)* | UC-01 | SD-04 |
| 3 | `GET` | `/api/sensors/chart` | N chu kỳ gần nhất cho biểu đồ | UC-01 | SD-04 |
| 4 | `GET` | `/api/sensors` | Bảng số đo, có lọc/sắp xếp/phân trang | UC-03, UC-04 | SD-06 |
| 5 | `GET` | `/api/devices` | Danh sách thiết bị kèm trạng thái | UC-01 | SD-04 |
| 6 | `POST` | `/api/devices/{id}/control` | Gửi lệnh bật/tắt; người thao tác lấy từ token | UC-02 | SD-01, SD-02, SD-05 |
| 7 | `GET` | `/api/actions` | Bảng lịch sử thao tác | UC-05, UC-04 | SD-06 |
| 8 | `GET` | `/api/profile` | Thông tin sinh viên và liên kết bàn giao | UC-06 | *(không có)* |
| 9 | `POST` | `/api/auth/login` | **Đăng nhập**, trả token | UC-08 | *(không có)* |
| 10 | `POST` | `/api/auth/logout` | **Đăng xuất**, thu hồi token | UC-08 | *(không có)* |
| 11 | `WS` | `/ws/realtime/?token=…` | Kênh đẩy sự kiện `sensor.data`, `device.state` | UC-01, UC-02 | SD-02→SD-05 |

**Tổng: 10 endpoint REST + 1 kênh WebSocket.** Chỉ 10 endpoint REST xuất hiện trong Swagger (T-17) — WebSocket không thuộc đặc tả OpenAPI. Mọi endpoint trừ `POST /api/auth/login` đều yêu cầu token (§2.2).

> **Đăng nhập không có sequence riêng**, cùng lý do với UC-06: mỗi thao tác chỉ là một lời gọi HTTP, không có tương tác nhiều bước để vẽ.

### 3.2 Endpoint phụ trợ do router sinh ra

Ba ViewSet dùng `ReadOnlyModelViewSet` nên router tạo thêm các đường dẫn chi tiết. Chúng **không được Frontend sử dụng** nhưng rất tiện khi kiểm thử bằng Postman và khi trình bày Swagger:

| Đường dẫn | Trả về |
|---|---|
| `GET /api/sensors/{id}` | Một bản ghi cảm biến |
| `GET /api/devices/{id}` | Một thiết bị |
| `GET /api/actions/{id}` | Một bản ghi lịch sử thao tác |

Không có endpoint `POST` / `PUT` / `DELETE` nào cho ba bảng dữ liệu: bản ghi cảm biến do MQTT worker ghi, bản ghi lịch sử do luồng điều khiển sinh, thiết bị do data migration tạo (`04-Database.md` §10). Đây là hệ quả trực tiếp của phạm vi 8 use case, không phải thiếu sót. Các đường dẫn chi tiết này cũng yêu cầu token như mọi endpoint khác.

### 3.3 Endpoint tài liệu

| Đường dẫn | Nội dung |
|---|---|
| `/api/schema` | File OpenAPI 3.0 dạng YAML do `drf-spectacular` sinh |
| `/api/schema/swagger-ui/` | Giao diện Swagger UI, gọi thử được trực tiếp (T-17) |
| `/api/schema/redoc/` | Bản đọc dạng tài liệu *(tùy chọn)* |

Ba đường dẫn này **không yêu cầu đăng nhập** (`SERVE_PERMISSIONS` mặc định của `drf-spectacular` là `AllowAny` — đừng đổi), để mở Swagger được ngay khi trình bày. Muốn gọi thử endpoint ngay trong Swagger thì bấm **Authorize** và nhập kèm chữ `Token` — xem §8.1.

---

## 4. ĐẶC TẢ CHI TIẾT REST API

### 4.0 `GET /api/sensors/devices` — danh mục cảm biến

| Mục | Nội dung |
|---|---|
| **Use case** | UC-01 bước 3, UC-03, UC-04 |
| **Truy vấn ORM** | `SensorDevice.objects.filter(is_active=True)` |
| **Phân trang** | **Không** — `pagination_class = None`, bảng cố định 3 dòng |
| **Tham số** | Không có |

**Phản hồi `200 OK`**

```json
[
  { "id": 1, "code": "room01_temp", "name": "Nhiệt độ phòng",  "metric_type": "TEMPERATURE", "unit": "°C",  "node_id": "esp8266_room01" },
  { "id": 2, "code": "room01_humi", "name": "Độ ẩm phòng",     "metric_type": "HUMIDITY",    "unit": "%",   "node_id": "esp8266_room01" },
  { "id": 3, "code": "room01_lux",  "name": "Ánh sáng phòng",  "metric_type": "LIGHT",       "unit": "lux", "node_id": "esp8266_room01" }
]
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | int | Khóa kỹ thuật |
| `code` | string(30) | Mã nghiệp vụ, dùng cho tham số lọc `?sensor=` |
| `name` | string(100) | Nhãn hiển thị trên thẻ số liệu và cột bảng |
| `metric_type` | enum | `TEMPERATURE` / `HUMIDITY` / `LIGHT` |
| `unit` | string(10) | Đơn vị hiển thị |
| `node_id` | string(50) | Bo mạch chứa cảm biến |

> **Vì sao Frontend cần endpoint này.** Nhãn và đơn vị của ba thẻ số liệu **không được ghi cứng** trong mã Frontend (FR-17). Nhờ vậy, lắp thêm cảm biến thứ tư chỉ cần thêm một dòng vào danh mục và khởi động lại worker — Dashboard tự hiện thêm thẻ, bảng Data Sensor tự có thêm lựa chọn trong dropdown, không sửa mã.
>
> **Không trả `min_value` / `max_value`.** Hai cột ngưỡng chỉ phục vụ việc kiểm tra ở worker (BR-02); Frontend không dùng tới. Trả thêm chỉ khiến người đọc tưởng giao diện có chức năng cấu hình ngưỡng.

---

### 4.1 `GET /api/sensors/latest` — số đo mới nhất của từng cảm biến

| Mục | Nội dung |
|---|---|
| **Use case** | UC-01 bước 2 |
| **Sequence** | SD-04 (`03-Sequence.md` §5) |
| **Truy vấn ORM** | `SensorData.objects.select_related("sensor").order_by("sensor_id", "-recorded_at").distinct("sensor_id")` |
| **Chỉ mục dùng tới** | `sensordata_sensor_time_unique` |
| **Tham số** | Không có |

**Phản hồi `200 OK`** — **một mảng**, mỗi phần tử là số đo mới nhất của một cảm biến:

```json
[
  {
    "sensor": { "id": 1, "code": "room01_temp", "name": "Nhiệt độ phòng", "unit": "°C" },
    "value": 28.5,
    "recorded_at": "2026-08-17T10:30:02.451231Z"
  },
  {
    "sensor": { "id": 2, "code": "room01_humi", "name": "Độ ẩm phòng", "unit": "%" },
    "value": 72.0,
    "recorded_at": "2026-08-17T10:30:02.451231Z"
  },
  {
    "sensor": { "id": 3, "code": "room01_lux", "name": "Ánh sáng phòng", "unit": "lux" },
    "value": 350.0,
    "recorded_at": "2026-08-17T10:30:02.451231Z"
  }
]
```

| Trường | Kiểu | Null | Mô tả |
|---|---|---|---|
| `sensor` | object | ✗ | Cảm biến đã sinh ra số đo — lấy qua `select_related` |
| `value` | float | **✗** | Giá trị đo. Dòng tồn tại nghĩa là **đo được thật** |
| `recorded_at` | datetime | ✗ | Thời điểm **backend nhận** message, không phải giờ thiết bị (`04-Database.md` §2.1) |

**Phản hồi `200 OK` với mảng rỗng `[]`** — chưa có số đo nào trong CSDL (UC-01 A1).

> **Đổi ở bản 2.0: không còn dùng `204 No Content`.** Bản 1.3 trả một object duy nhất, nên "chưa có dữ liệu" cần một mã trạng thái riêng để Frontend khỏi phải kiểm `null` từng trường. Nay endpoint trả **mảng**, và mảng rỗng đã tự nó mang nghĩa "chưa có số đo nào" — giống hệt cách `/api/sensors/chart` xử lý (§4.2). Giữ `204` cho một endpoint trả mảng sẽ tạo ra **hai hình dạng phản hồi cho cùng một lời gọi**, đúng thứ mà §2.6 đang cố tránh.
>
> **Vì sao mảng có thể thiếu phần tử.** Cảm biến có trong danh mục nhưng chưa từng gửi số đo nào thì **không xuất hiện** trong mảng (UC-01 A3). Frontend dựng thẻ số liệu từ `/api/sensors/devices` rồi điền giá trị từ mảng này, thẻ nào không khớp thì hiển thị `--`. Không làm ngược lại — dựng thẻ từ mảng số đo sẽ khiến cảm biến mới lắp biến mất khỏi Dashboard cho tới lúc có số đo đầu tiên.
>
> **`value` của cảm biến ánh sáng là `350.0` chứ không phải `350`.** Bảng số đo chỉ có một cột giá trị dùng chung cho ba đại lượng nên kiểu là `double precision` (`04-Database.md` §4.3). Frontend làm tròn khi `metric_type = LIGHT`.

**Ghi chú cài đặt.** `DISTINCT ON` là cú pháp riêng của PostgreSQL — `.distinct("sensor_id")` **chỉ chạy trên PostgreSQL**, và bắt buộc `order_by()` phải bắt đầu bằng đúng trường đó. Đường dẫn này là `@action(detail=False, url_path="latest")` của `SensorViewSet`; router đặt route hành động **trước** route chi tiết `/api/sensors/{id}` nên `latest` không bị hiểu nhầm thành một giá trị `id`.

---

### 4.2 `GET /api/sensors/chart` — dữ liệu cho biểu đồ

| Mục | Nội dung |
|---|---|
| **Use case** | UC-01 bước 2, BR-10 |
| **Sequence** | SD-04 |
| **Truy vấn ORM** | Chốt tập **mốc thời gian** trước, rồi lấy mọi số đo thuộc các mốc đó — xem "Ghi chú cài đặt" |
| **Phân trang** | Không — trả mảng thuần |

**Tham số truy vấn**

| Tham số | Kiểu | Mặc định | Ràng buộc |
|---|---|---|---|
| `limit` | int | `20` (BR-10) | 1 → 100 **chu kỳ**; lớn hơn thì tự hạ về 100; sai kiểu → `400` |

**Phản hồi `200 OK`** — mảng **sắp xếp tăng dần theo thời gian**, **một phần tử cho mỗi chu kỳ**:

```json
[
  { "recorded_at": "2026-08-17T10:29:24.113Z", "temperature": 27.6, "humidity": 70.2, "light": 352 },
  { "recorded_at": "2026-08-17T10:29:26.140Z", "temperature": 27.8, "humidity": 70.5, "light": 349 },

  { "recorded_at": "2026-08-17T10:29:54.088Z", "temperature": 28.4, "humidity": null, "light": 352 },

  { "recorded_at": "2026-08-17T10:30:02.451Z", "temperature": 28.5, "humidity": 72.0, "light": 350 }
]
```

*(Rút gọn — trả về đủ 20 phần tử. Bốn phần tử trên là chu kỳ thứ 1, 2, 16 và 20 của cửa sổ `10:29:24Z → 10:30:02Z`.)*

**Khóa của mỗi phần tử là `metric_type` viết thường** — `temperature`, `humidity`, `light` — chứ không phải mã cảm biến. Lý do: Recharts tham chiếu đường vẽ bằng `dataKey` cố định trong mã Frontend, mà `metric_type` là tập giá trị đóng (ba giá trị, ràng buộc `CHECK`), còn mã cảm biến thì đổi theo phòng (`room01_temp` / `room02_temp`).

> **Hình dạng phản hồi giữ nguyên như bản 1.3, dù cấu trúc lưu trữ đã đổi hoàn toàn.** Trong CSDL, cửa sổ 20 chu kỳ này là **60 bản ghi rời**; backend xoay bảng (pivot) chúng thành 20 phần tử trước khi trả về. Nhờ vậy **mã vẽ biểu đồ của Frontend không phải sửa một dòng nào** khi chuyển sang mô hình mới.
>
> **Vì sao backend xoay bảng chứ không để Frontend làm.** Quy ước "chu kỳ nào thiếu số đo thì trường đó là `null`" chỉ nên tồn tại ở **một** chỗ. Để Frontend tự gom 60 bản ghi thành 20 điểm là nhân đôi chỗ phải nhớ quy ước, và mỗi lần thêm điểm mới từ WebSocket lại phải xử lý lần nữa.

> **Chu kỳ thiếu số đo vẫn nằm trong mảng.** Phần tử thứ ba ở trên là chu kỳ `10:29:54Z` — DHT11 đọc lỗi độ ẩm nên **không có bản ghi** cho cảm biến `room01_humi` tại mốc đó (UC-07 A2), và backend điền `null` vào đúng trường khi xoay bảng. Endpoint **không** bỏ cả chu kỳ: biểu đồ cần giữ đúng trục thời gian, và thư viện vẽ sẽ để **đường độ ẩm đứt một đoạn** tại mốc đó, đúng như bản vẽ `docs/wireframe/01-dashboard.html`.

Mảng rỗng `[]` khi chưa có dữ liệu — thư viện vẽ biểu đồ nhận `[]` không lỗi.

> **Hai điểm khác biệt có chủ đích so với các endpoint còn lại.**
>
> **① Thứ tự tăng dần.** Recharts vẽ các điểm theo đúng thứ tự phần tử trong mảng; nhận danh sách giảm dần thì trục thời gian chạy từ phải sang trái. Backend chốt 20 mốc mới nhất bằng truy vấn giảm dần để tận dụng chỉ mục, sau đó sắp lại tăng dần trong Python trước khi tuần tự hóa.
>
> **② Bỏ `id` và mã cảm biến.** Biểu đồ chỉ cần trục thời gian và ba số đo. Hình dạng gọn khiến hợp đồng dữ liệu của biểu đồ rõ ràng: **những gì có trong mảng này chính là những gì vẽ được**.

**Ghi chú cài đặt — không được viết `ORDER BY recorded_at DESC LIMIT 60`.** Cách đó chỉ đúng khi mọi chu kỳ đều đủ ba số đo. Chỉ cần một cảm biến lỗi vài chu kỳ là 60 bản ghi ấy **không phủ đúng 20 mốc**, biểu đồ hụt hoặc thừa điểm ở đầu cửa sổ. Phải chốt tập mốc trước:

```sql
SELECT sd.sensor_id, sd.value, sd.recorded_at
FROM   sensors_sensordata sd
WHERE  sd.recorded_at >= (
           SELECT min(recorded_at) FROM (
               SELECT DISTINCT recorded_at FROM sensors_sensordata
               ORDER BY recorded_at DESC LIMIT 20
           ) t
       )
ORDER  BY sd.recorded_at;
```

Kết quả tối đa `limit × 3` bản ghi, xoay bảng trong Python rồi trả về.

---

### 4.3 `GET /api/sensors` — bảng số liệu cảm biến

| Mục | Nội dung |
|---|---|
| **Use case** | UC-03 (luồng chính), UC-04 (`«extend»`) |
| **Sequence** | SD-06 (`03-Sequence.md` §7) |
| **Truy vấn ORM** | `SensorData.objects.select_related("sensor")` + `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter` |
| **Chỉ mục dùng tới** | `idx_sensordata_recorded_desc`, `sensordata_sensor_time_unique` |

**Tham số truy vấn**

| Tham số | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `page` | int | `1` | Trang cần lấy |
| `page_size` | int | `10` | 1 → 100 (BR-08) |
| `ordering` | string | `-recorded_at` | Nhận: `recorded_at`, `value`, `id` và biến thể có `-` |
| `search` | string | — | Khớp một phần, không phân biệt hoa thường, trên **`sensor__code`** và **`sensor__name`** |
| `sensor` | string | — | Khớp chính xác **mã cảm biến**, ví dụ `room01_temp` |
| `node` | string | — | Khớp chính xác mã bo mạch (`sensor__node_id`) |
| `recorded_at__gte` | datetime | — | Từ thời điểm (kèm múi giờ — §2.4) |
| `recorded_at__lte` | datetime | — | Đến thời điểm |
| `value__gte` | float | — | Giá trị từ … trở lên — **bắt buộc kèm `sensor`** |
| `value__lte` | float | — | Giá trị tới … — **bắt buộc kèm `sensor`** |

**Bộ lọc gọn đi một nửa so với bản 1.3.** Sáu tham số `temperature__gte/lte`, `humidity__gte/lte`, `light__gte/lte` nay gộp thành **hai** — `value__gte` / `value__lte` — vì cột đại lượng đã trở thành khóa ngoại `sensor` thay vì ba cột riêng. Dropdown trên giao diện đổi nhãn từ **"Cột ▾"** sang **"Cảm biến ▾"**, cấu trúc không đổi (`01-SRS.md` §4.1, màn hình 2; UC-04 bước 1b).

Mọi điều kiện nối bằng `AND`:

```
?sensor=room01_temp&value__gte=30&recorded_at__gte=2026-08-17T00:00:00+07:00
```

> **⚠️ `value__gte` / `value__lte` không dùng được một mình.** Thiếu tham số `sensor` thì API trả `400 VALIDATION_ERROR`. Ba cảm biến đo ba đại lượng có **đơn vị khác nhau**, nên điều kiện "giá trị từ 28 đến 30" áp cho cả bảng sẽ gộp *28 °C* với *28 lux* vào cùng một tập kết quả — một con số vô nghĩa. Giao diện phản ánh ràng buộc này bằng cách để hai ô Từ/Đến ở trạng thái vô hiệu cho tới khi người dùng chọn cảm biến (UC-04 E4).
>
> Cùng lý do đó, `ordering=value` **chỉ nên dùng kèm `sensor`**. API không chặn, nhưng sắp xếp giá trị của ba đại lượng lẫn nhau cho ra một danh sách không có ý nghĩa đọc được.

> **Bẫy cũ đã biến mất.** Bản 1.3 có một cảnh báo dài về việc bản ghi `temperature = null` bị loại khỏi kết quả ở **cả hai chiều** so sánh, khiến `count` nhỏ hơn dự kiến mà không có lỗi nào. Từ bản 2.0, cột `value` là `NOT NULL` — cảm biến không đọc được thì **không có dòng** — nên hiện tượng này không còn. Dòng chú thích tương ứng trên giao diện cũng đã được bỏ.

> **Cột `value` không có chỉ mục.** `04-Database.md` §5.2 giải thích đầy đủ: bảng nhận **129.600 lượt ghi/ngày** trong khi lọc theo giá trị là thao tác thủ công vài lần mỗi phiên, lại có độ chọn lọc thấp vì nhiệt độ phòng dao động trong dải hẹp. Điều kiện `sensor` đi kèm đã thu hẹp còn 1/3 số dòng trước khi phải so sánh `value`, nên `Seq Scan` phần còn lại vẫn đạt NFR-03 ở quy mô đồ án. Cách đo lại ở `04-Database.md` §11.2.

> **Vì sao `search` nay khớp được hai cột.** `SearchFilter` của DRF sinh mệnh đề `ILIKE`, chỉ áp dụng cho cột kiểu chuỗi. Bản 1.3 chỉ có đúng một cột chuỗi (`device_id`) nên ô tìm kiếm gần như vô dụng. Nay hai cột chuỗi `sensor.code` và `sensor.name` nằm ở bảng danh mục, truy cập qua `search_fields = ["sensor__code", "sensor__name"]` — gõ `"nhiệt"` hay `"temp"` đều ra đúng tập bản ghi. Ô tìm kiếm trên màn hình Data Sensor vì vậy đã có ngữ nghĩa rõ ràng.

**Phản hồi `200 OK`**

```json
{
  "count": 36134,
  "next": "http://localhost:8000/api/sensors?page=2",
  "previous": null,
  "results": [
    {
      "id": 36132,
      "sensor": { "id": 1, "code": "room01_temp", "name": "Nhiệt độ phòng", "unit": "°C" },
      "value": 28.5,
      "recorded_at": "2026-08-17T10:30:02.451231Z"
    },
    {
      "id": 36133,
      "sensor": { "id": 2, "code": "room01_humi", "name": "Độ ẩm phòng", "unit": "%" },
      "value": 72.0,
      "recorded_at": "2026-08-17T10:30:02.451231Z"
    },
    {
      "id": 36134,
      "sensor": { "id": 3, "code": "room01_lux", "name": "Ánh sáng phòng", "unit": "lux" },
      "value": 350.0,
      "recorded_at": "2026-08-17T10:30:02.451231Z"
    }
  ]
}
```

Phần tử trong `results` dùng đúng serializer của §4.1.

> **Ba phần tử đầu thuộc **cùng một chu kỳ** nên mang cùng `recorded_at`, và hiện theo thứ tự danh mục *Nhiệt độ → Độ ẩm → Ánh sáng* (BR-11). Thứ tự này do `ordering = ["-recorded_at", "sensor_id"]` quyết định — xem ghi chú phân trang bên dưới.

> **⚠️ Một trang 10 bản ghi nay chỉ chứa 3⅓ chu kỳ.** Bản 1.3 thì 10 bản ghi là 10 mốc thời gian (20 giây dữ liệu); nay là khoảng 6 giây. Đây là hệ quả trực tiếp của việc tách một chu kỳ thành ba dòng. `page_size` mặc định giữ 10 theo BR-08, nhưng giao diện nên đặt sẵn một lựa chọn lớn hơn (15 hoặc 30) để một trang chứa được số chu kỳ trọn vẹn — xem §12.

> **⚠️ Thứ tự sắp xếp phải gồm hai cột.** Ba bản ghi cùng chu kỳ có `recorded_at` **giống hệt nhau**. Nếu chỉ `ORDER BY recorded_at DESC`, PostgreSQL được tự do trả về chúng theo thứ tự bất kỳ và thứ tự có thể khác nhau giữa hai lần gọi — hậu quả là khi lật trang, có dòng xuất hiện hai lần còn dòng khác biến mất. Model khai `ordering = ["-recorded_at", "sensor_id"]` để chặn điều này (`04-Database.md` §5.2). **Khi Frontend gửi `ordering` tùy chỉnh, backend vẫn phải nối thêm cột phá hòa** — xem mã ở §7.3.

**Ví dụ gọi**

```bash
# Trang 2, 30 bản ghi/trang (10 chu kỳ)
curl "http://localhost:8000/api/sensors?page=2&page_size=30"

# Nhiệt độ từ 30 °C trở lên trong ngày 17/08/2026 theo giờ Việt Nam
curl -G "http://localhost:8000/api/sensors" \
  --data-urlencode "sensor=room01_temp" \
  --data-urlencode "value__gte=30" \
  --data-urlencode "recorded_at__gte=2026-08-17T00:00:00+07:00" \
  --data-urlencode "recorded_at__lte=2026-08-17T23:59:59+07:00" \
  --data-urlencode "ordering=-value"

# Tìm theo tên cảm biến
curl -G "http://localhost:8000/api/sensors" --data-urlencode "search=độ ẩm"
```

**Lỗi có thể gặp**

| HTTP | `code` | Điều kiện |
|---|---|---|
| `400` | `VALIDATION_ERROR` | `page_size=abc`, `recorded_at__gte` sai định dạng ISO-8601, `value__gte=abc`, **hoặc dùng `value__gte`/`value__lte` mà thiếu `sensor`** |
| `400` | `INVALID_RANGE` | `recorded_at__gte` > `recorded_at__lte`, hoặc `value__gte` > `value__lte` (UC-04 E2) |
| `404` | `PAGE_NOT_FOUND` | `page` vượt quá tổng số trang (UC-03 A2) |

Ví dụ thân phản hồi `400 INVALID_RANGE`:

```json
{
  "error": {
    "code": "INVALID_RANGE",
    "message": "Khoảng lọc không hợp lệ.",
    "details": {
      "value__gte": ["Giá trị đầu khoảng phải nhỏ hơn hoặc bằng giá trị cuối khoảng."]
    }
  }
}
```

Ví dụ thân phản hồi khi thiếu `sensor`:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dữ liệu không hợp lệ.",
    "details": {
      "value__gte": ["Phải chọn một cảm biến trước khi lọc theo khoảng giá trị."]
    }
  }
}
```

> **Cảnh báo hiệu năng khi sắp xếp theo giá trị.** `ordering=-value` chạy trên cột **không có chỉ mục**. PostgreSQL quét rồi lấy top-N. Ở quy mô đồ án (dưới ~1 triệu bản ghi) thao tác này vẫn nằm trong ngưỡng 500 ms của NFR-03; nếu bảng phình lớn hơn thì thêm chỉ mục ghép `(sensor_id, value)` — **không** thêm chỉ mục đơn cột trên `value`. Xem §12 điểm 2.

---

### 4.4 `GET /api/devices` — danh sách thiết bị

| Mục | Nội dung |
|---|---|
| **Use case** | UC-01 bước 5; dùng lại ở SD-05 khi Frontend cần lấy trạng thái thật sau timeout |
| **Sequence** | SD-04, SD-05 |
| **Truy vấn ORM** | `Device.objects.filter(is_active=True)` |
| **Phân trang** | **Không** — trả mảng thuần |

**Phản hồi `200 OK`**

```json
[
  {
    "id": 1,
    "code": "room01_lamp",
    "name": "Đèn phòng",
    "device_type": "LIGHT",
    "node_id": "esp8266_room01",
    "gpio_pin": "D5",
    "current_state": "OFF",
    "updated_at": "2026-08-17T10:15:33.921Z"
  },
  {
    "id": 2,
    "code": "room01_fan",
    "name": "Quạt trần",
    "device_type": "FAN",
    "node_id": "esp8266_room01",
    "gpio_pin": "D6",
    "current_state": "ON",
    "updated_at": "2026-08-17T10:28:07.884Z"
  }
]
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | int | Dùng để dựng URL `/api/devices/{id}/control` |
| `code` | string(30) | Mã nghiệp vụ, trùng với trường `device` của payload MQTT |
| `name` | string(100) | Nhãn hiển thị cạnh công tắc |
| `device_type` | enum | `LIGHT` / `FAN` / `OTHER` — Frontend chọn biểu tượng 💡 / 🌀 theo giá trị này |
| `node_id` | string(50) | Bo mạch có chân điều khiển thiết bị này. Với một phòng thì mọi dòng cùng giá trị; có ý nghĩa khi lắp bo thứ hai |
| `gpio_pin` | string(10) | Chân điều khiển; Frontend không dùng, giữ lại để đối chiếu khi demo phần cứng. **Chỉ duy nhất trong phạm vi một `node_id`** (`04-Database.md` §4.4a) |
| `current_state` | enum | `ON` / `OFF` — **trạng thái vật lý đã xác nhận** (`04-Database.md` §6.2) |
| `updated_at` | datetime | Lần cập nhật trạng thái gần nhất |

Trường `is_active` **không** được trả về: kết quả đã lọc sẵn `is_active = true` nên mọi phần tử đều có cùng giá trị, đưa vào chỉ làm nhiễu.

> **Hai giá trị `updated_at` ở trên không phải số bịa.** Mỗi giá trị bằng đúng `responded_at` của lệnh `SUCCESS` gần nhất của thiết bị đó trong ví dụ §4.6: `room01_lamp` tắt lúc `10:15:33.921Z` (bản ghi `id 84`), `room01_fan` bật lúc `10:28:07.884Z` (bản ghi `id 87`). Đây là hệ quả trực tiếp của quy tắc "chỉ cập nhật `current_state` khi `SUCCESS`" — muốn kiểm tra cài đặt có đúng không thì so hai cột này với nhau.

> **Vì sao không phân trang.** Bảng `devices` cố định 2 dòng, mở rộng lắm cũng vài dòng (FR-16). Bọc trong `{count, next, previous, results}` khiến Frontend phải bóc thêm một lớp cho một mảng không bao giờ dài. **Bẫy cài đặt:** `PAGE_SIZE` khai báo trong `REST_FRAMEWORK` có hiệu lực toàn cục, nên ViewSet này phải đặt tường minh `pagination_class = None`, nếu không kết quả vẫn bị bọc và Frontend nhận `undefined` khi duyệt mảng.

---

### 4.5 `POST /api/devices/{id}/control` — gửi lệnh bật/tắt

Đây là endpoint trọng tâm của đồ án.

| Mục | Nội dung |
|---|---|
| **Use case** | UC-02 (luồng chính, E1→E5) |
| **Sequence** | SD-01 §2, SD-02 §3, SD-05 §6 |
| **Quy tắc nghiệp vụ** | BR-03, BR-04, BR-05, BR-06 |
| **Giao dịch** | Toàn bộ view nằm trong `transaction.atomic()` |

**Tham số đường dẫn**

| Tham số | Kiểu | Mô tả |
|---|---|---|
| `id` | int | Khóa chính của thiết bị. Thiết bị có `is_active = false` được coi như **không tồn tại** |

**Thân yêu cầu**

```json
{ "action": "ON" }
```

| Trường | Kiểu | Bắt buộc | Ràng buộc |
|---|---|---|---|
| `action` | string | ✓ | Thuộc {`ON`, `OFF`}. Chuỗi viết thường (`"on"`) được **tự chuẩn hóa** thành chữ hoa trước khi kiểm tra |

**Header bắt buộc:** `Authorization: Token <token>` (§2.2). Người thao tác ghi vào lịch sử **lấy từ token**, không lấy từ thân yêu cầu.

**Phản hồi `202 Accepted`**

```json
{
  "request_id": "3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
  "device_id": 1,
  "device": "room01_lamp",
  "action": "ON",
  "user": { "id": 1, "full_name": "Lưu Đức Anh" },
  "status": "PENDING",
  "created_at": "2026-08-17T10:31:44.902Z"
}
```

| Trường | Kiểu | Null | Mô tả |
|---|---|---|---|
| `request_id` | uuid | ✗ | Mã ghép cặp lệnh ↔ phản hồi (BR-06). **Frontend phải lưu lại** để đối chiếu với sự kiện `device.state` sắp tới |
| `device_id` | int | ✗ | Khóa chính thiết bị |
| `device` | string | ✗ | Mã `code` — giống hệt trường `device` trong payload MQTT |
| `action` | enum | ✗ | Lệnh đã được tiếp nhận |
| `user` | object | ✗ | Người đã đăng nhập gửi lệnh này, lấy từ token. **Không bao giờ `null`** ở endpoint này |
| `status` | enum | ✗ | Luôn là `PENDING` ở phản hồi này |
| `created_at` | datetime | ✗ | Mốc `T0` để tính timeout 5 giây (BR-03) |

> **Người thao tác lấy từ token, không nhận từ thân yêu cầu** *(đổi ở bản 2.1)*. Bản 2.0 nhận `user_id` do người gọi tự khai, nên ai cũng ghi được tên người khác vào lịch sử. Nay máy chủ dùng `request.user` sau khi xác thực token. Nếu người gọi vẫn gửi kèm `user_id`, trường này bị **bỏ qua im lặng** (serializer của DRF không đọc trường không khai báo), và bản ghi vẫn mang tên chủ token — ca kiểm thử A-11c.
>
> **Cột `user_id` của lịch sử vẫn cho phép `NULL` — BR-12 giữ nguyên.** Mọi lệnh đi qua API đều có người thao tác, nhưng bản ghi **không** đi qua API thì không có: dữ liệu khởi tạo, bản ghi tạo tay qua Django shell hoặc trang admin. Vì vậy `GET /api/actions` vẫn có thể trả `"user": null` và bộ lọc `?user=none` vẫn có ý nghĩa (§4.6).

> **`user` được ghi một lần, không bao giờ đổi.** MQTT worker khi cập nhật bản ghi sang `SUCCESS`/`FAILED` chỉ chạm vào `status`, `responded_at`, `error_message` — dùng `save(update_fields=[...])` để bảo đảm điều đó ở mức mã nguồn (`04-Database.md` §6.3).

> **Vì sao `202` chứ không phải `200`** *(chốt điểm ① của `03-Sequence.md` §10)*. Tại thời điểm phản hồi, lệnh mới chỉ được **ghi vào CSDL và đẩy lên broker** — bóng đèn vẫn chưa sáng. `202 Accepted` mang đúng nghĩa "đã tiếp nhận, kết quả sẽ có sau", còn `200 OK` ngụ ý công việc đã xong. Kết quả thật đi về theo đường WebSocket (§5.3). Nếu view chờ `device_respond` rồi mới trả lời, mỗi lần bấm công tắc sẽ giữ một thread của `daphne` tới 5 giây — chỉ cần vài người bấm cùng lúc là hết thread.

**Bảng lỗi đầy đủ**

| HTTP | `code` | Điều kiện | Có ghi `action_history` không? | Luồng UC |
|---|---|---|---|---|
| `400` | `VALIDATION_ERROR` | Thiếu `action` hoặc giá trị ngoài {`ON`,`OFF`} | Không | E4 |
| `401` | `UNAUTHENTICATED` | Thiếu token, token sai hoặc đã bị thu hồi | Không | BR-13 |
| `404` | `NOT_FOUND` | `id` không tồn tại **hoặc** thiết bị `is_active = false` | Không | E3 |
| `409` | `DEVICE_BUSY` | Thiết bị còn một bản ghi `PENDING` chưa kết thúc | Không | E6, BR-04 |
| `503` | `BROKER_UNAVAILABLE` | Không kết nối hoặc không publish được lên Mosquitto | **Không** — bản ghi `PENDING` bị cuộn ngược | E2 |

Ví dụ thân phản hồi `409`:

```json
{
  "error": {
    "code": "DEVICE_BUSY",
    "message": "Thiết bị đang chờ phản hồi cho lệnh trước đó, vui lòng thử lại sau vài giây.",
    "details": null
  }
}
```

> **`409` là phần máy chủ của BR-04** *(đã đưa vào mô hình nghiệp vụ ở `02-UseCase.md` bản 1.3 — luồng ngoại lệ UC-02 **E6**)*. Lớp bảo vệ ở Frontend **chỉ có tác dụng trong một tab**: kịch bản T-15 mở hai tab, tab thứ hai không hề biết tab thứ nhất vừa gửi lệnh (trạng thái `PENDING` không sinh sự kiện WebSocket nào). Kết quả là hai bản ghi `PENDING` cho cùng một thiết bị, hai message trên `device_control`, và phần cứng nhận hai lệnh liên tiếp. Kiểm tra ở máy chủ là nơi **duy nhất** chặn được tình huống này. Chi phí: một truy vấn `EXISTS` trên chỉ mục bộ phận `idx_action_pending`, vốn chỉ chứa vài dòng (`04-Database.md` §5.2).
>
> Bản ghi `PENDING` luôn tự thoát sau tối đa 6 giây nhờ vòng quét timeout (SD-05), nên `409` không thể khóa thiết bị vĩnh viễn.

> **Vì sao `404` chứ không phải `403`/`409` với thiết bị `is_active = false`.** Thiết bị đã tháo không xuất hiện trong `GET /api/devices`, tức là **không tồn tại dưới góc nhìn của API**. Trả `404` giữ cho tập tài nguyên mà API thừa nhận là nhất quán giữa danh sách và thao tác. Về cài đặt chỉ là một dòng: `get_object_or_404(Device.objects.filter(is_active=True), pk=pk)`.

> **Vì sao `503` không để lại bản ghi.** UC-02 E2 quy định broker hỏng thì không ghi `action_history`, nhưng luồng chính lại ghi `PENDING` **trước** khi publish. Hai điều này chỉ dung hòa được nhờ `transaction.atomic()`: ngoại lệ từ `publish()` làm giao dịch cuộn ngược và bản ghi vừa tạo biến mất (`03-Sequence.md` §2.4). Hệ quả cần biết khi vấn đáp: **dãy `id` của bảng `action_history` sẽ có lỗ hổng** sau mỗi lần cuộn ngược, vì `bigserial` không trả lại số đã cấp. Đây là hành vi bình thường của PostgreSQL, không phải mất dữ liệu.

**Điều gì xảy ra sau khi nhận `202`**

| Thời điểm | Sự kiện | Frontend làm gì |
|---|---|---|
| `T0` | Nhận `202` | Giữ công tắc ở trạng thái khóa, lưu `request_id`, bật bộ đếm dự phòng ~7 giây |
| `T0 + ~0,5s` | Sự kiện `device.state` với `status: "SUCCESS"` | Mở khóa, đặt trạng thái theo `current_state` |
| `T0 + 5→6s` | Sự kiện `device.state` với `status: "FAILED"` | Mở khóa, trả công tắc về trạng thái cũ, hiện "Thiết bị không phản hồi" |
| `T0 + 7s` | Bộ đếm dự phòng hết hạn (WebSocket đứt giữa chừng) | Mở khóa và gọi lại `GET /api/devices` để lấy trạng thái thật |

Độ trễ timeout là **5–6 giây chứ không phải đúng 5**, vì vòng quét chạy mỗi 1 giây (`03-Sequence.md` §6.3).

---

### 4.6 `GET /api/actions` — bảng lịch sử thao tác

| Mục | Nội dung |
|---|---|
| **Use case** | UC-05 (luồng chính), UC-04 (`«extend»`) |
| **Sequence** | SD-06 *(biến thể)* |
| **Truy vấn ORM** | `ActionHistory.objects.select_related("device", "user")` — **bắt buộc**, tránh N+1 (`04-Database.md` §11.1) |
| **Chỉ mục dùng tới** | `idx_action_created_desc`, `idx_action_dev_created`, chỉ mục tự sinh của khóa ngoại `user_id` |

**Tham số truy vấn**

| Tham số | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `page`, `page_size` | int | `1`, `10` | Như §2.8 |
| `ordering` | string | `-created_at` | Nhận: `created_at`, `responded_at`, `status`, `action`, `id` |
| `search` | string | — | Khớp một phần trên `device.name`, `device.code`, `user.full_name`, `error_message` |
| `device` | int | — | Lọc theo khóa chính thiết bị |
| `user` | int | — | Lọc theo khóa chính **người thao tác**. Giá trị đặc biệt `user=none` lọc các bản ghi **không xác định được người thao tác** |
| `status` | enum | — | `PENDING` / `SUCCESS` / `FAILED` |
| `action` | enum | — | `ON` / `OFF` |
| `created_at__gte` | datetime | — | Từ thời điểm |
| `created_at__lte` | datetime | — | Đến thời điểm |

> **Vì sao cần giá trị `user=none` riêng.** Trường `user_id` cho phép `NULL` (BR-12), mà `?user=` bỏ trống bị `DjangoFilterBackend` hiểu là "không lọc" chứ không phải "lọc lấy dòng rỗng". Không có giá trị đặc biệt này thì **không có cách nào** liệt kê các lệnh không rõ ai phát ra — đúng thứ người chấm sẽ thử. Cài đặt là một `ChoiceFilter` với `method` tùy chỉnh gọi `.filter(user__isnull=True)`.

**Phản hồi `200 OK`**

```json
{
  "count": 88,
  "next": "http://localhost:8000/api/actions?page=2",
  "previous": null,
  "results": [
    {
      "id": 88,
      "device": { "id": 1, "code": "room01_lamp", "name": "Đèn phòng" },
      "action": "ON",
      "user": { "id": 1, "full_name": "Lưu Đức Anh" },
      "status": "PENDING",
      "error_message": null,
      "request_id": "3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
      "created_at": "2026-08-17T10:31:44.902Z",
      "responded_at": null,
      "latency_ms": null
    },
    {
      "id": 87,
      "device": { "id": 2, "code": "room01_fan", "name": "Quạt trần" },
      "action": "ON",
      "user": { "id": 1, "full_name": "Lưu Đức Anh" },
      "status": "SUCCESS",
      "error_message": null,
      "request_id": "9d4e5f60-7a8b-4c1d-9e2f-3a4b5c6d7e8f",
      "created_at": "2026-08-17T10:28:07.472Z",
      "responded_at": "2026-08-17T10:28:07.884Z",
      "latency_ms": 412
    },
    {
      "id": 86,
      "device": { "id": 2, "code": "room01_fan", "name": "Quạt trần" },
      "action": "ON",
      "user": { "id": 1, "full_name": "Lưu Đức Anh" },
      "status": "FAILED",
      "error_message": "Timeout: không nhận được device_respond trong 5 giây",
      "request_id": "b7c1d2e3-1122-4a5b-9c8d-77e6f5a4b3c2",
      "created_at": "2026-08-17T10:20:02.117Z",
      "responded_at": "2026-08-17T10:20:07.640Z",
      "latency_ms": 5523
    }
  ]
}
```

> **Ba bản ghi trên là một mạch chuyện, cố ý dùng lại ở mọi tài liệu và bản vẽ.** Lệnh `id 86` bật quạt bị hết giờ (BR-03) nên `current_state` của `room01_fan` không đổi; người dùng bấm lại, `id 87` thành công lúc `10:28:07.884Z` — đúng giá trị `updated_at` của `room01_fan` ở ví dụ §4.4, vì cột này chỉ đổi khi lệnh `SUCCESS`. `id 88` chính là lệnh sinh ra phản hồi `202` ở §4.5 (cùng `request_id`) và tại thời điểm chụp vẫn còn `PENDING`, nên `responded_at` và `latency_ms` đều là `null`. Ba dòng này khớp ba dòng đầu của bản vẽ `docs/wireframe/03-action-history.html`.

| Trường | Kiểu | Null | Mô tả |
|---|---|---|---|
| `device` | object | ✗ | Lồng 3 trường; Frontend hiển thị `device.code · device.name` ở cột "Thiết bị" |
| `action` | enum | ✗ | Lệnh đã yêu cầu |
| `user` | object | **✓** | Người thao tác (BR-12, FR-18). **`null`** khi lệnh không xác định được người phát ra — giao diện hiển thị `—` |
| `status` | enum | ✗ | Frontend tô màu: `SUCCESS` xanh · `FAILED` đỏ · `PENDING` vàng (UC-05 bước 4) |
| `error_message` | string(255) | ✓ | `null` khi không có lỗi |
| `request_id` | uuid | ✗ | Phục vụ đối chiếu khi gỡ lỗi cùng log của MQTT worker |
| `created_at` | datetime | ✗ | Lúc ghi `PENDING` |
| `responded_at` | datetime | ✓ | Thời điểm lệnh **kết thúc** — nhận `device_respond`, hoặc lúc bị đánh hết giờ. `null` khi còn `PENDING` (`04-Database.md` §4.3) |
| `latency_ms` | int | ✓ | Suy ra từ `responded_at - created_at`, **không lưu thành cột**. Với lệnh hết giờ, giá trị luôn rơi vào dải 5.000–6.000 ms — nó đo *thời gian chờ đã bỏ ra*, không phải thời gian phần cứng phản hồi |

> **⚠️ `user` có thể là `null` — Frontend phải xử lý.** Đây là trường duy nhất trong toàn bộ API mà một **đối tượng lồng** có thể rỗng. Truy cập thẳng `row.user.full_name` sẽ ném lỗi ở đúng những dòng do `mosquitto_pub` sinh ra — thứ chắc chắn có mặt trong dữ liệu demo tuần 2. Giao diện hiển thị `—`, **không** ghi "Hệ thống" hay "Ẩn danh": hai chữ đó gợi ý rằng tồn tại một tài khoản mang tên như vậy, trong khi sự thật là *không biết ai*.

> **Vì sao `device` là đối tượng lồng chứ không phải `device_name` phẳng.** Bảng lịch sử hiển thị tên thiết bị, nhưng khi bấm vào một dòng để lọc theo thiết bị đó thì Frontend lại cần `id`, và khi đối chiếu với log MQTT thì cần `code`. Gửi cả ba trong một đối tượng lồng thì `select_related` vốn đã nạp sẵn dữ liệu, không tốn thêm truy vấn nào.

> **Màn hình này không dùng WebSocket.** Bảng lịch sử là ảnh chụp tại một thời điểm; tự chèn dòng mới sẽ đẩy dòng người dùng đang đọc trôi xuống (`03-Sequence.md` §7.3). Ngoại lệ duy nhất là UC-05 A2: nếu trang đang hiển thị một bản ghi `PENDING`, Frontend có thể cập nhật riêng dòng đó khi nhận sự kiện `device.state` có `request_id` trùng — không tải lại cả bảng.

**Ví dụ gọi**

```bash
# Các lệnh thất bại của thiết bị số 1
curl "http://localhost:8000/api/actions?device=1&status=FAILED"

# Tìm theo tên thiết bị
curl -G "http://localhost:8000/api/actions" --data-urlencode "search=Quạt"

# Các lệnh do người dùng số 1 thực hiện
curl "http://localhost:8000/api/actions?user=1"

# Các lệnh không xác định được người thao tác
curl "http://localhost:8000/api/actions?user=none"
```

---

### 4.7 `GET /api/profile` — thông tin bàn giao

| Mục | Nội dung |
|---|---|
| **Use case** | UC-06 |
| **Sequence** | Không có — chỉ một lời gọi, không có tương tác nhiều bước (`03-Sequence.md` §9) |
| **Nguồn dữ liệu** | Biến môi trường trong `.env`, **không có bảng CSDL** (`04-Database.md` §1.3) |

**Phản hồi `200 OK`**

```json
{
  "student": {
    "full_name": "Lưu Đức Anh",
    "student_id": "B23DCAT011",
    "class_name": "D23CQAT01-B",
    "email": "ducanhyeutoan@gmail.com",
    "avatar_url": "/static/img/avatar.jpg"
  },
  "project": {
    "title": "Hệ thống giám sát và điều khiển môi trường phòng dựa trên IoT",
    "subject": "IoT & Ứng dụng",
    "supervisor": "TS. Nguyễn Quốc Uy"
  },
  "links": {
    "github": "https://github.com/<tài-khoản>/<kho-mã-nguồn>",
    "report_pdf": "https://…/BaoCao.pdf",
    "figma": "https://www.figma.com/file/…",
    "api_docs": "http://localhost:8000/api/schema/swagger-ui/"
  }
}
```

**Quy tắc với liên kết chưa có.** Biến môi trường để trống thì API trả về `null` (không trả chuỗi rỗng). Frontend hiển thị nút ở trạng thái vô hiệu kèm chú thích "Đang cập nhật" — đúng luồng ngoại lệ UC-06 E1. Phân biệt `null` và `""` giúp Frontend không phải đoán ý nghĩa của chuỗi rỗng.

Biến môi trường tương ứng trong `.env`:

```ini
PROFILE_FULL_NAME=Lưu Đức Anh
PROFILE_STUDENT_ID=B23DCAT011
PROFILE_CLASS=D23CQAT01-B
PROFILE_EMAIL=ducanhyeutoan@gmail.com
PROFILE_AVATAR_URL=/static/img/avatar.jpg
PROJECT_TITLE=Hệ thống giám sát và điều khiển môi trường phòng dựa trên IoT
PROJECT_SUBJECT=IoT & Ứng dụng
PROJECT_SUPERVISOR=TS. Nguyễn Quốc Uy
LINK_GITHUB=
LINK_REPORT_PDF=
LINK_FIGMA=
LINK_API_DOCS=http://localhost:8000/api/schema/swagger-ui/
```

> **Học vị của giảng viên nằm ngay trong chuỗi `supervisor`** (`"TS. Nguyễn Quốc Uy"`), không tách thành trường riêng và cũng không để Frontend tự ghép tiền tố — đúng yêu cầu "nội dung lấy từ cấu hình, không hard-code trong mã Frontend" của UC-06. Muốn đổi học vị thì sửa `.env`, không phải sửa mã.

> Học vị giảng viên `TS.` đã được xác nhận; riêng lớp `D23CQAT01-B` **chưa được xác nhận** — xem §12 điểm 5.

---

### 4.8 `POST /api/auth/login` — đăng nhập

| Mục | Nội dung |
|---|---|
| **Use case** | UC-08 *(chưa có trong `02-UseCase.md` — §12 điểm 7)* |
| **Xác thực** | **Không cần** — endpoint duy nhất như vậy, ngoài ba đường dẫn tài liệu ở §3.3 |
| **Bảng CSDL** | `users_user` (kiểm tra mật khẩu), `authtoken_token` (tạo hoặc lấy token) |

**Thân yêu cầu**

```json
{ "username": "admin", "password": "<mật khẩu>" }
```

| Trường | Kiểu | Bắt buộc | Ràng buộc |
|---|---|---|---|
| `username` | string | ✓ | Phân biệt chữ hoa, chữ thường (mặc định của Django) |
| `password` | string | ✓ | **Không** cắt khoảng trắng ở đầu và cuối |

**Phản hồi `200 OK`**

```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user": { "id": 1, "username": "admin", "full_name": "Lưu Đức Anh", "role": "ADMIN" }
}
```

| Trường | Kiểu | Null | Mô tả |
|---|---|---|---|
| `token` | string | ✗ | 40 ký tự hex. Frontend lưu lại và gửi kèm mọi request sau (§2.2) |
| `user` | object | ✗ | Hiển thị ở sidebar. Có thêm `username` và `role` so với đối tượng `user` rút gọn ở §4.5, §4.6 |

**Bảng lỗi**

| HTTP | `code` | Điều kiện |
|---|---|---|
| `400` | `VALIDATION_ERROR` | Thiếu `username` hoặc `password` |
| `400` | `INVALID_CREDENTIALS` | Sai tên đăng nhập hoặc mật khẩu, hoặc tài khoản `is_active = false` |

> **Đăng nhập nhiều lần trả về cùng một token.** Bảng `authtoken_token` liên kết **một–một** với người dùng, nên đăng nhập ở tab thứ hai hay máy thứ hai không sinh token mới. Hệ quả: **đăng xuất ở một nơi thì mọi nơi đều mất đăng nhập** (§4.9). Chấp nhận ở phạm vi đồ án (§11.2).
>
> **Frontend không gửi header `Authorization` với request này**, kể cả khi còn giữ token cũ. Máy chủ vốn bỏ qua header ở riêng endpoint này (§7.7), nhưng không gửi thì tab Network đọc dễ hiểu hơn.

### 4.9 `POST /api/auth/logout` — đăng xuất

| Mục | Nội dung |
|---|---|
| **Use case** | UC-08 |
| **Xác thực** | Bắt buộc |
| **Thân yêu cầu** | Không có |

**Phản hồi `204 No Content`** — không có thân. Token vừa dùng bị **xoá khỏi CSDL**; gọi lại bằng chính token đó nhận `401` (ca kiểm thử A-22).

| HTTP | `code` | Điều kiện |
|---|---|---|
| `401` | `UNAUTHENTICATED` | Thiếu token, token sai hoặc đã bị thu hồi |

> **Frontend xoá token trong `localStorage` và về trang đăng nhập kể cả khi lời gọi này thất bại** (mất mạng, `401`). Người dùng bấm "Đăng xuất" thì giao diện phải phản hồi ngay; trường hợp lời gọi lỗi, token chỉ chưa bị thu hồi phía máy chủ, còn trình duyệt đã không giữ nó nữa.

---

## 5. GIAO DIỆN WEBSOCKET

### 5.1 Kết nối

| Mục | Giá trị |
|---|---|
| **Đường dẫn** | `ws://<host>:8000/ws/realtime/?token=<token>` *(có dấu gạch chéo trước `?`)* |
| **Nhóm channel layer** | `realtime` — **một nhóm duy nhất cho toàn hệ thống** |
| **Xác thực** | Token qua tham số `?token=` (§2.2). Thiếu hoặc sai → máy chủ **nhận kết nối rồi đóng ngay với mã `4401`** |
| **Chiều dữ liệu** | **Một chiều**: chỉ máy chủ → trình duyệt |
| **Định dạng** | JSON, mỗi message là một sự kiện độc lập |
| **Consumer** | `AsyncJsonWebsocketConsumer` trong `apps/realtime/consumers.py` |

**Máy chủ không gửi gì khi vừa kết nối.** Trạng thái ban đầu do ba lời gọi HTTP của SD-04 dựng lên; WebSocket chỉ lo phần **thay đổi tiếp theo**. Nhờ vậy hợp đồng giữ đúng **hai** loại sự kiện, không phát sinh loại thứ ba kiểu `connection.ack`.

**Message do trình duyệt gửi lên sẽ bị bỏ qua** (chỉ ghi log). Không có thao tác nghiệp vụ nào đi theo chiều này — điều khiển thiết bị dùng HTTP `POST` để còn nhận được mã lỗi 400/404/409/503 (§4.5), thứ mà WebSocket không có sẵn cơ chế biểu diễn.

> **Vì sao token đi trên URL chứ không phải header.** API `WebSocket` của trình duyệt **không cho đặt header** tùy ý. Hai cách còn lại là cookie (quay về vấn đề CSRF và khác origin ở §2.2) hoặc tham số trên URL. Cái giá: token xuất hiện trong log truy cập của `daphne`. Chấp nhận ở phạm vi LAN.
>
> ⚠️ **Phải `accept()` rồi mới `close(code=4401)`, không được đóng trước khi nhận.** Đóng trước `accept()` thì Channels từ chối bắt tay bằng HTTP `403`, và trình duyệt chỉ thấy mã đóng **`1006`** chung chung. Frontend khi đó không phân biệt được *"sai token"* với *"máy chủ tắt"*, nên cứ thử kết nối lại mỗi 5 giây mãi mãi (§5.4 quy tắc 2). Mã `4401` thuộc dải `4000–4999` dành cho ứng dụng tự định nghĩa; chọn giống `401` cho dễ nhớ.

> **Vì sao chỉ một nhóm `realtime`** *(chốt điểm ⑤ của `03-Sequence.md` §10)*. Hệ thống giám sát đúng một phòng, mọi client đều quan tâm mọi sự kiện. Chia nhóm theo thiết bị sẽ khiến worker phải gửi tới N nhóm cho mỗi sự kiện mà không giảm được lưu lượng nào. Khi lắp phòng thứ hai thì tách thành `room_<id>` và thêm tham số vào đường dẫn — xem `04-Database.md` §12.2.

### 5.2 Sự kiện `sensor.data`

Phát bởi **P2 (MQTT worker)** sau mỗi lần ghi thành công một bản ghi cảm biến (SD-03 bước 8). Tần suất: 2 giây/lần (BR-01).

```json
{
  "type": "sensor.data",
  "device_id": "esp8266_room01",
  "temperature": 28.5,
  "humidity": 72.0,
  "light": 350,
  "recorded_at": "2026-08-17T10:30:02.451231Z"
}
```

| Trường | Kiểu | Null | Ghi chú |
|---|---|---|---|
| `type` | string | ✗ | Luôn là `sensor.data` |
| `device_id` | string | ✗ | Mã node cảm biến (`sensor.node_id`) |
| `temperature`, `humidity` | float | ✓ | `null` khi cảm biến đó không đọc được ở chu kỳ này (UC-07 A2) |
| `light` | float | ✓ | lux |
| `recorded_at` | datetime | ✗ | Giống hệt giá trị đã ghi vào CSDL — **chung cho cả ba số đo của chu kỳ** (BR-11) |

> **Hợp đồng của sự kiện này giữ nguyên ở bản 2.0, dù cấu trúc lưu trữ đã đổi hoàn toàn.** Một chu kỳ nay sinh ra **ba bản ghi** trong CSDL, nhưng vẫn chỉ phát **một** sự kiện WebSocket — vì một chu kỳ là một lần cập nhật của Dashboard. Worker gom ba số đo vừa ghi thành gói phẳng này trước khi `group_send`. Nhờ vậy **mã realtime của Frontend không phải sửa một dòng nào**.
>
> Khóa trong gói là `metric_type` viết thường (`temperature` / `humidity` / `light`), giống `dataKey` của biểu đồ ở §4.2 — không phải mã cảm biến, vì mã đổi theo phòng còn `metric_type` là tập giá trị đóng.
>
> **Cảm biến không đọc được thì trường tương ứng là `null`**, không phải vắng khóa. Frontend nhờ vậy luôn nhận đúng ba khóa và chỉ cần một phép kiểm `null` khi thêm điểm vào biểu đồ.

**Frontend xử lý:** cập nhật 3 thẻ số liệu, thêm một điểm vào biểu đồ và **loại bỏ điểm cũ nhất nếu vượt quá 20** (BR-10), đồng thời đặt lại bộ đếm 30 giây của BR-07.

### 5.3 Sự kiện `device.state`

Phát bởi **P2** khi một lệnh điều khiển kết thúc — thành công (SD-02) hoặc thất bại vì hết giờ (SD-05).

```json
{
  "type": "device.state",
  "device_id": 1,
  "device": "room01_lamp",
  "current_state": "ON",
  "request_id": "3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
  "status": "SUCCESS",
  "error_message": null
}
```

| Trường | Kiểu | Null | Ghi chú |
|---|---|---|---|
| `type` | string | ✗ | Luôn là `device.state` |
| `device_id` | int | ✗ | Khóa chính — Frontend dùng để tìm đúng công tắc |
| `device` | string | ✗ | Mã `code` — dùng khi đối chiếu với log MQTT |
| `current_state` | enum | ✗ | Trạng thái **sau** khi xử lý. Ở nhánh `FAILED` là **giá trị cũ, không đổi** |
| `request_id` | uuid | ✗ | So khớp với `request_id` nhận được từ `202` (§4.5) |
| `status` | enum | ✗ | `SUCCESS` hoặc `FAILED` — không bao giờ là `PENDING` |
| `error_message` | string | ✓ | Có nội dung khi `FAILED`, `null` khi `SUCCESS` |

Ví dụ sự kiện timeout:

```json
{
  "type": "device.state",
  "device_id": 2,
  "device": "room01_fan",
  "current_state": "OFF",
  "request_id": "b7c1d2e3-1122-4a5b-9c8d-77e6f5a4b3c2",
  "status": "FAILED",
  "error_message": "Timeout: không nhận được device_respond trong 5 giây"
}
```

> **Vì sao gửi cả `device_id` lẫn `device`** *(chốt điểm ③ của `03-Sequence.md` §10)*. Frontend dựng danh sách công tắc từ `GET /api/devices`, trong đó khóa của mỗi phần tử là `id` (số) — nên cần `device_id` để tìm đúng công tắc mà không phải xây bảng tra `code → id`. Còn `code` là thứ xuất hiện trong log của Mosquitto và trong Serial Monitor của ESP8266, nên giữ lại giúp việc gỡ lỗi ba tầng (firmware ↔ broker ↔ web) đối chiếu được với nhau. Hai trường cộng lại chưa tới 30 byte.

> **Vì sao timeout không có sự kiện riêng.** Dùng lại `device.state` với `status: "FAILED"` giữ đúng hợp đồng hai sự kiện đã công bố ở `01-SRS.md` §4.4, và quan trọng hơn: Frontend chỉ cần **một** hàm xử lý cho mọi kết cục của một lệnh — so khớp `request_id`, mở khóa công tắc, đặt trạng thái theo `current_state`, hiển thị `error_message` nếu có.

### 5.4 Quy tắc phía Frontend

| # | Quy tắc | Nguồn |
|---|---|---|
| 1 | Mở WebSocket **sau khi** ba lời gọi HTTP ban đầu hoàn tất | SD-04 |
| 2 | Đứt kết nối → thử lại mỗi 5 giây; kết nối lại thành công thì gọi lại `GET /api/sensors/latest` để bù khoảng trống | UC-01 E1 |
| 3 | Quá 30 giây không có `sensor.data` → hiện nhãn "Thiết bị ngoại tuyến", làm mờ số liệu cũ | BR-07 |
| 4 | Bỏ qua sự kiện có `request_id` không khớp lệnh nào đang chờ (có thể do tab khác gửi) — nhưng **vẫn cập nhật** `current_state` của thiết bị | UC-02 A2 |
| 5 | Bộ đếm dự phòng ~7 giây cho mỗi lệnh, phòng trường hợp WebSocket đứt đúng lúc lệnh đang chạy | SD-05 §6.3 |
| 6 | Kết nối bị đóng với mã `4401` → **không** thử kết nối lại theo quy tắc 2; xoá token và chuyển về trang đăng nhập | §5.1, BR-13 |
| 7 | Mọi request REST nhận `401` → xoá token, chuyển về trang đăng nhập; đăng nhập lại xong thì quay về đúng trang đang xem | §2.2, BR-13 |

### 5.5 Ba bẫy khi cài đặt Channels

| # | Bẫy | Cách tránh |
|---|---|---|
| 1 | **`type` vừa là khóa định tuyến vừa là trường dữ liệu.** Channels lấy `type` trong dict `group_send` để chọn phương thức của consumer, đổi dấu chấm thành gạch dưới: `"sensor.data"` → `async def sensor_data(self, event)`. Chính dict đó cũng được đẩy thẳng ra trình duyệt | Đổi tên sự kiện thì phải đổi **cả hai chỗ**. Đây là lý do tên sự kiện có dấu chấm chứ không phải gạch dưới |
| 2 | **Worker chạy đồng bộ, `group_send` là hàm bất đồng bộ** | Bọc bằng `async_to_sync(channel_layer.group_send)(...)` trong `mqtt_worker` |
| 3 | **`InMemoryChannelLayer` không báo lỗi khi dùng sai.** Worker gọi `group_send` thành công, nhưng không client nào nhận được gì vì hai tiến trình ở hai vùng nhớ khác nhau | Bắt buộc dùng `channels_redis` (`01-SRS.md` §2.2.1). Triệu chứng đặc trưng: HTTP chạy tốt, WebSocket kết nối được, nhưng **không bao giờ có message nào tới** |

---

## 6. GIAO DIỆN MQTT

Đây là giao diện giữa Backend và firmware. Ba topic đã chốt từ `01-SRS.md` §4.3, tài liệu này bổ sung kiểu dữ liệu, tính bắt buộc và cách xử lý khi sai.

### 6.1 Cấu hình chung

| Tham số | Giá trị |
|---|---|
| Host / Port | `localhost` (hoặc IP LAN) `:1883` |
| Xác thực | username / password, **tắt anonymous** (NFR-09) |
| Client ID | `esp8266_room01` (thiết bị) · `backend_worker` (P2) · `backend_api_<ngẫu nhiên>` (P1) |
| Giữ lại message (retain) | **Không** dùng ở cả ba topic |

> **Vì sao P1 dùng client ID ngẫu nhiên.** Broker ngắt kết nối cũ khi có client mới trùng ID. P1 tạo một client paho ngắn hạn cho **mỗi lần** gọi API; nếu để ID cố định thì hai lệnh bấm gần nhau sẽ tự đá nhau ra khỏi broker.

> **Vì sao không dùng retain.** Message `retain` được broker gửi lại cho mọi client vừa subscribe. Với `device_control`, ESP8266 khởi động lại sẽ nhận ngay lệnh cũ và tự bật đèn — một hành vi bất ngờ với người dùng. Với `data_sensors`, số liệu cũ vài phút không có giá trị hiển thị.

### 6.2 Topic `data_sensors` — ESP8266 → Backend (P2)

| Mục | Giá trị |
|---|---|
| Hướng | Thiết bị publish · P2 subscribe |
| QoS | **0** |
| Tần suất | 2 giây/lần (BR-01) |

```json
{
  "device_id": "esp8266_room01",
  "temperature": 28.5,
  "humidity": 72.0,
  "light": 350,
  "timestamp": "2026-08-17T10:30:02Z"
}
```

> **Payload không đổi ở bản 2.0.** Firmware vẫn gửi **một message chứa cả ba số đo**; việc tách thành ba bản ghi là của Backend. Cho ESP publish ba message riêng sẽ nhân ba lưu lượng WiFi **và** khiến ba số đo tới ở ba thời điểm khác nhau — vi phạm BR-11, làm biểu đồ không xoay bảng được (`04-Database.md` §7.1).

| Trường | Kiểu | Bắt buộc | Xử lý ở Backend |
|---|---|---|---|
| `device_id` | string | Không | Thiếu thì dùng mặc định `esp8266_room01`. Dùng để tra cảm biến theo cặp *(`node_id`, đại lượng)* |
| `temperature` | float | Không | Ánh xạ tới cảm biến có `metric_type = TEMPERATURE` cùng node. Ngoài ngưỡng của **chính cảm biến đó** → **loại bỏ đúng số đo này**, ghi log (UC-07 E3) |
| `humidity` | float | Không | `metric_type = HUMIDITY` — như trên |
| `light` | float | Không | `metric_type = LIGHT` — như trên |
| `timestamp` | string | Không | **Bỏ qua hoàn toàn** — `recorded_at` do backend sinh (`04-Database.md` §2.1) |

Cả ba số đo đều không bắt buộc để hỗ trợ UC-07 A2 (chỉ đọc được một phần cảm biến). Trường vắng mặt hoặc `null` thì **không ghi bản ghi nào** cho cảm biến tương ứng — khác với bản 1.3, khi đó ghi một dòng có cột `NULL`.

**Ngưỡng hợp lệ nay là dữ liệu, không phải hằng số.** Worker đọc `min_value` / `max_value` từ danh mục cảm biến chứ không ghi cứng `−10→60` trong mã. Danh mục được nạp vào bộ nhớ **một lần lúc worker khởi động**, khóa theo cặp `(node_id, metric_type)` — nhờ ràng buộc `UNIQUE (node_id, metric_type)` nên khóa này là duy nhất. Hệ quả vận hành: **sửa ngưỡng hoặc thêm cảm biến phải khởi động lại `mqtt_worker`**.

**Trường không khớp cảm biến nào** (ví dụ firmware gửi thêm `pressure` khi danh mục chưa có) → bỏ qua, ghi log một lần, các trường còn lại xử lý bình thường (UC-07 E5).

**Xử lý message hỏng:** JSON sai cú pháp → ghi log, bỏ qua, **worker không được dừng** (NFR-16, UC-07 E4).

**QoS 0 là có chủ đích:** mất một mẫu trong 43.200 mẫu mỗi ngày không ai nhận ra, trong khi bắt tay `PUBACK` của QoS 1 tốn thêm một vòng truyền cho mỗi mẫu. *(43.200 là số **message**; mỗi message sinh 3 bản ghi nên CSDL nhận 129.600 dòng/ngày.)*

### 6.3 Topic `device_control` — Backend (P1) → ESP8266

| Mục | Giá trị |
|---|---|
| Hướng | P1 publish · Thiết bị subscribe |
| QoS | **1** — mất một lệnh điều khiển là người dùng thấy hệ thống hỏng |

```json
{
  "request_id": "3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
  "device": "room01_lamp",
  "action": "ON"
}
```

| Trường | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `request_id` | string(36) | ✓ | UUID dạng chuỗi. Firmware **phải trả lại nguyên vẹn** trong `device_respond` |
| `device` | string | ✓ | Mã `code`, **không** phải `id` số (`04-Database.md` §7.2) |
| `action` | enum | ✓ | `ON` → `digitalWrite(pin, HIGH)`; `OFF` → `LOW` |

> **Lưu ý cho firmware.** `request_id` là chuỗi UUID **36 ký tự**, không phải mã ngắn — firmware phải cấp đủ bộ đệm cho nó. Toàn bộ payload khoảng 110 byte, trong khi `arduino-mqtt` mặc định chỉ cấp **128 byte** cho mỗi chiều đọc/ghi. Phải khai báo tường minh `MQTTClient client(256);` chứ đừng để mặc định — sát nút như vậy chỉ cần đổi tên thiết bị dài thêm vài ký tự là tràn. Nếu tuần 2 đo thấy chật bộ nhớ thì rút gọn `request_id` còn 8 ký tự đầu và đổi kiểu cột — phương án này đã ghi ở `04-Database.md` §14 điểm 1.

**Firmware phải bỏ qua message có `device` không nằm trong bảng ánh xạ chân của nó** và ghi log ra Serial Monitor, thay vì mặc định điều khiển chân đầu tiên.

### 6.4 Topic `device_respond` — ESP8266 → Backend (P2)

| Mục | Giá trị |
|---|---|
| Hướng | Thiết bị publish · P2 subscribe |
| QoS | **1** |
| Thời hạn | Phải về trong **5 giây** kể từ `created_at`, nếu không lệnh bị đánh `FAILED` (BR-03) |

```json
{
  "request_id": "3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
  "device": "room01_lamp",
  "state": "ON",
  "status": "SUCCESS"
}
```

| Trường | Kiểu | Bắt buộc | Xử lý ở Backend |
|---|---|---|---|
| `request_id` | string(36) | ✓ | Tra cứu bản ghi `PENDING`. Không tìm thấy → bỏ qua, ghi log (UC-02 E5) |
| `device` | string | ✓ | Đối chiếu với `device.code` của bản ghi; lệch → ghi log cảnh báo |
| `state` | enum | ✓ | Trạng thái vật lý sau khi thực thi. Lệch với `action` → ghi log, **không lưu thành cột** (`04-Database.md` §4.3) |
| `status` | enum | ✓ | `SUCCESS` → cập nhật bản ghi; giá trị khác → đánh `FAILED` kèm `error_message` |

**Chống xử lý trùng.** QoS 1 cho phép broker gửi lại message. Truy vấn `select_for_update().get(request_id=…, status="PENDING")` khiến lần gửi thứ hai ném `DoesNotExist` và bị bỏ qua — cùng một cơ chế xử lý phản hồi đến muộn (`04-Database.md` §5.3).

### 6.5 Bảng đối chiếu ba giao diện

Cùng một khái niệm, ba cách gọi tên ở ba tầng — bảng này để tra chéo khi gỡ lỗi:

| Khái niệm | REST | WebSocket | MQTT | Cột CSDL |
|---|---|---|---|---|
| Khóa chính thiết bị | `id` | `device_id` | *(không gửi)* | `devices_device.id` |
| Mã nghiệp vụ thiết bị | `code` | `device` | `device` | `devices_device.code` |
| Lệnh yêu cầu | `action` | *(không gửi)* | `action` | `devices_actionhistory.action` |
| Trạng thái vật lý | `current_state` | `current_state` | `state` | `devices_device.current_state` |
| Kết quả thực thi | `status` | `status` | `status` | `devices_actionhistory.status` |
| Mã ghép cặp | `request_id` | `request_id` | `request_id` | `devices_actionhistory.request_id` |
| Mã node cảm biến | `device_id` | `device_id` | `device_id` | `sensors_sensordata.device_id` |

> Hai dòng cuối cùng của cột REST đều mang tên `device_id` nhưng **khác kiểu và khác ý nghĩa**: ở `device.state` là số nguyên (thiết bị chấp hành), ở `sensor.data` là chuỗi (node cảm biến). Đây là hệ quả của việc hai khái niệm cùng mang chữ "device" đã phân tích ở `04-Database.md` §2.2. Sự trùng tên này không gây lỗi vì hai trường không bao giờ xuất hiện trong cùng một message, nhưng cần biết khi đọc log.

---

## 7. GỢI Ý CÀI ĐẶT (TUẦN 3)

Phần này để copy khi bắt đầu viết mã, không phải đặc tả bắt buộc.

### 7.1 Cấu hình `settings.py`

```python
REST_FRAMEWORK = {
    # §2.2 — CHỈ TokenAuthentication. Thêm SessionAuthentication đứng đầu thì
    # request thiếu token nhận 403 thay vì 401, Frontend không về trang đăng nhập.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",      # BR-13
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,                                    # BR-08
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",   # §7.5
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "IoT Room Monitoring API",
    "DESCRIPTION": "Hệ thống giám sát và điều khiển môi trường phòng dựa trên IoT",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

TIME_ZONE = "UTC"          # §2.4 — bắt buộc, đừng đổi sang Asia/Ho_Chi_Minh
USE_TZ = True

# ⚠️ BẮT BUỘC có TRƯỚC lần `migrate` đầu tiên (`04-Database.md` §2.5).
# Khai sau khi đã migrate thì cách sửa duy nhất là DROP DATABASE rồi làm lại.
AUTH_USER_MODEL = "users.User"

INSTALLED_APPS = [
    # … các app có sẵn …
    "rest_framework",
    "rest_framework.authtoken",     # §2.2 — sinh bảng authtoken_token khi migrate
]

CORS_ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
```

> `rest_framework.authtoken` tạo thêm bảng **`authtoken_token`** (mỗi người dùng một token). Đây là bảng có sẵn của DRF, cùng loại với `auth_group` hay `django_session`, nên **không** tính vào 5 bảng nghiệp vụ của `04-Database.md`.

`PageNumberPagination` mặc định **không** đọc tham số `page_size`. Phải khai báo lớp con:

```python
# config/pagination.py
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 10                  # BR-08
    page_size_query_param = "page_size"
    max_page_size = 100             # UC-04 E3 — tự hạ về 100, không báo lỗi
```

### 7.2 Định tuyến `config/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.sensors.views import SensorViewSet
from apps.devices.views import DeviceViewSet, ActionHistoryViewSet
from apps.core.views import ProfileView
from apps.users.views import LoginView, LogoutView

router = DefaultRouter(trailing_slash=False)        # §2.5 — bắt buộc
router.register("sensors", SensorViewSet, basename="sensors")
router.register("devices", DeviceViewSet, basename="devices")
router.register("actions", ActionHistoryViewSet, basename="actions")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/profile", ProfileView.as_view()),
    path("api/auth/login", LoginView.as_view()),     # §4.8
    path("api/auth/logout", LogoutView.as_view()),   # §4.9
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/",
         SpectacularSwaggerView.as_view(url_name="schema")),
]
```

Mười endpoint chính gói gọn trong **3 ViewSet + 3 APIView**: `devices`, `latest` và `chart` là `@action(detail=False)` của `SensorViewSet`, `control` là `@action(detail=True, methods=["post"])` của `DeviceViewSet`; `LoginView`, `LogoutView` ở §7.7.

> ⚠️ **Đường dẫn `/api/sensors/devices` không xung đột với `/api/devices`.** Hai thứ khác nhau hoàn toàn: cái đầu là **danh mục cảm biến**, cái sau là **thiết bị chấp hành**. Đặt tên như vậy vì cả hai đều nằm dưới không gian tên của tài nguyên tương ứng. Nếu thấy dễ nhầm khi trình bày Swagger, có thể đổi `url_path="catalog"` — nhưng phải sửa đồng thời ở Frontend và §3.1.

### 7.3 Bộ lọc của `/api/sensors`

```python
# apps/sensors/filters.py
from django import forms
from django_filters import rest_framework as filters

from .models import SensorData


class RangeConsistencyForm(forms.Form):
    """Chặn trường hợp đầu khoảng lớn hơn cuối khoảng (UC-04 E2)."""

    PAIRS = [
        ("recorded_at__gte", "recorded_at__lte"),
        ("value__gte", "value__lte"),
    ]

    def clean(self):
        cleaned = super().clean()
        for low, high in self.PAIRS:
            a, b = cleaned.get(low), cleaned.get(high)
            if a is not None and b is not None and a > b:
                self.add_error(low, "Giá trị đầu khoảng phải nhỏ hơn "
                                    "hoặc bằng giá trị cuối khoảng.")

        # §4.3 — khoảng giá trị chỉ có nghĩa khi đã chọn một cảm biến,
        # vì ba đại lượng có đơn vị khác nhau (UC-04 E4).
        if not cleaned.get("sensor"):
            for field in ("value__gte", "value__lte"):
                if cleaned.get(field) is not None:
                    self.add_error(
                        field,
                        "Phải chọn một cảm biến trước khi lọc theo khoảng giá trị.",
                    )
        return cleaned


class SensorDataFilter(filters.FilterSet):
    # Lọc theo MÃ cảm biến chứ không phải id — `?sensor=room01_temp` đọc được,
    # và mã không đổi khi chạy lại migration ở máy khác (`04-Database.md` §4.2).
    sensor = filters.CharFilter(field_name="sensor__code", lookup_expr="exact")
    node = filters.CharFilter(field_name="sensor__node_id", lookup_expr="exact")

    class Meta:
        model = SensorData
        form = RangeConsistencyForm
        fields = {
            "recorded_at": ["gte", "lte"],
            "value":       ["gte", "lte"],     # §4.3 — UC-04 bước 1b
        }
```

Khai báo `fields` dạng dict khiến django-filter tự sinh tên tham số đúng quy ước `<cột>__<phép so sánh>`, không phải viết tay từng filter.

ViewSet tương ứng:

```python
class SensorViewSet(ReadOnlyModelViewSet):
    # select_related BẮT BUỘC: serializer đọc sensor.code / name / unit ở mọi
    # dòng, thiếu nó thì 10 dòng thành 11 truy vấn (`04-Database.md` §11.3).
    queryset = SensorData.objects.select_related("sensor")
    serializer_class = SensorDataSerializer
    pagination_class = StandardPagination
    filterset_class = SensorDataFilter
    search_fields = ["sensor__code", "sensor__name"]   # §4.3 — hai cột chuỗi
    ordering_fields = ["recorded_at", "value", "id"]
    ordering = ["-recorded_at", "sensor_id"]           # BR-09 + BR-11
```

> **Ba điểm cần biết.**
> 1. `DjangoFilterBackend` gọi `translate_validation(filterset.errors)` khi form không hợp lệ, sinh ra `ValidationError` của DRF → bộ xử lý ngoại lệ ở §7.5 biến nó thành `400`. Muốn ra đúng mã `INVALID_RANGE` thay vì `VALIDATION_ERROR` thì kiểm tra trong hàm xử lý: nếu mọi khóa trong `details` đều kết thúc bằng `__gte` hoặc `__lte` **và** thông báo lỗi là về thứ tự khoảng thì đổi mã. Lỗi "phải chọn cảm biến" ở trên cũng nằm trên khóa `value__gte` nhưng phải giữ mã `VALIDATION_ERROR` — phân biệt bằng nội dung thông báo, hoặc gắn mã riêng vào `ValidationError`.
> 2. **`ordering_fields` phải liệt kê tường minh.** Để `"__all__"` thì người gọi sắp xếp được theo bất kỳ cột nào, kể cả cột không có index, và `drf-spectacular` cũng không sinh được danh sách gợi ý trong Swagger.
> 3. ⚠️ **`OrderingFilter` THAY THẾ hoàn toàn `ordering` khi client gửi tham số.** Gọi `?ordering=-value` thì thứ tự trở thành `["-value"]` — mất cột phá hòa, và ba bản ghi cùng chu kỳ lại có thể đổi chỗ giữa các lần gọi, gây lặp/mất dòng khi lật trang (§4.3). Phải nối thêm cột phá hòa:
>
> ```python
> class TiebreakOrderingFilter(OrderingFilter):
>     """Luôn nối một cột phá hòa vào cuối, để thứ tự xác định duy nhất."""
>
>     def get_ordering(self, request, queryset, view):
>         ordering = super().get_ordering(request, queryset, view)
>         if ordering and "id" not in ordering and "-id" not in ordering:
>             return list(ordering) + ["sensor_id"]
>         return ordering
> ```
>
> Đây là lỗi **chỉ lộ ra khi lật sang trang 2** — dễ lọt qua mọi lần thử tay trên trang đầu.

### 7.4 View điều khiển thiết bị

Đây là đoạn mã cần chính xác nhất trong toàn bộ backend — nó phải thỏa mãn cùng lúc BR-04, BR-05, BR-06 và luồng ngoại lệ E2/E3/E4.

```python
class DeviceViewSet(ReadOnlyModelViewSet):
    queryset = Device.objects.filter(is_active=True)
    serializer_class = DeviceSerializer
    pagination_class = None                       # §4.4 — không bọc phân trang

    @action(detail=True, methods=["post"], url_path="control")
    def control(self, request, pk=None):
        device = self.get_object()                # 404 nếu không có / đã tháo
        serializer = ControlRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)          # 400
        action_value = serializer.validated_data["action"]
        user = request.user                                # §2.2 — lấy từ token, không từ body

        try:
            with transaction.atomic():
                busy = (ActionHistory.objects
                        .filter(device=device,
                                status=ActionHistory.Status.PENDING)
                        .exists())
                if busy:
                    raise DeviceBusy()                     # 409

                record = ActionHistory.objects.create(
                    device=device, action=action_value,
                    user=user,                             # luôn có — endpoint yêu cầu đăng nhập
                )                                          # PENDING, BR-05
                publish_control(record.request_id, device.code, action_value)
        except (OSError, TimeoutError) as exc:
            # publish thất bại -> giao dịch đã cuộn ngược, không còn bản ghi nào
            raise BrokerUnavailable() from exc             # 503

        return Response(ControlAcceptedSerializer(record).data,
                        status=status.HTTP_202_ACCEPTED)
```

Serializer chuẩn hóa chữ hoa cho `action`:

```python
class ControlRequestSerializer(serializers.Serializer):
    action = serializers.CharField()
    # Bản 2.1 bỏ trường user_id: người thao tác lấy từ request.user (§4.5).

    def validate_action(self, value):
        value = value.strip().upper()
        if value not in ("ON", "OFF"):
            raise serializers.ValidationError(
                'Giá trị phải là "ON" hoặc "OFF".')
        return value
```

> **Chống giả mạo người thao tác không cần viết thêm dòng nào.** Serializer chỉ khai báo `action`, nên `user_id` người gọi gửi kèm bị DRF bỏ qua. Người thao tác chỉ có thể là chủ của token — đã được `TokenAuthentication` xác thực trước khi view chạy (ca kiểm thử A-11c).

Hàm publish dùng client paho ngắn hạn (`03-Sequence.md` §3.3):

```python
def publish_control(request_id, device_code, action_value):
    payload = json.dumps({
        "request_id": str(request_id),
        "device": device_code,
        "action": action_value,
    })
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,          # paho-mqtt 2.x
        client_id=f"backend_api_{uuid.uuid4().hex[:8]}",
    )
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=10)
    client.loop_start()
    try:
        info = client.publish("device_control", payload, qos=1)
        info.wait_for_publish(timeout=2)
        if not info.is_published():
            raise TimeoutError("Broker không xác nhận PUBACK trong 2 giây")
    finally:
        client.loop_stop()
        client.disconnect()
```

> ⚠️ **Ba điểm dễ sai trong hàm này.**
> 1. **Bắt buộc `loop_start()` trước khi `publish(qos=1)`.** Không có vòng lặp mạng chạy nền thì message chỉ nằm trong hàng đợi và `disconnect()` sẽ vứt nó đi — API vẫn trả `202` trong khi lệnh chưa từng rời khỏi máy chủ. Đây là lỗi im lặng khó phát hiện nhất của paho.
> 2. **`paho-mqtt` 2.x đổi chữ ký `Client()`**, bắt buộc truyền `CallbackAPIVersion` ở tham số đầu. Cài nhầm bản 1.6.x thì bỏ tham số này đi, nếu không sẽ lỗi `TypeError` — tương tự tình huống `CheckConstraint(condition=…)` của Django 5.1 đã ghi ở `CLAUDE.md` §0.4.
> 3. **`connect()` phải có giới hạn thời gian.** Broker chết mà không đặt timeout thì request treo tới khi hết `keepalive`, phá vỡ NFR-01. Trong LAN, giá trị 2 giây là dư dùng.

### 7.5 Bộ xử lý ngoại lệ thống nhất

```python
# config/exceptions.py
from rest_framework.views import exception_handler as drf_handler
from rest_framework.exceptions import APIException

# Chỉ dùng đúng 9 mã đã công bố ở §2.7 — không sinh thêm mã mới ở đây,
# nếu không "danh sách mã lỗi của toàn hệ thống" sẽ không còn đầy đủ.
CODE_BY_STATUS = {
    400: "VALIDATION_ERROR", 401: "UNAUTHENTICATED", 404: "NOT_FOUND",
    409: "DEVICE_BUSY", 500: "INTERNAL_ERROR", 503: "BROKER_UNAVAILABLE",
}


class InvalidCredentials(APIException):
    status_code = 400                         # §2.7 — cố ý không dùng 401
    error_code = "INVALID_CREDENTIALS"
    default_detail = "Tên đăng nhập hoặc mật khẩu không đúng."


class DeviceBusy(APIException):
    status_code = 409
    error_code = "DEVICE_BUSY"
    default_detail = ("Thiết bị đang chờ phản hồi cho lệnh trước đó, "
                      "vui lòng thử lại sau vài giây.")


class BrokerUnavailable(APIException):
    status_code = 503
    error_code = "BROKER_UNAVAILABLE"
    default_detail = "Không kết nối được tới hệ thống điều khiển (MQTT broker)."


def api_exception_handler(exc, context):
    response = drf_handler(exc, context)
    if response is None:                      # lỗi không do DRF sinh ra -> 500
        return None

    code = getattr(exc, "error_code", None) or \
        CODE_BY_STATUS.get(response.status_code, "ERROR")

    if code == "UNAUTHENTICATED":             # thông báo gốc của DRF là tiếng Anh
        message, details = "Bạn chưa đăng nhập hoặc phiên đăng nhập đã hết.", None
    elif isinstance(response.data, dict) and "detail" in response.data:
        message, details = str(response.data["detail"]), None
    else:                                     # lỗi serializer theo từng trường
        message, details = "Dữ liệu gửi lên không hợp lệ.", response.data

    response.data = {"error": {"code": code, "message": message,
                               "details": details}}
    return response
```

Riêng lỗi `404` do phân trang cần mã `PAGE_NOT_FOUND` thay vì `NOT_FOUND`; cách gọn nhất là bắt `NotFound` có `detail` bằng `"Invalid page."` trong hàm trên và đổi mã.

### 7.6 Consumer WebSocket

```python
# apps/realtime/consumers.py
class RealtimeConsumer(AsyncJsonWebsocketConsumer):
    GROUP = "realtime"

    async def connect(self):
        await self.accept()                       # §5.1 — accept TRƯỚC rồi mới đóng
        if self.scope["user"].is_anonymous:
            await self.close(code=4401)           # sai/thiếu token
            return
        await self.channel_layer.group_add(self.GROUP, self.channel_name)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    async def receive_json(self, content, **kwargs):
        logger.info("Bỏ qua message từ client: %s", content)   # §5.1

    # Tên phương thức = giá trị "type" với dấu chấm đổi thành gạch dưới
    async def sensor_data(self, event):
        await self.send_json(event)

    async def device_state(self, event):
        await self.send_json(event)
```

Channels không có sẵn cách đọc token của DRF, nên cần một middleware nhỏ đọc `?token=` rồi gắn người dùng vào `scope`:

```python
# apps/realtime/auth.py
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user(key):
    try:
        user = Token.objects.select_related("user").get(key=key).user
    except Token.DoesNotExist:
        return AnonymousUser()
    return user if user.is_active else AnonymousUser()   # giống TokenAuthentication


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        key = parse_qs(scope["query_string"].decode()).get("token", [None])[0]
        scope["user"] = await get_user(key) if key else AnonymousUser()
        return await super().__call__(scope, receive, send)
```

```python
# config/asgi.py — bọc router WebSocket
"websocket": AllowedHostsOriginValidator(
    TokenAuthMiddleware(URLRouter(websocket_urlpatterns))
),
```

> ⚠️ **`asgi.py` phải gọi `get_asgi_application()` trước khi import `TokenAuthMiddleware`.** File middleware import model `Token`; import sớm hơn thì Django chưa nạp xong ứng dụng và báo `AppRegistryNotReady`.

Phía worker (mã đồng bộ):

```python
# `rows` là danh sách SensorData vừa bulk_create cho MỘT chu kỳ (§5.2).
# Gom lại thành gói phẳng theo metric_type, cảm biến nào thiếu thì để None.
values = {r.sensor.metric_type.lower(): r.value for r in rows}

async_to_sync(get_channel_layer().group_send)("realtime", {
    "type": "sensor.data",
    "device_id": node_id,
    "temperature": values.get("temperature"),
    "humidity": values.get("humidity"),
    "light": values.get("light"),
    "recorded_at": recorded_at.isoformat().replace("+00:00", "Z"),
})
```

> **Một chu kỳ = một sự kiện, dù CSDL nhận ba bản ghi.** Dùng `.get()` chứ không phải `[...]` để cảm biến lỗi cho ra `None` (→ `null` trong JSON) thay vì ném `KeyError` làm dừng worker (NFR-16). `recorded_at` lấy từ biến chung của chu kỳ, **không** lấy từ `rows[0].recorded_at` — cả ba bằng nhau nên hai cách cho cùng kết quả, nhưng dùng biến chung thì đoạn mã tự nói lên ràng buộc BR-11.

### 7.7 View đăng nhập và đăng xuất

```python
# apps/users/views.py
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.exceptions import InvalidCredentials
from .models import User


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)     # điểm 1


class LoginUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "full_name", "role"]


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []                                 # điểm 2

    def post(self, request):
        s = LoginRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)                        # 400 VALIDATION_ERROR
        user = authenticate(request, **s.validated_data)        # None nếu sai hoặc đã khóa
        if user is None:
            raise InvalidCredentials()                          # 400 INVALID_CREDENTIALS
        token, _ = Token.objects.get_or_create(user=user)       # điểm 3
        update_last_login(None, user)
        return Response({"token": token.key,
                         "user": LoginUserSerializer(user).data})


class LogoutView(APIView):
    # Dùng IsAuthenticated mặc định → thiếu token thì 401 trước khi vào hàm.
    def post(self, request):
        request.auth.delete()               # request.auth chính là đối tượng Token
        return Response(status=status.HTTP_204_NO_CONTENT)
```

> **Ba điểm dễ sai.**
> 1. **`trim_whitespace=False` cho mật khẩu.** `CharField` mặc định cắt khoảng trắng ở đầu và cuối; mật khẩu có dấu cách ở hai đầu sẽ **không bao giờ** khớp, và lỗi hiện ra chỉ là "sai mật khẩu".
> 2. **`authentication_classes = []` ở riêng view đăng nhập.** Nếu trình duyệt còn giữ một token đã bị thu hồi mà vẫn gửi kèm, `TokenAuthentication` trả `401` **trước khi view kịp chạy** — người dùng không đăng nhập lại được. Bỏ xác thực ở view này là hết. Vì sai mật khẩu trả `400` chứ không phải `401`, view này cũng không dính bẫy `403` ở §2.2.
> 3. **`get_or_create` → mỗi người dùng một token dùng chung** cho mọi tab và mọi máy (§4.8).

---

## 8. OPENAPI, SWAGGER VÀ POSTMAN

### 8.1 Sinh tài liệu tự động

```bash
# Xem trực tiếp trên trình duyệt (T-17)
http://localhost:8000/api/schema/swagger-ui/

# Xuất file OpenAPI để nộp kèm báo cáo
python manage.py spectacular --file docs/openapi.yaml
```

`drf-spectacular` đọc được serializer và filter backend, nhưng **không tự biết** ba thứ sau — phải chú thích thủ công bằng `@extend_schema`:

| Nội dung | Vì sao không tự sinh được |
|---|---|
| `/api/sensors/latest` trả **mảng** chứ không phải một object | Endpoint dùng `@action`, `drf-spectacular` suy ra kiểu từ serializer nên mặc định coi là một đối tượng đơn — phải khai `responses={200: SensorReadingSerializer(many=True)}` |
| Các mã lỗi `400/401/404/409/503` kèm ví dụ | Hình dạng lỗi do bộ xử lý ngoại lệ tùy chỉnh quyết định (§7.5) |
| Toàn bộ giao diện WebSocket và MQTT | OpenAPI 3.0 chỉ mô tả HTTP |

Ví dụ chú thích cho endpoint điều khiển:

```python
@extend_schema(
    request=ControlRequestSerializer,
    responses={
        202: ControlAcceptedSerializer,
        400: ErrorSerializer, 401: ErrorSerializer, 404: ErrorSerializer,
        409: ErrorSerializer, 503: ErrorSerializer,
    },
    examples=[
        OpenApiExample("Bật đèn", value={"action": "ON"}),
    ],
)
```

> ⚠️ **Nút Authorize của Swagger phải nhập cả chữ `Token`.** `drf-spectacular` tự nhận ra `TokenAuthentication` và hiện nút **Authorize**, nhưng ô nhập ghi thẳng giá trị vào header `Authorization`. Phải gõ `Token 9944b0…` (có chữ `Token` và một dấu cách); chỉ dán mã token thì mọi request trả `401`.

> **WebSocket và MQTT không nằm trong Swagger.** Khi trình bày, đây chính là lý do tài liệu này tồn tại song song với Swagger UI: §5 và §6 là phần hợp đồng mà OpenAPI không biểu diễn được.

### 8.2 Postman Collection

Xuất ra `docs/postman_collection.json`, tổ chức theo 5 thư mục tương ứng §4:

```
IoT Room Monitoring
├── Auth         POST login · POST logout
├── Sensors      GET devices · GET latest · GET chart · GET list (kèm ví dụ có bộ lọc)
├── Devices      GET list · POST control (ON) · POST control (OFF)
├── Actions      GET list · GET list?status=FAILED · GET list?user=none
└── Profile      GET profile
```

Dùng biến môi trường `{{base_url}} = http://localhost:8000/api` để đổi giữa máy cá nhân và IP LAN mà không phải sửa từng request.

**Token dùng chung cho cả collection.** Đặt mục *Authorization* của collection là header `Authorization: Token {{token}}`, rồi thêm đoạn script sau vào tab *Scripts → Post-response* của request `POST login` để tự lưu token:

```js
pm.collectionVariables.set("token", pm.response.json().token);
```

Chỉ cần chạy `login` một lần, mọi request khác tự dùng token mới. Riêng request `POST login` đặt *Authorization* là **No Auth**.

Ba request nên chuẩn bị sẵn để **minh họa lỗi** khi vấn đáp — chúng thể hiện rõ hơn phần xử lý ngoại lệ so với các request thành công:

| Request | Kết quả mong đợi |
|---|---|
| `POST /api/devices/999/control` | `404 NOT_FOUND` |
| `POST /api/devices/1/control` với `{"action":"TOGGLE"}` | `400 VALIDATION_ERROR` |
| `POST /api/devices/1/control` khi đã tắt Mosquitto | `503 BROKER_UNAVAILABLE` |
| `GET /api/sensors` với *Authorization* đặt **No Auth** | `401 UNAUTHENTICATED` |

---

## 9. MA TRẬN TRUY VẾT

### 9.1 Endpoint ↔ UC ↔ FR ↔ bảng dữ liệu

| Endpoint | UC | FR | Sequence | Bảng CSDL |
|---|---|---|---|---|
| `GET /api/sensors/devices` | UC-01, UC-03 | FR-16, FR-17 | SD-04 | `sensors_sensordevice` |
| `GET /api/sensors/latest` | UC-01 | FR-01, FR-02, FR-17 | SD-04 | `sensors_sensordata`, `sensors_sensordevice` |
| `GET /api/sensors/chart` | UC-01 | FR-03 | SD-04 | `sensors_sensordata`, `sensors_sensordevice` |
| `GET /api/sensors` | UC-03, UC-04 | FR-07, FR-10, FR-11, FR-17 | SD-06 | `sensors_sensordata`, `sensors_sensordevice` |
| `GET /api/devices` | UC-01 | FR-04, FR-16 | SD-04, SD-05 | `devices_device` |
| `POST /api/devices/{id}/control` | UC-02 | FR-04, FR-05, FR-08, FR-09, FR-18 | SD-01, SD-02, SD-05 | `devices_device`, `devices_actionhistory`, `users_user` |
| `GET /api/actions` | UC-05, UC-04 | FR-08, FR-10, FR-11, FR-18 | SD-06 | `devices_actionhistory`, `users_user` |
| `GET /api/profile` | UC-06 | FR-13 | — | *(không có — đọc `.env`)* |
| `POST /api/auth/login` | UC-08 | FR-19 | — | `users_user`, `authtoken_token` |
| `POST /api/auth/logout` | UC-08 | FR-19 | — | `authtoken_token` |
| `WS /ws/realtime/` | UC-01, UC-02 | FR-12, FR-15 | SD-02→SD-05 | *(không có — chỉ truyền tin)* |
| MQTT `data_sensors` | UC-07 | FR-01, FR-14, FR-17 | SD-03 | `sensors_sensordata`, `sensors_sensordevice` |
| MQTT `device_control` | UC-02 | FR-05 | SD-01, SD-02 | `devices_actionhistory` |
| MQTT `device_respond` | UC-02 | FR-06 | SD-01, SD-02, SD-05 | `devices_device`, `devices_actionhistory` |

**Kiểm tra độ phủ:** FR-01 → FR-19 đều có ít nhất một giao diện hiện thực, trừ **FR-15** (hiển thị online/offline) được xử lý hoàn toàn ở Frontend bằng bộ đếm 30 giây trên sự kiện `sensor.data` (BR-07) nên không phát sinh endpoint riêng.

### 9.2 Quy tắc nghiệp vụ ↔ nơi hiện thực

| BR | Nội dung | Hiện thực ở đâu trong API |
|---|---|---|
| BR-01 | Chu kỳ 2 giây | Firmware; API không ràng buộc |
| BR-02 | Ngưỡng dữ liệu hợp lệ, **riêng theo từng cảm biến** | §6.2 — worker đọc `min_value`/`max_value` của cảm biến rồi loại **đúng số đo** vượt ngưỡng trước khi ghi |
| BR-03 | Timeout 5 giây | Vòng quét ở P2 → sự kiện `device.state` `FAILED` (§5.3) |
| BR-04 | Thiết bị không nhận lệnh mới khi còn `PENDING` | Hai tầng: Frontend khóa công tắc (§5.4) **và** máy chủ trả `409 DEVICE_BUSY` — UC-02 E6 (§4.5) |
| BR-05 | Mỗi lệnh sinh đúng một bản ghi | `POST .../control` trong `transaction.atomic()` |
| BR-06 | `request_id` duy nhất | Trả về ở `202`, lặp lại ở MQTT và `device.state` |
| BR-07 | Ngoại tuyến sau 30 giây | Frontend đếm giờ trên `sensor.data` (§5.4) |
| BR-08 | Phân trang 10/100 | §2.8 |
| BR-09 | Sắp xếp thời gian giảm dần | `ordering` mặc định của §4.3 và §4.6 |
| BR-10 | Biểu đồ 20 chu kỳ | `limit=20` mặc định của §4.2 |
| BR-11 | Mỗi số đo một bản ghi, cùng chu kỳ cùng mốc thời gian | Worker `bulk_create` với `recorded_at` tính một lần (§6.2); ràng buộc `UNIQUE (sensor_id, recorded_at)`; `ordering` hai cột ở §7.3 |
| BR-12 | Ghi nhận người thao tác | Lấy từ token ở `POST .../control` (§4.5); trường `user` vẫn có thể `null` ở `GET /api/actions` với bản ghi không đi qua API (§4.6); bộ lọc `?user=` và `?user=none` |
| BR-13 | Mọi thao tác trên hệ thống yêu cầu đăng nhập | `IsAuthenticated` mặc định (§7.1); `401 UNAUTHENTICATED` (§2.7); WebSocket đóng mã `4401` (§5.1) |

---

## 10. KỊCH BẢN KIỂM THỬ API

Tổng **36 kịch bản**, chạy được bằng Postman hoặc `curl`, **không cần phần cứng** trừ A-16 → A-18.

> Từ bản 2.1, mọi ca đều **gửi kèm token của `admin`**, trừ khi ghi khác. Bản 2.0 ghi "25 kịch bản" trong khi bảng có 31 dòng; bản 2.1 đếm lại và thêm 5 ca A-19 → A-23.
>
> Các ca A-11 → A-11c cùng gọi thiết bị số 1: chạy **cách nhau ít nhất 7 giây**, nếu không ca sau nhận `409 DEVICE_BUSY` vì lệnh trước còn `PENDING` (BR-04).

| # | Kịch bản | Kết quả mong đợi | Liên quan |
|---|---|---|---|
| A-00 | `GET /api/sensors/devices` | Mảng thuần 3 phần tử kèm `code`, `name`, `unit`; **không** có `count`/`results` | §4.0, FR-17 |
| A-01 | `GET /api/sensors/latest` khi CSDL rỗng | `200` kèm mảng rỗng `[]` | UC-01 A1, §4.1 |
| A-02 | Gửi 1 message giả bằng `mosquitto_pub` rồi gọi lại A-01 | `200` kèm **3 phần tử**, cả ba cùng một `recorded_at` | FR-01, BR-11 |
| A-02b | Sau A-02, `GET /api/sensors` | `count` tăng đúng **3**, ba dòng đầu cùng mốc thời gian, thứ tự Nhiệt độ → Độ ẩm → Ánh sáng | BR-11, §4.3 |
| A-02c | Gửi message thiếu trường `humidity`, rồi `GET /api/sensors` | `count` chỉ tăng **2**; không có dòng nào cho `room01_humi` ở mốc đó | UC-07 A2 |
| A-03 | `GET /api/sensors/chart` | Mảng ≤ 20 phần tử, **tăng dần** theo `recorded_at`, mỗi phần tử có đủ 3 khóa | BR-10 |
| A-03b | Sau A-02c, `GET /api/sensors/chart` | Phần tử của mốc thiếu số đo có `"humidity": null`, **không** bị loại khỏi mảng | §4.2 |
| A-04 | `GET /api/sensors?page_size=500` | `200`, đúng 100 phần tử (tự hạ về biên) | UC-04 E3 |
| A-05 | `GET /api/sensors?page_size=abc` | `400 VALIDATION_ERROR` | §2.8 |
| A-06 | `GET /api/sensors?page=99999` | `404 PAGE_NOT_FOUND` | UC-03 A2 |
| A-07 | `GET /api/sensors?recorded_at__gte=…&…__lte=…` với ngày ngược nhau | `400 INVALID_RANGE` | UC-04 E2 |
| A-07b | `GET /api/sensors?sensor=room01_temp&value__gte=35&value__lte=20` | `400 INVALID_RANGE`, `details` chỉ đúng cặp `value__*` | UC-04 E2 |
| A-07c | `GET /api/sensors?sensor=room01_temp&value__gte=30&recorded_at__gte=…` | `200`, mọi bản ghi đều thỏa **cả hai** điều kiện và đều thuộc cảm biến nhiệt độ | UC-04 bước 1b |
| A-07d | `GET /api/sensors?value__gte=30` **không kèm `sensor`** | `400 VALIDATION_ERROR`, `details.value__gte` nói phải chọn cảm biến | UC-04 E4 |
| A-07e | `GET /api/sensors?search=độ ẩm` | Chỉ trả bản ghi của `room01_humi` | §4.3 |
| A-07f | Lấy trang 1 rồi trang 2 với `?ordering=-value&page_size=3` | Không có `id` nào xuất hiện ở **cả hai** trang | §4.3, §7.3 |
| A-08 | `GET /api/devices` | Mảng thuần 2 phần tử, **không** có `count`/`results` | §4.4 |
| A-09 | `POST /api/devices/999/control` `{"action":"ON"}` | `404 NOT_FOUND` | UC-02 E3 |
| A-10 | `POST /api/devices/1/control` `{"action":"TOGGLE"}` | `400 VALIDATION_ERROR`, `details.action` có nội dung | UC-02 E4 |
| A-11 | `POST /api/devices/1/control` `{"action":"on"}` | `202` — chuỗi thường được chuẩn hóa | §4.5 |
| A-11b | `POST /api/devices/1/control` `{"action":"ON"}` với token của `admin` | `202` kèm `"user": {"id": 1, "full_name": "Lưu Đức Anh"}`; bản ghi trong `GET /api/actions` mang đúng tên này | FR-18, BR-12 |
| A-11c | `POST /api/devices/1/control` `{"action":"ON","user_id":1}` với token của **`operator`** | `202` kèm `user` là **Người vận hành** — `user_id` trong thân yêu cầu bị bỏ qua, không giả mạo được | §4.5, BR-12 |
| A-11d | `POST /api/devices/1/control` `{"action":"ON"}` **không có token** | `401 UNAUTHENTICATED`; `GET /api/actions` **không** có bản ghi mới | BR-13 |
| A-11e | `GET /api/actions?user=none` | Chỉ trả các bản ghi không đi qua API (dữ liệu khởi tạo, ví dụ `id 79`); **không** có bản ghi nào do A-11b, A-11c tạo | §4.6, BR-12 |
| A-12 | Tắt Mosquitto, gọi `POST .../control` | `503 BROKER_UNAVAILABLE`, và `GET /api/actions` **không** có bản ghi mới | UC-02 E2 |
| A-13 | Gọi `POST .../control` hai lần liên tiếp trong 1 giây | Lần đầu `202`, lần sau `409 DEVICE_BUSY`; `GET /api/actions` chỉ có **một** bản ghi mới | UC-02 E6, BR-04 |
| A-14 | Sau A-13, chờ 7 giây rồi gọi lại | `202` — bản ghi cũ đã tự chuyển `FAILED` | BR-03 |
| A-15 | `GET /api/actions?status=FAILED` sau A-14 | Có ít nhất 1 bản ghi, `error_message` nói về timeout | UC-05 |
| A-16 | Mở 2 tab trình duyệt, bật đèn ở tab 1 | Tab 2 nhận `device.state` và tự đổi công tắc | T-15, FR-12 |
| A-17 | Rút nguồn ESP8266 rồi bấm bật đèn | Sau 5–6 giây có `device.state` `FAILED`; lịch sử ghi `FAILED` | T-07, BR-03 |
| A-18 | Mở `/api/schema/swagger-ui/` **khi chưa đăng nhập** | Mở được; liệt kê đủ **10** endpoint chính; bấm Authorize nhập `Token <token>` rồi gọi thử được | T-17, §3.3 |
| A-19 | `POST /api/auth/login` với tài khoản `admin` và mật khẩu đúng | `200` kèm `token` dài 40 ký tự và `user` có `username`, `full_name`, `role` | §4.8, UC-08 |
| A-20 | `POST /api/auth/login` sai mật khẩu; rồi thử lại với tên đăng nhập không tồn tại | Cả hai đều `400 INVALID_CREDENTIALS` với **cùng một** `message` | §2.7, UC-08 E1 |
| A-21 | `GET /api/sensors` **không** có header `Authorization` | `401 UNAUTHENTICATED`, phản hồi có header `WWW-Authenticate: Token` — **không** phải `403` | §2.2, BR-13 |
| A-22 | `POST /api/auth/logout`, rồi dùng lại chính token đó gọi `GET /api/devices` | Lần đầu `204`; lần sau `401 UNAUTHENTICATED` | §4.9 |
| A-23 | Mở WebSocket `ws://localhost:8000/ws/realtime/?token=sai` | Kết nối được chấp nhận rồi **đóng ngay với mã `4401`**, không phải `1006` | §5.1, BR-13 |

A-00 → A-15 và A-19 → A-22 **chạy được ngay ở tuần 3** khi chưa lắp mạch, chỉ cần Mosquitto và `mosquitto_pub` để giả lập thiết bị. A-23 cần công cụ gọi được WebSocket (Postman có sẵn). A-16 → A-18 cần Frontend hoặc phần cứng.

> **A-21 và A-23 là hai ca đáng chạy nhất của phần đăng nhập**, vì lỗi của chúng không làm hỏng chức năng nào mà chỉ khiến Frontend phản ứng sai: nhận `403` thay vì `401` thì không về trang đăng nhập; nhận `1006` thay vì `4401` thì thử kết nối lại mãi mãi.

> **Bốn ca đáng chú ý nhất** vì chúng bắt được lỗi mà thử tay khó phát hiện:
> - **A-02b** và **A-02c** kiểm chứng BR-11: một message vào phải ra đúng 3 dòng cùng mốc thời gian, và cảm biến lỗi thì thiếu dòng chứ không phải có dòng rỗng.
> - **A-03b** kiểm chứng rằng chu kỳ thiếu số đo **vẫn nằm trên biểu đồ** với giá trị `null` — nếu backend bỏ cả chu kỳ thì trục thời gian bị co lại mà nhìn biểu đồ không nhận ra.
> - **A-07f** kiểm chứng thứ tự sắp xếp có cột phá hòa. Đây là lỗi **chỉ lộ ra khi lật trang** (§7.3 điểm 3), và cũng là lỗi dễ bị bỏ qua nhất trong toàn bộ danh sách này.

---

## 11. QUYẾT ĐỊNH CHỐT TẠI TÀI LIỆU NÀY

### 11.1 Ba điểm treo từ `03-Sequence.md` §10 nay đã chốt

| # | Vấn đề | Quyết định | Mục |
|---|---|---|---|
| ① | Mã trạng thái của `POST .../control` | **`202 Accepted`** — lệnh mới được tiếp nhận, kết quả về qua WebSocket | §4.5 |
| ③ | `device.state` có kèm `device_id` số không | **Có** — gửi cả `device_id` (int) và `device` (code), tổng chưa tới 30 byte | §5.3 |
| ⑤ | Tên nhóm WebSocket | **`realtime`**, một nhóm duy nhất cho toàn hệ thống | §5.1 |

Hai điểm ② (bộ đếm dự phòng ~7 giây ở Frontend) và ④ (chu kỳ vòng quét 1 giây) vẫn giữ nguyên giả định, phải **đo lại khi có phần cứng** ở tuần 2–4.

### 11.2 Quyết định mới phát sinh trong tài liệu này

| Quyết định | Lý do |
|---|---|
| **`409 DEVICE_BUSY`** khi thiết bị còn lệnh `PENDING` | BR-04 khóa công tắc ở Frontend chỉ có tác dụng trong một tab; T-15 mở hai tab là lách qua được. Máy chủ là nơi duy nhất chặn được (§4.5) |
| ~~**`204 No Content`** cho `/api/sensors/latest` khi bảng rỗng~~ | **Đã bỏ ở bản 2.0.** Endpoint nay trả mảng nên mảng rỗng `[]` đã đủ nghĩa; giữ `204` sẽ tạo hai hình dạng phản hồi cho cùng một lời gọi (§4.1) |
| **Cấu trúc lỗi thống nhất `{error:{code,message,details}}`** | DRF mặc định trả hai hình dạng khác nhau cho ngoại lệ và lỗi serializer; Frontend sẽ phải viết hai nhánh và không có mã lỗi ổn định để so sánh (§2.6) |
| **`trailing_slash=False`** cho router | `APPEND_SLASH` chuyển hướng `301` và **làm mất body của `POST`** — lệnh điều khiển biến mất im lặng (§2.5) |
| **`TIME_ZONE = "UTC"`**, API luôn trả hậu tố `Z` | Giữ mọi ví dụ trong 4 tài liệu khớp nhau; việc đổi sang giờ Việt Nam là của Frontend (§2.4) |
| **`/api/sensors/chart` trả thứ tự tăng dần** và bỏ `id`/`device_id` | Recharts vẽ theo thứ tự phần tử; đảo ở Backend thì Frontend không phải nhớ quy ước này ở hai chỗ (§4.2) |
| **`GET /api/devices` không phân trang** | Bảng cố định 2 dòng; phải đặt `pagination_class = None` vì `PAGE_SIZE` là cấu hình toàn cục (§4.4) |
| **Thiết bị `is_active = false` trả `404`** | Thiết bị đã tháo không có trong `GET /api/devices`, coi như không tồn tại dưới góc nhìn API (§4.5) |
| **`search` của `/api/sensors` chỉ khớp `device_id`** | `SearchFilter` sinh `ILIKE`, chỉ dùng được cho cột chuỗi; bảng này có đúng một cột chuỗi (§4.3) |
| **Lọc theo khoảng giá trị số đo** bằng 6 tham số `<cột>__gte` / `<cột>__lte` *(bổ sung ở bản 1.1)* | Hiện thực dropdown "Cột ▾" đã vẽ trên wireframe và lời hứa của FR-10 ("lọc theo cột"). **Không kèm index** — xem §12 điểm 2 (§4.3) |
| **Một mã lỗi `INVALID_RANGE` dùng chung** cho khoảng thời gian và khoảng giá trị, thay vì tách `INVALID_DATE_RANGE` | Frontend chỉ cần một nhánh xử lý; muốn biết ô nào sai thì đọc `details` — vốn đã có sẵn trong cấu trúc lỗi (§2.6) |
| **API không trả nhãn tiếng Việt cho enum** | Frontend vốn đã sở hữu toàn bộ chuỗi hiển thị; thêm `*_display` là chia đôi trách nhiệm dịch thuật ra hai nơi (§2.3) |
| **WebSocket một chiều, message từ client bị bỏ qua** | Điều khiển cần mã lỗi 400/404/409/503, thứ WebSocket không biểu diễn sẵn (§5.1) |
| **Không dùng `retain` ở cả 3 topic MQTT** | ESP8266 khởi động lại sẽ nhận lại lệnh cũ và tự bật đèn (§6.1) |
| **Đăng nhập bằng token của DRF**, không dùng session cookie hay JWT *(bản 2.1)* | Frontend và Backend khác origin nên session kéo theo CSRF và cookie `SameSite`; JWT thêm thư viện và luồng làm mới mà không thu hồi được ngay (§2.2) |
| **Sai mật khẩu trả `400 INVALID_CREDENTIALS`**, `401` chỉ dành cho "chưa đăng nhập" *(bản 2.1)* | Frontend dùng một bộ chặn `401` chung cho mọi request; nếu sai mật khẩu cũng là `401` thì bộ chặn kích hoạt ngay trên trang đăng nhập (§2.7) |
| **Bỏ `user_id` khỏi thân `POST .../control`**, lấy `request.user` *(bản 2.1)* | Chống ghi tên người khác vào lịch sử; hoàn tất điểm 3b của §12 bản 2.0 (§4.5) |
| **WebSocket nhận token qua `?token=`**; sai thì `accept()` rồi đóng mã `4401` *(bản 2.1)* | Trình duyệt không đặt được header cho WebSocket; đóng trước `accept()` chỉ cho mã `1006`, Frontend không phân biệt được với máy chủ tắt (§5.1) |
| **Không có endpoint `GET /api/auth/me`** *(bản 2.1)* | Frontend lưu `user` từ phản hồi đăng nhập. Token bị thu hồi thì request kế tiếp nhận `401` và tự về trang đăng nhập, không cần lời gọi riêng để kiểm tra |
| **Mỗi người dùng một token, không hết hạn** *(bản 2.1)* | Đơn giản nhất với `rest_framework.authtoken`. Hệ quả: đăng xuất ở một nơi là mọi nơi mất đăng nhập (§4.8) |

---

## 12. ĐIỂM CÒN CẦN CHỐT

| # | Vấn đề | Hiện đang giả định | Chốt khi nào |
|---|---|---|---|
| 1 | ~~Lọc theo khoảng giá trị số đo~~ | ✅ **Đã chốt** — bản 1.1 thêm 6 tham số theo cột, bản 2.0 gộp lại còn `value__gte` / `value__lte` kèm `sensor` (§4.3) | — |
| 2 | **Lọc và sắp xếp theo `value` chạy trên cột không có index** | Chấp nhận `Seq Scan`; dưới ~1 triệu bản ghi vẫn đạt NFR-03, nhất là khi đã có điều kiện `sensor` thu hẹp còn 1/3 | Đo bằng `EXPLAIN ANALYZE` ở tuần 3 (`04-Database.md` §11.2). Vượt ngưỡng thì thêm chỉ mục ghép `(sensor_id, value)`, **không** thêm chỉ mục đơn cột |
| 2b | **Mã lỗi cho khoảng lọc ngược** — `INVALID_RANGE` cần một nhánh riêng trong bộ xử lý ngoại lệ, nếu không sẽ rơi vào `VALIDATION_ERROR` chung. Bản 2.0 làm việc này khó hơn: lỗi "phải chọn cảm biến" **cũng** nằm trên khóa `value__gte` nhưng phải giữ mã `VALIDATION_ERROR` | Phân biệt bằng nội dung thông báo, hoặc gắn `code` riêng vào `ValidationError` (§7.3) | Tuần 3, khi viết `api_exception_handler` |
| 2c | **`page_size` mặc định cho `/api/sensors`** — một trang 10 bản ghi nay chỉ chứa 3⅓ chu kỳ (§4.3) | Giữ 10 theo BR-08 | Tuần 4, khi dựng bảng thật. Nếu khó đọc thì đặt mặc định giao diện là 15 hoặc 30 — **đổi ở Frontend**, không đổi BR-08 |
| 3 | **`GET /api/sensors/chart` có cần tham số lọc theo node** không, khi lắp bo mạch thứ hai | Chưa có — chỉ nhận `limit`. Riêng `/api/sensors` **đã có** tham số `node` (§4.3) | Khi mở rộng nhiều phòng |
| 3b | ~~Đăng nhập~~ — ✅ **Đã chốt ở bản 2.1** (token DRF, bỏ `user_id` khỏi thân yêu cầu — §2.2, §4.5). **Phân quyền theo vai trò vẫn chưa làm** | Tài khoản `VIEWER` hiện vẫn gọi được `POST .../control` | Khi cần phân quyền: thêm permission class kiểm tra `role` cho riêng `control`, trả `403` — và phải thêm mã lỗi mới vào §2.7 |
| 4 | **Định dạng `latency_ms`** khi bản ghi còn `PENDING` | Trả `null` | Tuần 4, khi thiết kế cột hiển thị |
| 5 | **Thông tin sinh viên ở §4.7** — học vị giảng viên đã xác nhận là `TS.` (theo `docs/BTH1.docx`) và đã sửa ở bản 2.1; **lớp `D23CQAT01-B` vẫn là suy đoán** | Giữ tạm | Trước khi nộp — ảnh hưởng cả trang bìa báo cáo |
| 6 | **Ảnh đại diện trang Profile** phục vụ thế nào | File tĩnh qua `/static/`; cần bật `STATICFILES_DIRS` | Tuần 4 |
| 7 | **Các tài liệu khác chưa theo kịp bản 2.1** | `01-SRS.md` §8.2 vẫn ghi "không đăng nhập"; chưa có **UC-08** (Đăng nhập, đăng xuất), **FR-19**, **BR-13** trong `01-SRS.md` / `02-UseCase.md` dù tài liệu này đã tham chiếu; ảnh sơ đồ use case phải xuất lại; `04-Database.md` chưa nhắc bảng `authtoken_token`; chưa có bản vẽ màn hình đăng nhập; `BaoCao.md` và bản Word chưa cập nhật | Sau khi code xong Frontend (thứ tự chốt ngày 14/09/2026) |
| 8 | **Token không hết hạn** | Chấp nhận trong LAN | Khi đưa ra Internet: thêm thời hạn cho token hoặc chuyển sang JWT kèm cookie `HttpOnly` |

---

## 13. LỊCH SỬ PHIÊN BẢN

| Phiên bản | Ngày | Người sửa | Nội dung |
|---|---|---|---|
| **2.1** | **14/09/2026** | Nhóm thực hiện | **Bổ sung đăng nhập bằng token.** ① Endpoint mới `POST /api/auth/login` và `POST /api/auth/logout` (§4.8, §4.9); tổng 8 → **10 endpoint REST**. ② §2.2 viết lại: mọi endpoint và kênh WebSocket yêu cầu token, trừ đăng nhập và tài liệu Swagger. ③ Hai mã lỗi mới `INVALID_CREDENTIALS` (400) và `UNAUTHENTICATED` (401), tổng 7 → **9 mã**; `204` dùng lại cho đăng xuất. ④ **`POST .../control` bỏ trường `user_id`**, người thao tác lấy từ token (§4.5). ⑤ WebSocket nhận `?token=`, sai thì đóng mã `4401` (§5.1); §5.4 thêm 2 quy tắc Frontend. ⑥ §7 thêm cấu hình xác thực, middleware WebSocket, view đăng nhập/đăng xuất (§7.7). ⑦ §10 đếm lại bản 2.0 là 31 ca (không phải 25), viết lại A-11b → A-11e, thêm A-19 → A-23 — tổng **36 ca**. ⑧ §4.7 sửa học vị giảng viên `ThS.` → `TS.`. **Các tài liệu khác chưa đồng bộ — xem §12 điểm 7** |
| 2.0 | 20/08/2026 | Nhóm thực hiện | **Đồng bộ theo `04-Database.md` v2.0 — mô hình dữ liệu đổi theo yêu cầu của giảng viên ngày 20/08.** ① Endpoint mới **`GET /api/sensors/devices`** (danh mục cảm biến, §4.0); tổng 7 → **8 endpoint REST**. ② **`/api/sensors/latest` trả mảng**, bỏ `204 No Content` — mảng rỗng đã đủ nghĩa (§4.1). ③ **`/api/sensors` viết lại**: trường trả về gồm `sensor` lồng + `value`, bộ lọc 6 tham số → **`sensor` + `value__gte`/`value__lte`**, thêm `node`, `search` khớp 2 cột chuỗi (§4.3). ④ **`/api/sensors/chart` giữ nguyên hình dạng phản hồi** nhưng đổi cách dựng — backend xoay bảng 60 bản ghi thành 20 phần tử (§4.2). ⑤ **`POST .../control` nhận `user_id` tùy chọn**, phản hồi thêm `user` (§4.5). ⑥ **`/api/actions` thêm trường `user` có thể `null`**, bộ lọc `?user=` và `?user=none` (§4.6). ⑦ `/api/devices` thêm `node_id`; `gpio_pin` chỉ duy nhất trong phạm vi một bo (§4.4). ⑧ Đổi tên mã: `led1`→`room01_lamp`, `led2`→`room01_fan`. ⑨ §7.1 thêm `AUTH_USER_MODEL`; §7.3 viết lại `FilterSet` kèm **`TiebreakOrderingFilter`**; §6.2 gom 3 số đo thành một sự kiện WebSocket. ⑩ Thêm **BR-11**, **BR-12** vào §9.2; ma trận truy vết mở tới FR-18. ⑪ §10: 21 → **25 ca kiểm thử**. **Hợp đồng WebSocket giữ nguyên — mã realtime của Frontend không phải sửa** |
| 1.0 | 17/08/2026 | Nhóm thực hiện | Bản đầu tiên: 7 endpoint REST + 1 kênh WebSocket (2 sự kiện) + 3 topic MQTT, cấu trúc lỗi thống nhất với 7 mã lỗi, 18 kịch bản kiểm thử, chốt 3 điểm treo của `03-Sequence.md` §10 |
| 1.1 | 17/08/2026 | Nhóm thực hiện | Bổ sung **lọc theo khoảng giá trị số đo** cho `/api/sensors`: 6 tham số `<cột>__gte`/`<cột>__lte` (§4.3), mã `FilterSet` kèm kiểm tra khoảng ngược (§7.3), 3 ca kiểm thử A-07b→A-07d (tổng 21 ca). Gộp `INVALID_DATE_RANGE` thành `INVALID_RANGE`. Đánh số lại §7.4→§7.6 |
| 1.2 | 17/08/2026 | Nhóm thực hiện | **Đồng bộ ví dụ với bản vẽ giao diện.** §4.6: ví dụ đổi thành 3 bản ghi `id 86→88` (`FAILED` → bấm lại `SUCCESS` → `PENDING`), `count` = 88, khớp `updated_at` của `led2` ở §4.4 và `request_id` của §4.5; thêm ghi chú truy vết. §4.7: học vị `ThS.` đưa vào chuỗi `supervisor` và biến `PROJECT_SUPERVISOR` thay vì để Frontend tự ghép. **Không đổi đường dẫn, tham số hay mã lỗi nào** |
| 1.3 | 18/08/2026 | Nhóm thực hiện | **Rà soát chéo 5 tài liệu.** §4.2: sửa dữ liệu mẫu của biểu đồ cho khớp bộ dữ liệu chuẩn và bản vẽ Dashboard (mẫu `10:29:24Z` là 27.6 °C / 70.2 % / 352 lux, không phải 28.3 / 71.5 / 349), thêm bản ghi `12041` thiếu độ ẩm kèm giải thích vì sao endpoint này **không** loại bản ghi `null`. §4.5 và §9.2: `409` nay truy vết về luồng ngoại lệ **UC-02 E6** mới thêm ở `02-UseCase.md` 1.3. §4.6: làm rõ ngữ nghĩa `responded_at` / `latency_ms` với lệnh hết giờ. §7.5: `CODE_BY_STATUS` dùng đúng 7 mã đã công bố ở §2.7 (bỏ `CONFLICT`, `SERVICE_UNAVAILABLE`). §10: ghi rõ tổng 21 ca, bổ sung kỳ vọng cho A-13. **Không đổi đường dẫn, tham số hay hình dạng JSON nào** |
