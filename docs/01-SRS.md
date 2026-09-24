# ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)
## Hệ thống giám sát và điều khiển môi trường phòng dựa trên IoT

| | |
|---|---|
| **Phiên bản** | 0.5 (bản nháp) |
| **Ngày** | 20/08/2026 |
| **Môn học** | IoT & Ứng dụng — Học viện Công nghệ Bưu chính Viễn thông |
| **Giảng viên** | Nguyễn Quốc Uy (uynq@ptit.edu.vn) |
| **Nhóm thực hiện** | *(điền tên + MSSV)* |

---

## MỤC LỤC

1. [Giới thiệu](#1-giới-thiệu)
2. [Mô tả tổng quan](#2-mô-tả-tổng-quan)
3. [Yêu cầu chức năng](#3-yêu-cầu-chức-năng)
4. [Yêu cầu giao diện ngoài](#4-yêu-cầu-giao-diện-ngoài)
5. [Yêu cầu phi chức năng](#5-yêu-cầu-phi-chức-năng)
6. [Mô hình dữ liệu](#6-mô-hình-dữ-liệu-mức-khái-niệm)
7. [Tiêu chí nghiệm thu](#7-tiêu-chí-nghiệm-thu-uat)
8. [Phụ lục](#8-phụ-lục)

---

## 1. GIỚI THIỆU

### 1.1 Mục đích
Tài liệu này đặc tả đầy đủ các yêu cầu chức năng và phi chức năng của **Hệ thống giám sát và điều khiển môi trường phòng dựa trên IoT**. Tài liệu là cơ sở để:
- Nhóm phát triển thiết kế (Use Case, Sequence, CSDL, API, Figma) và lập trình.
- Giảng viên đánh giá mức độ đáp ứng yêu cầu tại buổi UAT và live code.

### 1.2 Phạm vi sản phẩm
Hệ thống gồm 2 phần:

- **Phần cứng (Edge):** vi điều khiển ESP8266 NodeMCU đọc số liệu từ cảm biến DHT11 (nhiệt độ, độ ẩm) và quang trở + LM393 (cường độ ánh sáng), điều khiển 2 thiết bị đầu ra (LED mô phỏng đèn và quạt).
- **Phần mềm (Web Application):** ứng dụng web cho phép người dùng theo dõi số liệu môi trường theo thời gian thực, bật/tắt thiết bị từ xa, tra cứu lịch sử số liệu và lịch sử thao tác.

Hai phần giao tiếp với nhau qua **giao thức MQTT** thông qua một **MQTT Broker (Eclipse Mosquitto)**.

**Ngoài phạm vi (Out of scope):** quản lý nhiều phòng, nhiều người dùng, phân quyền, ứng dụng di động native, cảnh báo qua email/SMS, điều khiển thiết bị điện 220V thật.

### 1.3 Định nghĩa và từ viết tắt

| Thuật ngữ | Giải thích |
|---|---|
| **IoT** | Internet of Things |
| **MQTT** | Message Queuing Telemetry Transport — giao thức nhắn tin publish/subscribe nhẹ, dùng cho IoT |
| **Broker** | Máy chủ trung gian nhận và phân phối message MQTT |
| **Topic** | Kênh chủ đề trong MQTT; client publish/subscribe theo topic |
| **Publish / Subscribe** | Gửi message lên topic / Đăng ký nhận message từ topic |
| **QoS** | Quality of Service — mức đảm bảo giao message của MQTT (0, 1, 2) |
| **FE / BE** | Frontend / Backend |
| **WS** | WebSocket — kênh hai chiều realtime giữa FE và BE |
| **GPIO** | General Purpose Input/Output — chân vào/ra của vi điều khiển |
| **DHT11** | Cảm biến nhiệt độ & độ ẩm |
| **LM393** | IC so sánh, dùng với quang trở để đọc ánh sáng |
| **Lux** | Đơn vị đo cường độ chiếu sáng |
| **UAT** | User Acceptance Testing — kiểm thử chấp nhận |
| **UC / FR / NFR** | Use Case / Functional Requirement / Non-Functional Requirement |

### 1.4 Tài liệu tham chiếu
- Ghi chú bài giảng trên bảng (ảnh `1.jpg` – `12.jpg`).
- `CLAUDE.md` — tài liệu bối cảnh và lộ trình dự án.
- MQTT v3.1.1 Specification — OASIS.
- Datasheet DHT11, ESP8266 NodeMCU.

---

## 2. MÔ TẢ TỔNG QUAN

### 2.1 Bối cảnh sản phẩm
Hệ thống là sản phẩm độc lập, triển khai trên một máy laptop duy nhất (chạy Broker + Backend + Database + Frontend) và một mạch phần cứng đặt trong phòng. Cả hai kết nối cùng một mạng WiFi LAN.

### 2.2 Kiến trúc tổng thể

```
        PHÒNG                                    LAPTOP
┌────────────────────┐                ┌────────────────────────────────────┐
│   ESP8266 NodeMCU  │                │                                    │
│  ┌──────────────┐  │                │  ┌──────────────┐                  │
│  │ DHT11        │──┤   pub          │  │ MQTT Broker  │                  │
│  │ (temp, hum)  │  │  data_sensors  │  │  Mosquitto   │                  │
│  └──────────────┘  │ ─────────────► │  │  :1883       │                  │
│  ┌──────────────┐  │                │  └──────┬───────┘                  │
│  │ Quang trở +  │──┤   pub          │         │ sub data_sensors         │
│  │ LM393 (lux)  │  │ device_respond │         │ sub device_respond       │
│  └──────────────┘  │ ─────────────► │         │ pub device_control       │
│  ┌──────────────┐  │                │  ┌──────▼───────┐   ┌───────────┐  │
│  │ LED 1 (Đèn)  │◄─┤   sub          │  │   Backend    │──►│ Database  │  │
│  │ LED 2 (Quạt) │  │ device_control │  │Django+DRF+WS │◄──│PostgreSQL │  │
│  └──────────────┘  │ ◄───────────── │  └──────┬───────┘   └───────────┘  │
│                    │                │         │ HTTP / WebSocket         │
│      WiFi 2.4GHz   │                │  ┌──────▼───────┐                  │
└────────────────────┘                │  │  Frontend    │◄─── Người dùng   │
                                      │  │  Web (React) │                  │
                                      │  └──────────────┘                  │
                                      └────────────────────────────────────┘
```

### 2.2.1 Phân rã tiến trình phía Backend

Backend xây dựng trên Django — một framework đồng bộ theo mô hình request–response, không có sẵn vòng lặp nền để duy trì kết nối MQTT. Do đó backend được tách thành **hai tiến trình chạy song song**, giao tiếp với nhau qua **Redis channel layer**:

| Tiến trình | Thành phần | Trách nhiệm |
|---|---|---|
| **P1 — ASGI server** (`daphne`) | Django REST Framework + Django Channels | Phục vụ REST API cho Frontend; duy trì kết nối WebSocket; publish lệnh lên `device_control` |
| **P2 — MQTT worker** (`manage.py mqtt_worker`) | `paho-mqtt` | Subscribe `data_sensors` và `device_respond`; kiểm tra và ghi dữ liệu vào PostgreSQL; đẩy sự kiện tới P1 qua Redis để phát ra WebSocket |

Redis là thành phần bắt buộc: hai tiến trình nằm ở hai không gian bộ nhớ khác nhau nên không thể dùng channel layer trong bộ nhớ.

### 2.3 Chức năng chính của sản phẩm
1. Thu thập số liệu nhiệt độ, độ ẩm, ánh sáng theo chu kỳ và truyền về hệ thống.
2. Hiển thị số liệu tức thời dưới dạng thẻ số và biểu đồ thời gian thực.
3. Điều khiển bật/tắt thiết bị từ giao diện web và nhận phản hồi xác nhận từ phần cứng.
4. Lưu trữ toàn bộ số liệu cảm biến và toàn bộ thao tác điều khiển.
5. Tra cứu lịch sử với tìm kiếm, lọc, sắp xếp, phân trang.
6. Trang Profile chứa thông tin nhóm và liên kết tới các sản phẩm bàn giao.

### 2.4 Đặc điểm người dùng

| Tác nhân | Mô tả | Trình độ |
|---|---|---|
| **Người dùng (User)** | Người sử dụng phòng, theo dõi môi trường và bật/tắt thiết bị | Không cần kiến thức kỹ thuật |
| **Thiết bị IoT (ESP8266)** | Tác nhân hệ thống, tự động gửi số liệu và thực thi lệnh | — |
| **MQTT Broker** | Tác nhân hệ thống, trung chuyển message | — |

> **Về người dùng và đăng nhập** *(chốt lại ở bản 0.5)*: hệ thống **có lưu danh sách người dùng** để ghi nhận ai đã thao tác vào thiết bị (FR-18), nhưng ở phạm vi đồ án **chưa có màn hình đăng nhập và chưa phân quyền**. Người thao tác được xác định qua trường `user_id` tùy chọn trong lời gọi API điều khiển; lệnh không xác định được người phát ra thì bản ghi lịch sử để trống trường này.
>
> Bảng người dùng có sẵn cột `role` (`ADMIN` / `OPERATOR` / `VIEWER`) nhưng hiện **chỉ mang tính mô tả**, chưa dùng để chặn thao tác. Đây là chỗ móc sẵn cho phần đăng nhập và phân quyền ở hướng phát triển — thêm một cột vào bảng vài dòng lúc này gần như không tốn gì, còn thêm sau khi đã có dữ liệu thật thì phải chạy migration kèm giá trị mặc định.

### 2.5 Ràng buộc

| Mã | Ràng buộc |
|---|---|
| CO-01 | Vi điều khiển bắt buộc là ESP8266 NodeMCU (hoặc ESP32), lập trình bằng Arduino IDE |
| CO-02 | Giao tiếp phần cứng ↔ máy chủ bắt buộc dùng MQTT với đúng 3 topic: `data_sensors`, `device_control`, `device_respond` |
| CO-03 | Cơ sở dữ liệu là **PostgreSQL 16**; truy cập qua Django ORM, schema quản lý bằng migration |
| CO-03b | Backend là **Django 5 + Django REST Framework**; realtime dùng **Django Channels** trên ASGI |
| CO-03c | Hệ thống cần thêm **Redis** làm channel layer để hai tiến trình backend trao đổi sự kiện |
| CO-04 | ESP8266 chỉ kết nối được WiFi băng tần 2.4 GHz |
| CO-05 | DHT11 có chu kỳ đọc tối thiểu 1 giây, sai số ±2°C / ±5% RH |
| CO-06 | Toàn bộ hệ thống chạy trên mạng LAN nội bộ, không public Internet |

### 2.6 Giả định và phụ thuộc
- Laptop và ESP8266 luôn ở cùng một mạng WiFi và WiFi hoạt động ổn định.
- Mosquitto Broker được cài đặt và khởi chạy trước khi bật Backend và phần cứng.
- PostgreSQL và Redis đã chạy sẵn trên laptop trước khi khởi động Backend.
- Cả hai tiến trình backend (ASGI server và MQTT worker) đều phải được khởi chạy; thiếu MQTT worker thì hệ thống vẫn phục vụ được API tra cứu nhưng **mất toàn bộ chức năng realtime và điều khiển**.
- Đèn/quạt trong đồ án được mô phỏng bằng LED, không đấu nối điện lưới.

---

## 3. YÊU CẦU CHỨC NĂNG

### 3.1 Danh sách Use Case

| ID | Tên Use Case | Tác nhân chính | Độ ưu tiên |
|---|---|---|---|
| UC-01 | Xem Dashboard giám sát | Người dùng | Cao |
| UC-02 | Điều khiển bật/tắt thiết bị | Người dùng | Cao |
| UC-03 | Xem lịch sử số liệu cảm biến | Người dùng | Cao |
| UC-04 | Tìm kiếm, lọc, sắp xếp, phân trang dữ liệu | Người dùng | Trung bình |
| UC-05 | Xem lịch sử thao tác thiết bị | Người dùng | Cao |
| UC-06 | Xem trang Profile | Người dùng | Thấp |
| UC-07 | Thu thập và truyền số liệu cảm biến *(tự động)* | Thiết bị IoT | Cao |

---

### 3.2 Đặc tả chi tiết Use Case

#### UC-01 — Xem Dashboard giám sát

| Mục | Nội dung |
|---|---|
| **Mã** | UC-01 |
| **Tác nhân** | Người dùng |
| **Mô tả** | Người dùng xem số liệu môi trường hiện tại và diễn biến theo thời gian |
| **Tiền điều kiện** | Backend đang chạy; đã có ít nhất một bản ghi cảm biến |
| **Hậu điều kiện** | Dashboard hiển thị số liệu mới nhất và tự cập nhật |

**Luồng chính:**
1. Người dùng truy cập trang Dashboard.
2. Hệ thống gọi API lấy số liệu mới nhất và N bản ghi gần nhất.
3. Hệ thống hiển thị 3 thẻ số liệu: **Nhiệt độ (°C)**, **Độ ẩm (%)**, **Ánh sáng (lux)**.
4. Hệ thống hiển thị biểu đồ đường diễn biến nhiệt độ / độ ẩm / ánh sáng theo thời gian.
5. Hệ thống mở kết nối WebSocket; mỗi khi có số liệu mới, các thẻ và biểu đồ tự cập nhật mà không cần tải lại trang.

**Luồng thay thế:**
- **A1 — Chưa có dữ liệu:** hiển thị `--` trên thẻ và thông báo "Chưa có dữ liệu".
- **A2 — Mất kết nối WebSocket:** hiển thị chỉ báo "Mất kết nối", tự động thử kết nối lại sau mỗi 5 giây.
- **A3 — Thiết bị IoT offline quá 30 giây:** hiển thị nhãn "Thiết bị ngoại tuyến".

**Yêu cầu liên quan:** FR-01, FR-02, FR-03, FR-12

---

#### UC-02 — Điều khiển bật/tắt thiết bị

| Mục | Nội dung |
|---|---|
| **Mã** | UC-02 |
| **Tác nhân** | Người dùng (chính), Thiết bị IoT, MQTT Broker (phụ) |
| **Mô tả** | Người dùng bật/tắt đèn hoặc quạt từ giao diện web |
| **Tiền điều kiện** | Broker đang chạy; thiết bị IoT đã kết nối và subscribe topic `device_control` |
| **Hậu điều kiện** | Trạng thái thiết bị thay đổi, một bản ghi được lưu vào lịch sử thao tác |

**Luồng chính:**
1. Người dùng bấm công tắc (toggle) của thiết bị trên Dashboard.
2. Frontend gửi yêu cầu điều khiển tới Backend qua HTTP, **kèm mã người thao tác** (`user_id`, tùy chọn).
3. Backend ghi một bản ghi vào bảng lịch sử thao tác với trạng thái `PENDING`, **lưu kèm người thao tác** (FR-18).
4. Backend publish lệnh lên topic `device_control`.
5. Broker chuyển tiếp lệnh tới thiết bị IoT.
6. Thiết bị IoT thay đổi mức logic chân GPIO tương ứng (HIGH = bật, LOW = tắt).
7. Thiết bị IoT publish xác nhận lên topic `device_respond`.
8. Backend nhận xác nhận, cập nhật bản ghi lịch sử sang trạng thái `SUCCESS`.
9. Backend đẩy trạng thái mới tới Frontend qua WebSocket.
10. Frontend cập nhật giao diện công tắc và hiển thị thông báo thành công.

**Luồng thay thế:**
- **A1 — Không nhận được xác nhận trong 5 giây:** Backend cập nhật trạng thái `FAILED`, đẩy thông báo lỗi về Frontend; Frontend trả công tắc về trạng thái cũ.
- **A2 — Broker không kết nối được:** Backend trả về lỗi ngay, không ghi lệnh, Frontend báo "Không kết nối được tới hệ thống điều khiển".
- **A3 — Người dùng bấm liên tục:** hệ thống khóa công tắc trong lúc chờ phản hồi (trạng thái `PENDING`). Nếu yêu cầu trùng vẫn tới được Backend (ví dụ người dùng mở hai tab trình duyệt), Backend từ chối bằng lỗi `409` và không ghi thêm bản ghi lịch sử.
- **A4 — Yêu cầu không kèm `user_id`:** hệ thống vẫn thực hiện lệnh bình thường và ghi bản ghi lịch sử với trường người thao tác để trống. Đây là trường hợp của lệnh phát bằng `mosquitto_pub` hoặc script kiểm thử.

**Yêu cầu liên quan:** FR-04, FR-05, FR-06, FR-09, FR-18

> *Đây là use case trọng tâm — sequence diagram của nó chính là sơ đồ giảng viên vẽ ở ảnh 9.*

---

#### UC-03 — Xem lịch sử số liệu cảm biến

| Mục | Nội dung |
|---|---|
| **Mã** | UC-03 |
| **Tác nhân** | Người dùng |
| **Mô tả** | Xem toàn bộ số liệu cảm biến đã ghi nhận dưới dạng bảng |
| **Tiền điều kiện** | Backend đang chạy |
| **Hậu điều kiện** | Không thay đổi trạng thái hệ thống |

**Luồng chính:**
1. Người dùng chọn menu "Data Sensor".
2. Hệ thống gọi API lấy danh sách bản ghi (mặc định trang 1, 10 bản ghi/trang, sắp xếp thời gian giảm dần).
3. Hệ thống hiển thị bảng với các cột: **ID · Mã cảm biến · Cảm biến · Giá trị · Đơn vị · Thời gian**. Mỗi dòng là **một số đo của một cảm biến**; ba dòng của cùng một chu kỳ mang cùng mốc thời gian (FR-17).
4. Hệ thống hiển thị thanh phân trang ở góc dưới bên phải.

**Luồng thay thế:**
- **A1 — Không có bản ghi nào:** hiển thị "Không có dữ liệu".

**Yêu cầu liên quan:** FR-07, FR-10, FR-11, FR-17

---

#### UC-04 — Tìm kiếm, lọc, sắp xếp, phân trang dữ liệu

| Mục | Nội dung |
|---|---|
| **Mã** | UC-04 |
| **Tác nhân** | Người dùng |
| **Mô tả** | Thu hẹp và sắp xếp dữ liệu trong các bảng lịch sử |
| **Quan hệ** | `«extend»` UC-03 và UC-05 (xem `02-UseCase.md` §4.1) |

**Luồng chính:**
1. Người dùng nhập từ khóa vào ô tìm kiếm và/hoặc chọn một **cảm biến** từ dropdown *(màn hình Data Sensor)*, hoặc chọn thiết bị / trạng thái / hành động / người thao tác *(màn hình Action History)*.
2. Người dùng có thể chọn thêm khoảng thời gian (từ ngày — đến ngày), và **khoảng giá trị** nếu đã chọn một cảm biến.
3. Hệ thống gọi API với các tham số lọc tương ứng.
4. Hệ thống trả về và hiển thị dữ liệu đã lọc, đặt lại về trang 1.
5. Người dùng bấm vào tiêu đề cột để sắp xếp tăng/giảm dần.
6. Người dùng chuyển trang bằng thanh phân trang.

**Luồng thay thế:**
- **A1 — Không có kết quả khớp:** hiển thị "Không tìm thấy kết quả phù hợp".
- **A2 — Chưa chọn cảm biến mà đã nhập khoảng giá trị:** hai ô Từ/Đến ở trạng thái vô hiệu nên không nhập được. Lý do: các đại lượng có đơn vị khác nhau, so sánh "giá trị ≥ 28" chung cho cả nhiệt độ lẫn ánh sáng là vô nghĩa.
- **A3 — Đầu khoảng lớn hơn cuối khoảng:** hệ thống báo lỗi và tô đỏ đúng cặp ô nhập bị sai.

**Yêu cầu liên quan:** FR-10, FR-11

---

#### UC-05 — Xem lịch sử thao tác thiết bị

| Mục | Nội dung |
|---|---|
| **Mã** | UC-05 |
| **Tác nhân** | Người dùng |
| **Mô tả** | Xem toàn bộ các lần bật/tắt thiết bị đã thực hiện |
| **Tiền điều kiện** | Backend đang chạy |

**Luồng chính:**
1. Người dùng chọn menu "Action History".
2. Hệ thống gọi API lấy danh sách bản ghi thao tác.
3. Hệ thống hiển thị bảng với các cột: **ID · Thiết bị · Hành động (ON/OFF) · Người thao tác · Trạng thái (SUCCESS/FAILED/PENDING) · Độ trễ · Thời gian**.
4. Người dùng có thể tìm kiếm / lọc / phân trang (theo UC-04).

**Luồng thay thế:**
- **A1 — Bản ghi không xác định được người thao tác:** cột "Người thao tác" hiển thị dấu `—` (FR-18, xem §4.1 màn hình 3).

**Yêu cầu liên quan:** FR-08, FR-10, FR-11, FR-18

---

#### UC-06 — Xem trang Profile

| Mục | Nội dung |
|---|---|
| **Mã** | UC-06 |
| **Tác nhân** | Người dùng (giảng viên chấm bài) |
| **Mô tả** | Xem thông tin nhóm và các liên kết bàn giao |

**Luồng chính:**
1. Người dùng chọn menu "Profile".
2. Hệ thống hiển thị ảnh đại diện, họ tên, MSSV, lớp, tên đề tài.
3. Hệ thống hiển thị các liên kết: **GitHub repository**, **Báo cáo PDF**, **Figma design**, **API docs (Postman/Swagger)**.

**Yêu cầu liên quan:** FR-13

---

#### UC-07 — Thu thập và truyền số liệu cảm biến *(tự động)*

| Mục | Nội dung |
|---|---|
| **Mã** | UC-07 |
| **Tác nhân** | Thiết bị IoT (ESP8266) |
| **Mô tả** | Thiết bị tự động đọc cảm biến và gửi số liệu về hệ thống theo chu kỳ |
| **Kích hoạt** | Bộ định thời trên thiết bị, mỗi 2 giây |

**Luồng chính:**
1. ESP8266 đọc nhiệt độ và độ ẩm từ DHT11.
2. ESP8266 đọc giá trị analog từ quang trở và quy đổi ra lux.
3. ESP8266 đóng gói dữ liệu thành chuỗi JSON.
4. ESP8266 publish lên topic `data_sensors` với QoS 0.
5. Backend (đang subscribe topic này) nhận được message.
6. Backend **tra danh mục cảm biến** để tìm cảm biến tương ứng với từng trường số đo, dựa trên cặp *(mã bo mạch, đại lượng đo)*.
7. Backend kiểm tra từng số đo với ngưỡng hợp lệ **riêng của cảm biến đó**, rồi ghi **mỗi số đo thành một bản ghi**. Cả nhóm mang **cùng một mốc thời gian** và được ghi trong một giao dịch (FR-17).
8. Backend đẩy dữ liệu tới Frontend qua WebSocket dưới dạng **một sự kiện cho cả chu kỳ**.

**Luồng thay thế:**
- **A1 — Đọc cảm biến thất bại (giá trị `NaN`):** bỏ qua chu kỳ này, không publish, ghi log lỗi.
- **A2 — Chỉ đọc được một phần cảm biến:** vẫn publish phần đọc được; Backend ghi bản ghi cho các cảm biến có số đo, **không ghi gì** cho cảm biến bị lỗi. Trên biểu đồ, đường của cảm biến đó đứt một đoạn tại mốc tương ứng.
- **A3 — Mất kết nối WiFi hoặc Broker:** ESP8266 tự động thử kết nối lại mỗi 5 giây; dữ liệu trong lúc mất kết nối bị bỏ qua.
- **A4 — Một số đo vượt ngưỡng hợp lệ:** Backend loại bỏ **đúng số đo đó** và ghi log cảnh báo kèm message gốc; các số đo còn lại trong cùng chu kỳ vẫn được lưu bình thường.

> **A4 đổi hành vi so với bản 0.4** *(khi đó ghi là "loại bỏ cả bản ghi")*. Ở mô hình cũ, ba số đo nằm chung một dòng nên một giá trị hỏng làm mất cả chu kỳ. Nay mỗi số đo là một dòng độc lập, nên chỉ cần bỏ dòng hỏng — nhất quán với luồng A2 vốn đã cho phép ghi một phần.

**Yêu cầu liên quan:** FR-01, FR-07, FR-12, FR-14, FR-17

---

### 3.3 Bảng yêu cầu chức năng

| Mã | Yêu cầu | UC liên quan | Ưu tiên |
|---|---|---|---|
| FR-01 | Hệ thống phải tiếp nhận số liệu nhiệt độ, độ ẩm, ánh sáng từ thiết bị IoT qua topic `data_sensors` | UC-01, UC-07 | Bắt buộc |
| FR-02 | Dashboard phải hiển thị 3 thẻ số liệu tức thời kèm đơn vị (°C, %, lux) | UC-01 | Bắt buộc |
| FR-03 | Dashboard phải hiển thị biểu đồ đường diễn biến số liệu theo thời gian | UC-01 | Bắt buộc |
| FR-04 | Hệ thống phải cho phép bật/tắt từng thiết bị độc lập từ giao diện | UC-02 | Bắt buộc |
| FR-05 | Hệ thống phải publish lệnh điều khiển lên topic `device_control` | UC-02 | Bắt buộc |
| FR-06 | Hệ thống phải cập nhật trạng thái thiết bị dựa trên phản hồi từ topic `device_respond` | UC-02 | Bắt buộc |
| FR-07 | Hệ thống phải lưu mọi bản ghi cảm biến hợp lệ vào CSDL kèm mốc thời gian | UC-03, UC-07 | Bắt buộc |
| FR-08 | Hệ thống phải lưu mọi thao tác điều khiển vào lịch sử kèm trạng thái thực thi | UC-02, UC-05 | Bắt buộc |
| FR-09 | Hệ thống phải đánh dấu `FAILED` nếu không nhận phản hồi trong 5 giây | UC-02 | Bắt buộc |
| FR-10 | Các bảng dữ liệu phải hỗ trợ tìm kiếm theo từ khóa và lọc theo cảm biến / khoảng giá trị / khoảng thời gian | UC-04 | Bắt buộc |
| FR-11 | Các bảng dữ liệu phải hỗ trợ sắp xếp theo cột và phân trang | UC-04 | Bắt buộc |
| FR-12 | Giao diện phải cập nhật theo thời gian thực qua WebSocket, không cần tải lại trang | UC-01 | Bắt buộc |
| FR-13 | Hệ thống phải có trang Profile chứa liên kết GitHub, PDF, Figma, API docs | UC-06 | Bắt buộc |
| FR-14 | Hệ thống phải loại bỏ dữ liệu cảm biến nằm ngoài ngưỡng hợp lệ | UC-07 | Nên có |
| FR-15 | Hệ thống nên hiển thị trạng thái kết nối của thiết bị IoT (online/offline) | UC-01 | Nên có |
| FR-16 | Hệ thống nên cho phép mở rộng thêm cảm biến và thiết bị điều khiển mà không sửa mã nguồn lõi | UC-07 | Tùy chọn |
| FR-17 | Hệ thống phải quản lý danh mục cảm biến; mỗi cảm biến có mã, tên, đại lượng đo, đơn vị và ngưỡng hợp lệ riêng | UC-03, UC-07 | Bắt buộc |
| FR-18 | Hệ thống phải ghi nhận người thao tác cho mỗi lệnh điều khiển và hiển thị ở màn hình lịch sử | UC-02, UC-05 | Bắt buộc |

**Về FR-17 và FR-18** *(bổ sung ở bản 0.5)*: hai yêu cầu này phát sinh sau buổi báo cáo ngày 20/08/2026, khi giảng viên yêu cầu **lưu số liệu theo từng cảm biến** thay vì lưu cả cụm ba số đo trên một bản ghi, và **ghi lại ai đã thao tác** vào thiết bị. Cấu trúc lưu trữ tương ứng đặc tả ở §6; thiết kế vật lý đầy đủ ở `04-Database.md` bản 2.0.

---

## 4. YÊU CẦU GIAO DIỆN NGOÀI

### 4.1 Giao diện người dùng

Bố cục chung: **thanh điều hướng dọc bên trái (sidebar)** + **vùng nội dung bên phải**. Sidebar gồm 4 mục: Dashboard · Data Sensor · Action History · Profile.

**Màn hình 1 — Dashboard**
```
┌────────┬──────────────────────────────────────────────────┐
│        │  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  Dash  │  │  20 °C  │  │  80 %   │  │ 100 lux │           │
│  board │  │Nhiệt độ │  │ Độ ẩm   │  │ Ánh sáng│           │
│        │  └─────────┘  └─────────┘  └─────────┘           │
│  Data  │  ┌──────────────────────────┐ ┌────────────────┐ │
│ Sensor │  │                          │ │ 💡 Đèn   [ ON] │ │
│        │  │   Biểu đồ đường realtime │ │                │ │
│ Action │  │   (temp / hum / lux)     │ │ 🌀 Quạt  [OFF] │ │
│ History│  │                          │ │                │ │
│        │  └──────────────────────────┘ └────────────────┘ │
│Profile │                                                  │
└────────┴──────────────────────────────────────────────────┘
```

**Màn hình 2 — Data Sensor**
```
┌────────┬────────────────────────────────────────────────────────────────┐
│        │ [🔍 Tìm kiếm][Cảm biến ▾][Từ][Đến][Từ ngày][Đến ngày][Xóa lọc] │
│  ...   │  ┌──────┬──────────────┬─────────────────┬───────┬─────┬──────┐│
│        │  │  ID  │ Mã cảm biến  │ Cảm biến        │Giá trị│Đơn vị│ Thời ││
│        │  ├──────┼──────────────┼─────────────────┼───────┼─────┼──────┤│
│        │  │36132 │ room01_temp  │ Nhiệt độ phòng  │ 28.5  │ °C  │30:02 ││
│        │  │36133 │ room01_humi  │ Độ ẩm phòng     │ 72.0  │  %  │30:02 ││
│        │  │36134 │ room01_lux   │ Ánh sáng phòng  │ 350   │ lux │30:02 ││
│        │  │ ...  │     ...      │      ...        │  ...  │ ... │ ...  ││
│        │  └──────┴──────────────┴─────────────────┴───────┴─────┴──────┘│
│        │                                          ◄ 1 2 3 4 5 ►         │
└────────┴────────────────────────────────────────────────────────────────┘
```
> **Mỗi dòng là một số đo của một cảm biến**, không phải một cụm ba số đo (FR-17). Ba dòng đầu ví dụ trên cùng thuộc **một chu kỳ** `17:30:02` nên mang cùng mốc thời gian, và hiện theo đúng thứ tự danh mục *Nhiệt độ → Độ ẩm → Ánh sáng*.
>
> Ô **tìm kiếm** tác động tới mã và tên cảm biến — hai cột chuỗi của bảng. Dropdown **Cảm biến** chọn một cảm biến để lọc. Hai ô **Từ / Đến** là khoảng giá trị, và **chỉ có hiệu lực khi đã chọn một cảm biến** — lọc "giá trị từ 28 đến 30" trên cả ba đại lượng là vô nghĩa vì 28 lux và 28 °C không so sánh được với nhau. Giao diện để hai ô này ở trạng thái vô hiệu cho tới khi người dùng chọn cảm biến.
>
> Dòng chú thích *"bản ghi thiếu số đo bị loại khỏi kết quả"* của bản 0.3 **đã được bỏ**: cột giá trị nay là `NOT NULL`, cảm biến không đọc được thì đơn giản là không có dòng, nên hiện tượng đó không còn.

**Màn hình 3 — Action History**: bố cục tương tự, cột `ID · Thiết bị · Hành động · Người thao tác · Trạng thái · Độ trễ · Thời gian`; bộ lọc gồm ô tìm kiếm, bốn dropdown (Thiết bị / Trạng thái / Hành động / Người thao tác) và khoảng ngày.

- Cột **Thiết bị** hiển thị cả mã lẫn tên — `room01_lamp · Đèn phòng` — vì mã là thứ đi trong payload MQTT và xuất hiện trong log, còn tên là thứ người dùng đọc.
- Cột **Người thao tác** hiển thị `full_name` của người đã gửi lệnh (FR-18). Bản ghi không xác định được người thao tác — lệnh phát bằng `mosquitto_pub` khi kiểm thử, hoặc dữ liệu khởi tạo — hiển thị dấu `—`, **không** ghi "Hệ thống" hay "Ẩn danh" vì hai chữ đó gợi ý rằng có một tài khoản mang tên như vậy.
- Cột **Độ trễ** là `latency_ms` do API tính từ `responded_at − created_at`, dùng làm bằng chứng của NFR-01 ngay trên màn hình.

**Màn hình 4 — Profile**: ảnh đại diện, thông tin nhóm, 4 nút liên kết.

> Bản thiết kế chi tiết (màu sắc, khoảng cách, typography) sẽ được hoàn thiện trên **Figma** ở bước B3.

### 4.2 Giao diện phần cứng

Bo mạch: `esp8266_room01`.

| Chân ESP8266 | Kết nối | Mã nghiệp vụ | Chế độ |
|---|---|---|---|
| `D4` (GPIO2) | DHT11 — Data | `room01_temp`, `room01_humi` | INPUT (thư viện DHT) |
| `A0` | LM393 — AO (quang trở) | `room01_lux` | ANALOG INPUT |
| `D5` (GPIO14) | LED 1 (Đèn) + trở 220Ω | `room01_lamp` | OUTPUT |
| `D6` (GPIO12) | LED 2 (Quạt) + trở 220Ω | `room01_fan` | OUTPUT |
| `3V3` | VCC của DHT11, LM393 | — | — |
| `GND` | GND chung | — | — |

> **Một chân `D4` mang hai mã cảm biến** vì DHT11 là một linh kiện đo **hai đại lượng** — nhiệt độ và độ ẩm — trên cùng một dây dữ liệu. Trong danh mục cảm biến chúng là hai bản ghi riêng, vì người dùng lọc và xem biểu đồ theo từng đại lượng chứ không theo linh kiện.
>
> **Quy ước đặt mã** `<vị trí>_<vai trò>` (`04-Database.md` §2.7): nhìn mã là biết thiết bị thuộc phòng nào, nên khi lắp thêm bo mạch cho phòng thứ hai thì có `room02_lamp`, `room02_temp`… và **được phép dùng lại chân `D5`/`D6`** — chân GPIO chỉ duy nhất trong phạm vi một bo mạch.

### 4.3 Giao diện truyền thông — MQTT

**Cấu hình broker**

| Tham số | Giá trị |
|---|---|
| Host | `localhost` (hoặc IP LAN của laptop) |
| Port | `1883` |
| Xác thực | username / password |
| QoS | 0 cho `data_sensors`, 1 cho `device_control` và `device_respond` |
| Client ID | `esp8266_room01` (thiết bị) · `backend_worker` (tiến trình MQTT worker) · `backend_api_<ngẫu nhiên>` (tiến trình ASGI, mỗi lần publish một client mới) |

**Topic 1 — `data_sensors`** *(ESP → Backend)*
```json
{
  "device_id": "esp8266_room01",
  "temperature": 28.5,
  "humidity": 72.0,
  "light": 350,
  "timestamp": "2026-08-13T10:30:02Z"
}
```

**Topic 2 — `device_control`** *(Backend → ESP)*
```json
{
  "request_id": "3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
  "device": "room01_lamp",
  "action": "ON"
}
```

**Topic 3 — `device_respond`** *(ESP → Backend)*
```json
{
  "request_id": "3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
  "device": "room01_lamp",
  "state": "ON",
  "status": "SUCCESS"
}
```

> `request_id` dùng để ghép cặp lệnh và phản hồi, phục vụ việc cập nhật đúng bản ghi lịch sử. Giá trị là một **UUID phiên bản 4 dạng chuỗi, dài 36 ký tự**, do backend sinh bằng `uuid4()`; firmware phải trả lại nguyên vẹn chuỗi này trong `device_respond`. Toàn bộ payload khoảng 110 byte. Thư viện MQTT của firmware (`arduino-mqtt`) mặc định chỉ cấp bộ đệm **128 byte**, nên phải khai báo tường minh `MQTTClient client(256);` để có dư địa.

**Kiểm thử bằng dòng lệnh**
```bash
# Lắng nghe số liệu cảm biến
mosquitto_sub -h localhost -p 1883 -t "data_sensors" -u <user> -P <pass>

# Giả lập gửi số liệu
mosquitto_pub -h localhost -p 1883 -t "data_sensors" -u <user> -P <pass> \
  -m '{"device_id":"esp8266_room01","temperature":20,"humidity":80,"light":100}'

# Giả lập gửi lệnh điều khiển
mosquitto_pub -h localhost -p 1883 -t "device_control" -u <user> -P <pass> \
  -m '{"request_id":"test01","device":"room01_lamp","action":"ON"}'
```

### 4.4 Giao diện phần mềm — API (tóm tắt)

| Phương thức | Đường dẫn | Chức năng | UC |
|---|---|---|---|
| `GET` | `/api/sensors/devices` | **Danh mục cảm biến** (mã, tên, đại lượng, đơn vị) | UC-01, UC-03 |
| `GET` | `/api/sensors/latest` | Số đo mới nhất **của từng cảm biến** — trả về một mảng | UC-01 |
| `GET` | `/api/sensors/chart?limit=20` | N chu kỳ gần nhất cho biểu đồ | UC-01 |
| `GET` | `/api/sensors` | Danh sách số đo (search, filter, sort, page) | UC-03, UC-04 |
| `GET` | `/api/devices` | Danh sách thiết bị và trạng thái hiện tại | UC-01 |
| `POST` | `/api/devices/{id}/control` | Gửi lệnh bật/tắt thiết bị, kèm `user_id` **tùy chọn** | UC-02 |
| `GET` | `/api/actions` | Lịch sử thao tác (search, filter, sort, page) | UC-05, UC-04 |
| `GET` | `/api/profile` | Thông tin nhóm và các liên kết | UC-06 |
| `WS` | `/ws/realtime/` — sự kiện `sensor.data`, `device.state` | Kênh đẩy dữ liệu realtime | UC-01, UC-02 |

Quy ước áp dụng cho toàn bộ API:
- Tham số truy vấn theo chuẩn Django REST Framework: `?search=`, `?ordering=-recorded_at`, `?page=1&page_size=10`, và các bộ lọc theo trường (`?recorded_at__gte=`, `?recorded_at__lte=`, `?sensor=room01_temp`, `?value__gte=`, `?value__lte=`).
- Response phân trang trả về cấu trúc `{ "count", "next", "previous", "results" }` (`PageNumberPagination` mặc định của DRF).
- Tên trường trong JSON giữ nguyên `snake_case`.
- Tài liệu OpenAPI sinh tự động bằng `drf-spectacular`, truy cập tại `/api/schema/swagger-ui/`.

> Đặc tả đầy đủ (request/response schema, mã lỗi, ví dụ) nằm ở tài liệu **`05-API.md`** và Swagger/Postman.

---

## 5. YÊU CẦU PHI CHỨC NĂNG

| Mã | Loại | Yêu cầu |
|---|---|---|
| NFR-01 | Hiệu năng | Độ trễ từ lúc bấm nút tới lúc thiết bị đổi trạng thái ≤ **2 giây** |
| NFR-02 | Hiệu năng | Độ trễ từ lúc ESP publish tới lúc giao diện cập nhật ≤ **1 giây** |
| NFR-03 | Hiệu năng | API trả kết quả trong ≤ **500 ms** với bảng ≤ 100.000 bản ghi |
| NFR-04 | Hiệu năng | Chu kỳ gửi số liệu cảm biến: **2 giây/lần** (cấu hình được) |
| NFR-05 | Độ tin cậy | ESP8266 tự động kết nối lại WiFi và Broker khi mất kết nối, chu kỳ thử lại 5 giây |
| NFR-06 | Độ tin cậy | Không mất bản ghi lịch sử thao tác kể cả khi lệnh thất bại (ghi trạng thái `FAILED`) |
| NFR-07 | Khả dụng | Giao diện hoạt động tốt trên Chrome/Edge phiên bản mới, độ phân giải ≥ 1366×768 |
| NFR-08 | Khả dụng | Mọi thao tác chính thực hiện được trong ≤ 3 lần bấm chuột |
| NFR-09 | Bảo mật | MQTT Broker bắt buộc bật xác thực username/password, tắt anonymous |
| NFR-10 | Bảo mật | Backend kiểm tra hợp lệ toàn bộ dữ liệu đầu vào từ MQTT và HTTP |
| NFR-11 | Bảo trì | Toàn bộ cấu hình (WiFi SSID, broker host/port, tài khoản, DB, Redis) tách khỏi mã nguồn — `.env` cho backend, `config.h` cho firmware |
| NFR-12 | Bảo trì | Mã nguồn tách lớp rõ ràng: firmware / backend / frontend; backend chia thành các Django app độc lập (`users`, `sensors`, `devices`, `realtime`, `mqtt`) |
| NFR-13 | Khả mở rộng | Thêm **cảm biến** mới chỉ cần thêm bản ghi trong danh mục `sensor_device`; thêm **thiết bị** mới chỉ cần thêm bản ghi trong `devices` và ánh xạ chân GPIO. Cả hai đều không phải sửa schema |
| NFR-15 | Bảo trì | Mọi thay đổi schema thực hiện qua Django migration, không sửa CSDL thủ công |
| NFR-16 | Độ tin cậy | MQTT worker phải tự kết nối lại broker khi mất kết nối và ghi log mọi message không hợp lệ |
| NFR-14 | Ràng buộc dữ liệu | Mỗi cảm biến có ngưỡng hợp lệ riêng, lưu ở hai cột `min_value` / `max_value` của danh mục. Giá trị hiện hành: nhiệt độ −10 → 60 °C · độ ẩm 0 → 100 % · ánh sáng 0 → 2000 lux |

> **Về nơi kiểm tra NFR-14** *(đổi ở bản 0.5)*: ngưỡng hợp lệ nay là **dữ liệu cấu hình** nằm trong danh mục cảm biến, không còn ghi cứng trong mã. Ưu điểm là hiệu chuẩn lại quang trở ở tuần 2 chỉ cần sửa một dòng dữ liệu thay vì chạy migration. Đổi lại, ràng buộc `CHECK` của PostgreSQL **không tham chiếu được sang bảng khác**, nên việc kiểm ngưỡng do MQTT worker đảm nhiệm; cơ sở dữ liệu chỉ giữ một ràng buộc nới rộng để chặn dữ liệu rác hiển nhiên. Phân tích đầy đủ ở `04-Database.md` §2.4.

---

## 6. MÔ HÌNH DỮ LIỆU (MỨC KHÁI NIỆM)

Mô hình gồm **5 thực thể**. Hai thực thể danh mục (`sensor_device`, `devices`) mô tả *cái gì đang tồn tại*; hai thực thể lịch sử (`sensor_data`, `action_history`) ghi lại *chuyện gì đã xảy ra*; `users` cho biết *ai đã làm*.

```
┌─────────────────────┐                    ┌─────────────────────┐
│    sensor_device    │                    │      devices        │
├─────────────────────┤                    ├─────────────────────┤
│ id           PK     │                    │ id           PK     │
│ code         UNIQUE │  "room01_temp"     │ code         UNIQUE │  "room01_lamp"
│ name                │  "Nhiệt độ phòng"  │ name                │  "Đèn phòng"
│ metric_type         │  TEMPERATURE/…     │ device_type         │  LIGHT / FAN
│ unit                │  "°C"              │ node_id             │  "esp8266_room01"
│ node_id             │  "esp8266_room01"  │ gpio_pin            │  "D5"
│ min_value/max_value │  ngưỡng hợp lệ     │ current_state       │  ON / OFF
└──────────┬──────────┘                    └──────────┬──────────┘
           │ 1                                        │ 1
           │                                          │
           │ N                                        │ N
┌──────────▼──────────┐                    ┌──────────▼──────────┐
│    sensor_data      │                    │   action_history    │
├─────────────────────┤                    ├─────────────────────┤
│ id           PK     │                    │ id           PK     │
│ sensor_id    FK     │                    │ device_id    FK     │
│ value        FLOAT  │  MỘT số đo         │ user_id      FK     │  NULL được
│ recorded_at  DATETIME│                   │ request_id   UNIQUE │
└─────────────────────┘                    │ action              │  ON / OFF
                                           │ status              │  PENDING/SUCCESS/FAILED
   UNIQUE (sensor_id, recorded_at)         │ created_at          │
                                           │ responded_at        │
                                           └──────────▲──────────┘
                                                      │ N
                                                      │
                                                      │ 1
                                           ┌──────────┴──────────┐
                                           │       users         │
                                           ├─────────────────────┤
                                           │ id           PK     │
                                           │ username     UNIQUE │
                                           │ password            │  đã băm
                                           │ full_name           │  "Lưu Đức Anh"
                                           │ role                │  ADMIN/OPERATOR/VIEWER
                                           └─────────────────────┘
```

**Ba điểm cần nêu rõ về mô hình này:**

1. **Mỗi bản ghi `sensor_data` là một số đo của một cảm biến** (FR-17), không phải một cụm ba số đo. Một chu kỳ lấy mẫu 2 giây sinh ra **ba bản ghi** mang **cùng một** `recorded_at` — ràng buộc `UNIQUE (sensor_id, recorded_at)` bảo đảm một cảm biến không thể có hai số đo tại cùng một thời điểm. Hệ quả: cảm biến nào không đọc được thì **không có bản ghi**, thay vì có bản ghi với giá trị rỗng như mô hình cũ.
2. **`users` không bắt buộc.** `action_history.user_id` cho phép rỗng vì có những lệnh không do người dùng giao diện phát ra — lệnh thử bằng `mosquitto_pub`, dữ liệu khởi tạo, script kiểm thử. Phạm vi hiện tại **chưa có màn hình đăng nhập** (§8.2), người thao tác được xác định qua trường `user_id` tùy chọn trong lời gọi API điều khiển.
3. **Khóa nghiệp vụ `code` tách khỏi khóa kỹ thuật `id`.** `id` do CSDL sinh, dùng cho khóa ngoại và URL. `code` do người đặt theo quy ước `<vị trí>_<vai trò>`, dùng trong payload MQTT vì firmware cần một chuỗi cố định để so sánh.

Ánh xạ sang Django (app · model · bảng vật lý):

| App | Model | Bảng PostgreSQL |
|---|---|---|
| `users` | `User` *(kế thừa `AbstractUser`)* | `users_user` |
| `sensors` | `SensorDevice` | `sensors_sensordevice` |
| `sensors` | `SensorData` | `sensors_sensordata` |
| `devices` | `Device` | `devices_device` |
| `devices` | `ActionHistory` | `devices_actionhistory` |

Khóa chính `id` do Django tự sinh (`BigAutoField`). Các trường liệt kê (`action`, `status`, `metric_type`, `role`) khai báo bằng `TextChoices` để ràng buộc giá trị ở tầng ứng dụng. Cần đánh index trên `SensorData.recorded_at` và `ActionHistory.created_at` để phục vụ sắp xếp và lọc theo thời gian (NFR-03), cùng ràng buộc `unique` trên `ActionHistory.request_id`.

> **Lưu ý khi cài đặt:** phải đặt `AUTH_USER_MODEL = "users.User"` trong `settings.py` **trước lần `migrate` đầu tiên**. Django ghi khóa ngoại tới bảng người dùng vào các bảng hệ thống ngay từ migration đầu, nên đổi về sau buộc phải xóa và tạo lại cơ sở dữ liệu.

> ERD chi tiết kèm kiểu dữ liệu, ràng buộc, index và mã `models.py` nằm ở tài liệu **`04-Database.md`** bản 2.0 — đó là bản có hiệu lực cho mọi chi tiết vật lý. Sơ đồ trên là **mức khái niệm**, cố ý lược bớt các cột phụ (`is_active`, `created_at`, `updated_at`, `error_message`, `hardware_model`).

---

## 7. TIÊU CHÍ NGHIỆM THU (UAT)

| # | Kịch bản kiểm thử | Kết quả mong đợi | UC |
|---|---|---|---|
| T-01 | Bật hệ thống, quan sát Dashboard | 3 thẻ hiển thị số liệu và tự cập nhật mỗi 2 giây | UC-01 |
| T-02 | Hà hơi vào cảm biến DHT11 | Giá trị độ ẩm trên Dashboard tăng rõ rệt trong ≤ 2 giây | UC-01 |
| T-03 | Che quang trở bằng tay | Giá trị ánh sáng giảm rõ rệt trong ≤ 2 giây | UC-01 |
| T-04 | Bấm bật "Đèn" trên giao diện | LED 1 sáng trong ≤ 2 giây, công tắc chuyển sang ON | UC-02 |
| T-05 | Bấm tắt "Đèn" | LED 1 tắt, công tắc chuyển sang OFF | UC-02 |
| T-06 | Bật/tắt "Quạt" | Chỉ LED 2 đổi trạng thái, LED 1 không bị ảnh hưởng | UC-02 |
| T-07 | Rút nguồn ESP8266 rồi bấm bật đèn | Sau 5–6 giây hiện thông báo lỗi, lịch sử ghi trạng thái `FAILED` | UC-02 |
| T-08 | Mở trang Data Sensor | Bảng hiển thị đủ 6 cột (ID, Mã cảm biến, Cảm biến, Giá trị, Đơn vị, Thời gian), phân trang hoạt động | UC-03 |
| T-08b | Quan sát ba dòng liên tiếp của cùng một chu kỳ | Ba dòng mang **cùng một mốc thời gian** và hiện theo thứ tự Nhiệt độ → Độ ẩm → Ánh sáng | UC-03, FR-17 |
| T-09 | Tìm kiếm số liệu theo khoảng thời gian | Chỉ hiển thị bản ghi trong khoảng đã chọn | UC-04 |
| T-10 | Chọn cảm biến "Nhiệt độ phòng" rồi bấm tiêu đề cột "Giá trị" | Dữ liệu sắp xếp tăng dần, bấm lần nữa thì giảm dần | UC-04 |
| T-10b | Chưa chọn cảm biến, thử nhập khoảng giá trị | Hai ô Từ/Đến ở trạng thái vô hiệu, không nhập được | UC-04 |
| T-11 | Mở Action History sau khi bật/tắt vài lần | Mỗi thao tác có đúng một bản ghi với trạng thái `SUCCESS` | UC-05 |
| T-11b | Xem cột "Người thao tác" của các bản ghi vừa tạo | Hiển thị đúng tên người đã gửi lệnh; bản ghi tạo bằng `mosquitto_pub` hiển thị `—` | UC-05, FR-18 |
| T-12 | Mở trang Profile | 4 liên kết đều mở đúng trang đích | UC-06 |
| T-13 | Chạy `mosquitto_sub -t "data_sensors"` trên terminal | Thấy chuỗi JSON số liệu xuất hiện mỗi 2 giây | UC-07 |
| T-14 | Chạy `mosquitto_pub -t "device_control"` gửi lệnh ON | LED sáng, `device_respond` trả về `SUCCESS` | UC-02 |
| T-15 | Mở đồng thời 2 tab trình duyệt, bật đèn ở tab 1 | Tab 2 tự cập nhật trạng thái mà không cần tải lại | UC-01, FR-12 |
| T-16 | Tắt tiến trình `mqtt_worker`, mở lại Dashboard | Trang vẫn tải được dữ liệu lịch sử, nhưng hiển thị "Thiết bị ngoại tuyến" và số liệu không cập nhật | §2.6 |
| T-17 | Mở `/api/schema/swagger-ui/` | Swagger UI liệt kê đầy đủ **8** endpoint REST, gọi thử được trực tiếp | B4 |
| T-18 | Thêm một dòng vào danh mục cảm biến rồi khởi động lại `mqtt_worker` | Dashboard tự hiện thêm một thẻ số liệu mà không phải sửa mã nguồn | FR-16, FR-17 |

---

## 8. PHỤ LỤC

### 8.1 Lịch sử phiên bản

| Phiên bản | Ngày | Người sửa | Nội dung |
|---|---|---|---|
| **0.5** | **20/08/2026** | *(tên SV)* | **Đồng bộ theo yêu cầu của giảng viên sau buổi báo cáo 20/08.** ① §6 mô hình dữ liệu: 3 → **5 thực thể** — tách danh mục cảm biến `sensor_device`, `sensor_data` nay lưu **một số đo của một cảm biến** trên mỗi bản ghi, thêm thực thể `users`. ② Thêm **FR-17** (danh mục cảm biến) và **FR-18** (ghi nhận người thao tác). ③ §4.1: vẽ lại màn hình Data Sensor theo cấu trúc mới, màn Action History thêm cột **Người thao tác**, bỏ chú thích về bản ghi thiếu số đo. ④ §4.2 và §4.3: đổi quy ước đặt mã sang `<vị trí>_<vai trò>` (`led1`→`room01_lamp`, `temp_01`→`room01_temp`…). ⑤ §4.4: thêm endpoint `/api/sensors/devices`, `/api/sensors/latest` trả mảng. ⑥ NFR-12/13/14 viết lại. ⑦ §7: T-08/T-10/T-17 sửa, thêm T-08b, T-10b, T-11b, T-18. ⑧ §8.2: chốt lại câu hỏi số 1 về đăng nhập |
| 0.1 | 13/08/2026 | *(tên SV)* | Khởi tạo bản nháp từ yêu cầu trên lớp |
| 0.2 | 13/08/2026 | *(tên SV)* | Chốt stack Django + DRF + Channels + PostgreSQL + Redis; bổ sung §2.2.1 phân rã tiến trình backend, CO-03b/c, NFR-15/16, T-16/17 |
| 0.4 | 18/08/2026 | *(tên SV)* | **Rà soát chéo 5 tài liệu.** UC-02 A3: bổ sung việc Backend từ chối lệnh trùng bằng `409` (phần máy chủ của BR-04). §4.3: sửa Client ID cho khớp `05-API.md` §6.1 (`backend_worker` / `backend_api_<ngẫu nhiên>` thay cho `backend_server`), đổi `request_id` mẫu sang UUID thật kèm ghi chú độ dài 36 ký tự. §7: T-07 sửa "sau 5 giây" → "sau 5–6 giây" cho khớp chu kỳ vòng quét 1 giây. §8.3: cập nhật trạng thái bàn giao. **FR/NFR, phạm vi, kiến trúc và sơ đồ giữ nguyên** |
| 0.3 | 17/08/2026 | *(tên SV)* | Đồng bộ §3.2 và §4.1 với bản vẽ giao diện: bảng Data Sensor thêm cột **Node** và dòng chú thích về bản ghi thiếu số đo, bảng Action History thêm cột **Độ trễ**; vẽ lại sơ đồ ASCII màn hình 2, mô tả đầy đủ bộ lọc của màn hình 3; T-08 sửa "5 cột" → "6 cột". **Danh sách FR/NFR, phạm vi và kiến trúc giữ nguyên** |

### 8.2 Vấn đề còn treo (cần chốt với giảng viên)

| # | Câu hỏi | Giả định tạm thời |
|---|---|---|
| 1 | Có cần chức năng đăng nhập / phân quyền không? | ✅ **Đã chốt 20/08:** hệ thống **có bảng người dùng** để ghi nhận người thao tác (FR-18), nhưng **chưa có màn hình đăng nhập**. Người thao tác xác định qua trường `user_id` tùy chọn khi gọi API điều khiển; bản ghi không xác định được người thì để rỗng. Đăng nhập và phân quyền theo `role` nằm ở mục hướng phát triển |
| 2 | Số lượng thiết bị điều khiển tối thiểu? | **2** (Đèn + Quạt), thiết kế sẵn để mở rộng lên 3+ |
| 2b | Hệ thống có phải chạy được với nhiều bo mạch / nhiều phòng không? | **Không bắt buộc** trong phạm vi đồ án (một phòng), nhưng schema đã sẵn sàng: cả hai bảng danh mục đều có `node_id`, và chân GPIO chỉ duy nhất **trong phạm vi một bo** nên phòng thứ hai dùng lại được `D5`/`D6`. Ba topic MQTT vẫn dùng chung cho mọi bo |
| 3 | Broker chạy local hay dùng dịch vụ cloud? | **Local Mosquitto**, có cấu hình chuyển sang cloud |
| 4 | Có cần làm thêm ứng dụng di động không? | **Không** — chỉ Web (Web responsive) |
| 5 | Chu kỳ gửi số liệu cảm biến bao nhiêu? | **2 giây** |
| 6 | Có cần chức năng cảnh báo vượt ngưỡng không? | **Không** trong phạm vi hiện tại |

### 8.3 Danh mục tài liệu sẽ bàn giao

| Tài liệu | File | Trạng thái |
|---|---|---|
| SRS | `docs/01-SRS.md` | ✅ v0.5 |
| Use Case Diagram + đặc tả | `docs/02-UseCase.md` | 🟨 v1.3 — **chờ đồng bộ mô hình dữ liệu mới** |
| Sequence Diagram | `docs/03-Sequence.md` | 🟨 v1.2 — **chờ đồng bộ** |
| Thiết kế CSDL | `docs/04-Database.md` | ✅ **v2.0** |
| API Documentation | `docs/05-API.md` | 🟨 v1.3 — **chờ đồng bộ** |
| Figma design | *(link)* | 🟨 mockup HTML xong, chờ vẽ lại trong Figma |
| Postman Collection | `docs/postman_collection.json` | ⬜ |
| Báo cáo PDF (C1–C4) | `docs/BaoCao.pdf` | 🟨 bản Word v0.2 đã dựng, chờ điền kết quả chương 4 |
