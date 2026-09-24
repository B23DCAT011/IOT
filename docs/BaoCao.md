# BÁO CÁO BÀI TẬP LỚN
## Hệ thống giám sát và điều khiển môi trường phòng dựa trên IoT

> **File nguồn của báo cáo Word.** Đây là bản **tự chứa** — mọi đặc tả cần cho người chấm đều nằm ngay trong file này, không trỏ sang tài liệu nào khác. Các file `01-SRS.md` → `05-API.md` là tài liệu thiết kế gốc, chi tiết hơn ở phần mã nguồn và ma trận truy vết, nhưng **không bắt buộc phải đọc kèm**.
> Những khối bảng có chữ **[ CHÈN HÌNH … ]** là chỗ trống chờ chèn ảnh — xem hướng dẫn ngay trong khung.
>
> Dựng file Word — ⚠️ **`docs/BaoCao.docx` có thể chứa phần chỉnh tay trong Word.** Hỏi trước khi ghi đè; nếu không chắc thì xuất ra tên tạm rồi tự đối chiếu:
> ```
> python tools/build_body.py docs/BaoCao.md
> timeout 240 python tools/assemble.py "HỆ THỐNG GIÁM SÁT VÀ ĐIỀU KHIỂN MÔI TRƯỜNG PHÒNG DỰA TRÊN IOT" docs/BaoCao.docx "ĐỀ TÀI"
> ```
> Đóng Word trước khi chạy, nếu không Word khoá file và lệnh sẽ báo lỗi.

---

## 1. TỔNG QUAN

### 1.1 Đặt vấn đề

Việc theo dõi các thông số môi trường của một căn phòng — nhiệt độ, độ ẩm, cường độ ánh sáng — và điều khiển các thiết bị điện trong phòng là nhu cầu phổ biến trong nhà thông minh, phòng máy chủ, phòng thí nghiệm hay kho bảo quản. Cách làm thủ công đòi hỏi người dùng phải có mặt tại chỗ để đọc chỉ số và bật/tắt thiết bị, không lưu lại được diễn biến theo thời gian và không thể can thiệp từ xa.

Sự phổ biến của các vi điều khiển giá rẻ tích hợp WiFi như ESP8266, cùng với giao thức truyền thông nhẹ MQTT, cho phép xây dựng một hệ thống giám sát và điều khiển hoàn chỉnh với chi phí phần cứng dưới 200.000 đồng. Đề tài này xây dựng một hệ thống như vậy, gồm đầy đủ ba lớp: thiết bị đầu cuối, máy chủ xử lý và giao diện web.

### 1.2 Mục tiêu

| # | Mục tiêu | Kết quả mong đợi |
|---|---|---|
| 1 | Thu thập số liệu môi trường tự động | ESP8266 đọc DHT11 và quang trở, gửi về máy chủ mỗi 2 giây qua MQTT |
| 2 | Hiển thị số liệu theo thời gian thực | Dashboard web cập nhật thẻ số liệu và biểu đồ không cần tải lại trang |
| 3 | Điều khiển thiết bị từ xa | Bật/tắt đèn và quạt từ trình duyệt, có xác nhận từ phần cứng |
| 4 | Lưu trữ và tra cứu lịch sử | Toàn bộ số liệu và thao tác được lưu vào CSDL, tra cứu có lọc và phân trang |
| 5 | Xử lý được tình huống lỗi | Thiết bị mất kết nối, dữ liệu sai ngưỡng, broker hỏng đều có cơ chế xử lý rõ ràng |

### 1.3 Phạm vi đề tài

**Trong phạm vi:** một căn phòng, hai thiết bị chấp hành (đèn và quạt mô phỏng bằng LED), **hai cảm biến đo ba đại lượng** (DHT11 cho nhiệt độ và độ ẩm, quang trở cho cường độ ánh sáng), chạy trên mạng LAN nội bộ. Hệ thống **lưu danh sách người dùng** để ghi nhận ai đã thao tác vào thiết bị.

**Ngoài phạm vi:** quản lý nhiều phòng, **màn hình đăng nhập và phân quyền**, ứng dụng di động, cảnh báo qua email/SMS, điều khiển thiết bị điện lưới 220V.

Về người dùng, cần phân biệt rõ hai việc: hệ thống **có** bảng người dùng và **có** ghi lại người thao tác cho từng lệnh điều khiển (FR-18), nhưng **chưa có** cơ chế đăng nhập để xác minh danh tính đó. Người thao tác được nêu kèm khi gọi giao diện lập trình điều khiển; lệnh không xác định được người phát ra thì bản ghi lịch sử để trống trường này. Cấu trúc dữ liệu đã chuẩn bị sẵn cho phần đăng nhập ở giai đoạn sau (mục 2.4.4).

### 1.4 Yêu cầu chức năng

| Mã | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-01 | Tiếp nhận số liệu nhiệt độ, độ ẩm, ánh sáng từ thiết bị IoT qua topic `data_sensors` | Bắt buộc |
| FR-02 | Hiển thị 3 thẻ số liệu tức thời kèm đơn vị (°C, %, lux) | Bắt buộc |
| FR-03 | Hiển thị biểu đồ đường diễn biến số liệu theo thời gian | Bắt buộc |
| FR-04 | Cho phép bật/tắt từng thiết bị độc lập từ giao diện | Bắt buộc |
| FR-05 | Publish lệnh điều khiển lên topic `device_control` | Bắt buộc |
| FR-06 | Cập nhật trạng thái thiết bị dựa trên phản hồi từ topic `device_respond` | Bắt buộc |
| FR-07 | Lưu mọi bản ghi cảm biến hợp lệ vào CSDL kèm mốc thời gian | Bắt buộc |
| FR-08 | Lưu mọi thao tác điều khiển vào lịch sử kèm trạng thái thực thi | Bắt buộc |
| FR-09 | Đánh dấu `FAILED` nếu không nhận phản hồi trong 5 giây | Bắt buộc |
| FR-10 | Hỗ trợ tìm kiếm và lọc theo cảm biến / khoảng giá trị / khoảng thời gian | Bắt buộc |
| FR-11 | Hỗ trợ sắp xếp theo cột và phân trang | Bắt buộc |
| FR-12 | Cập nhật giao diện theo thời gian thực qua WebSocket | Bắt buộc |
| FR-13 | Trang Profile chứa liên kết GitHub, PDF, Figma, API docs | Bắt buộc |
| FR-14 | Loại bỏ số đo nằm ngoài ngưỡng hợp lệ | Nên có |
| FR-15 | Hiển thị trạng thái kết nối của thiết bị IoT (online/offline) | Nên có |
| FR-16 | Cho phép mở rộng thêm cảm biến và thiết bị điều khiển mà không sửa mã nguồn lõi | Tùy chọn |
| FR-17 | Quản lý danh mục cảm biến; mỗi cảm biến có mã, tên, đại lượng đo, đơn vị và ngưỡng hợp lệ riêng | Bắt buộc |
| FR-18 | Ghi nhận người thao tác cho mỗi lệnh điều khiển và hiển thị ở màn hình lịch sử | Bắt buộc |

### 1.5 Yêu cầu phi chức năng

| Mã | Loại | Yêu cầu |
|---|---|---|
| NFR-01 | Hiệu năng | Độ trễ từ lúc bấm nút tới lúc thiết bị đổi trạng thái ≤ **2 giây** |
| NFR-02 | Hiệu năng | Độ trễ từ lúc thiết bị gửi số liệu tới lúc giao diện cập nhật ≤ **1 giây** |
| NFR-03 | Hiệu năng | API trả kết quả ≤ **500 ms** với bảng tới 100.000 bản ghi |
| NFR-04 | Hiệu năng | Chu kỳ gửi số liệu cảm biến **2 giây/lần**, cấu hình được trong firmware |
| NFR-05 | Độ tin cậy | Thiết bị tự kết nối lại WiFi và Broker sau mỗi 5 giây khi mất kết nối |
| NFR-06 | Độ tin cậy | Không mất bản ghi lịch sử kể cả khi lệnh thất bại (ghi trạng thái `FAILED`) |
| NFR-07 | Khả dụng | Giao diện hoạt động tốt trên Chrome/Edge bản mới, độ phân giải ≥ 1366×768 |
| NFR-08 | Khả dụng | Mọi thao tác chính thực hiện được trong ≤ 3 lần bấm chuột |
| NFR-09 | Bảo mật | MQTT Broker bắt buộc bật xác thực username/password, tắt truy cập ẩn danh |
| NFR-10 | Bảo mật | Kiểm tra hợp lệ toàn bộ dữ liệu đầu vào từ MQTT và HTTP |
| NFR-11 | Bảo trì | Toàn bộ cấu hình tách khỏi mã nguồn — `.env` cho backend, `config.h` cho firmware |
| NFR-12 | Bảo trì | Mã nguồn tách lớp rõ ràng: firmware / backend / frontend; backend chia thành các ứng dụng Django độc lập (`users`, `sensors`, `devices`, `realtime`, `mqtt`) |
| NFR-13 | Khả mở rộng | Thêm **cảm biến** mới chỉ cần thêm một bản ghi trong danh mục cảm biến; thêm **thiết bị** mới chỉ cần thêm một bản ghi trong bảng thiết bị và khai báo ánh xạ chân GPIO. Cả hai đều không thay đổi cấu trúc bảng |
| NFR-14 | Ràng buộc dữ liệu | Mỗi cảm biến có ngưỡng hợp lệ riêng lưu trong danh mục. Giá trị hiện hành: nhiệt độ −10 → 60 °C · độ ẩm 0 → 100 % · ánh sáng 0 → 2000 lux |
| NFR-15 | Bảo trì | Mọi thay đổi cấu trúc cơ sở dữ liệu thực hiện qua migration, không sửa thủ công |
| NFR-16 | Độ tin cậy | MQTT worker phải tự kết nối lại broker khi mất kết nối và ghi log mọi message không hợp lệ; không được dừng vì một message hỏng |

### 1.6 Công nghệ sử dụng

| Lớp | Công nghệ | Lý do lựa chọn |
|---|---|---|
| Firmware | Arduino IDE (C++), thư viện `DHT`, `ESP8266WiFi`, `arduino-mqtt` *(lwmqtt)* | `arduino-mqtt` được chọn thay cho `PubSubClient` phổ biến hơn vì `PubSubClient` **chỉ publish được ở QoS 0**, không đáp ứng được mức QoS 1 mà topic `device_respond` yêu cầu (mục 2.3.2) |
| Truyền thông | Eclipse Mosquitto (MQTT), cổng 1883 | Giao thức nhẹ, thiết kế cho thiết bị tài nguyên hạn chế |
| Backend | Django 5 + Django REST Framework | Có sẵn ORM, migration, trang admin và hệ sinh thái filter/pagination |
| Realtime | Django Channels + Daphne (ASGI) | Đẩy dữ liệu tới trình duyệt qua WebSocket |
| Channel layer | Redis 7 | Bắt buộc — nối hai tiến trình backend, xem §2.3.1 |
| Cơ sở dữ liệu | PostgreSQL 16 | Hỗ trợ tốt kiểu `timestamptz`, `uuid` và chỉ mục bộ phận |
| Frontend | React + Vite + Recharts + Axios | Dựng biểu đồ realtime nhanh |
| Tài liệu API | `drf-spectacular` (OpenAPI/Swagger) + Postman | Sinh tài liệu tự động từ mã nguồn |

### 1.7 Bố cục báo cáo

- **Chương 1** trình bày bối cảnh, mục tiêu, phạm vi và các yêu cầu của hệ thống.
- **Chương 2** trình bày thiết kế ở mức hệ thống: kiến trúc tổng thể, phần cứng, phần mềm và cơ sở dữ liệu.
- **Chương 3** trình bày thiết kế chi tiết: biểu đồ use case, đặc tả đầy đủ cả 7 use case, quy tắc nghiệp vụ, biểu đồ tuần tự, thiết kế giao diện và thiết kế API.
- **Chương 4** trình bày kết quả thử nghiệm, đánh giá và kết luận.

---

## 2. THIẾT KẾ HỆ THỐNG

### 2.1 Kiến trúc tổng thể

Hệ thống gồm hai khối đặt trong cùng một mạng WiFi nội bộ:

- **Khối thiết bị (Edge)** — mạch ESP8266 gắn cảm biến và LED, đặt trong phòng cần giám sát.
- **Khối máy chủ** — chạy trên một máy tính, gồm MQTT Broker, Backend, Cơ sở dữ liệu, Frontend và một máy chủ Redis đóng vai trò cầu nối giữa hai tiến trình của Backend (giải thích ở mục 2.3.1).

Hai khối **không giao tiếp trực tiếp** với nhau mà thông qua MQTT Broker theo mô hình publish/subscribe. Nhờ vậy thiết bị và máy chủ không cần biết địa chỉ của nhau, và có thể khởi động lại độc lập mà không phá vỡ kết nối của bên còn lại.

![Kiến trúc tổng thể hệ thống](docs/img/architecture.png){ width=95% }

*Hình 2.1. Kiến trúc tổng thể hệ thống*

Ba mũi tên bắc ngang giữa hai khối đều nối vào **MQTT Broker**, không có đường nào nối thẳng ESP8266 với Backend — đó là biểu diễn trực quan của mô hình publish/subscribe nói ở đoạn trên. Chiều mũi tên cho biết hướng đi của message: hai topic `data_sensors` và `device_respond` đi từ thiết bị lên, riêng `device_control` đi từ máy chủ xuống.

### 2.2 Thiết kế phần cứng

#### 2.2.1 Danh sách linh kiện

| # | Linh kiện | Model | Chức năng |
|---|---|---|---|
| 1 | Vi điều khiển | ESP8266 NodeMCU | Đọc cảm biến, kết nối WiFi, điều khiển LED |
| 2 | Cảm biến nhiệt độ, độ ẩm | DHT11 | Đo nhiệt độ (±2 °C) và độ ẩm (±5 %RH) |
| 3 | Cảm biến ánh sáng | Quang trở + module LM393 | Đo cường độ chiếu sáng |
| 4 | Thiết bị chấp hành 1 | LED + điện trở 220 Ω | Mô phỏng đèn |
| 5 | Thiết bị chấp hành 2 | LED + điện trở 220 Ω | Mô phỏng quạt |
| 6 | Phụ kiện | Breadboard, dây nối | Lắp mạch thử nghiệm |

#### 2.2.2 Sơ đồ đấu nối

| Chân ESP8266 | Kết nối tới | Chế độ |
|---|---|---|
| `D4` (GPIO2) | DHT11 — chân Data | INPUT |
| `A0` | LM393 — chân AO | ANALOG INPUT |
| `D5` (GPIO14) | LED 1 (Đèn) qua trở 220 Ω | OUTPUT |
| `D6` (GPIO12) | LED 2 (Quạt) qua trở 220 Ω | OUTPUT |
| `3V3` | VCC của DHT11 và LM393 | — |
| `GND` | GND chung của toàn mạch | — |

| ⬛ CHÈN HÌNH 2.2 |
|---|
| **Cần vẽ:** sơ đồ đấu nối trên breadboard. **Công cụ gợi ý:** Fritzing, hoặc chụp ảnh mạch thật đã lắp. **Kích thước:** ngang 14 cm. **Làm ở tuần 2.** |

*Hình 2.2. Sơ đồ đấu nối phần cứng*

### 2.3 Thiết kế phần mềm

#### 2.3.1 Phân rã tiến trình phía Backend

Django là framework đồng bộ theo mô hình request–response, không có sẵn vòng lặp nền để duy trì kết nối MQTT. Vì vậy backend được tách thành **hai tiến trình chạy song song**:

| Tiến trình | Lệnh khởi chạy | Trách nhiệm |
|---|---|---|
| **P1 — ASGI server** | `daphne -p 8000 config.asgi:application` | Phục vụ REST API; duy trì kết nối WebSocket; publish lệnh lên `device_control` |
| **P2 — MQTT worker** | `python manage.py mqtt_worker` | Subscribe `data_sensors` và `device_respond`; ghi dữ liệu vào PostgreSQL; đẩy sự kiện tới P1 |

**Redis là thành phần bắt buộc.** Hai tiến trình nằm ở hai không gian bộ nhớ khác nhau, nên P2 không thể gọi trực tiếp tới các kết nối WebSocket do P1 đang giữ. Redis đóng vai trò *channel layer* — P2 đẩy sự kiện vào Redis, P1 nhận và phát tiếp ra trình duyệt. Nếu dùng `InMemoryChannelLayer` thay cho Redis, hệ thống **không báo bất kỳ lỗi nào** nhưng trình duyệt sẽ không bao giờ nhận được dữ liệu.

| ⬛ CHÈN HÌNH 2.3 |
|---|
| **Cần vẽ:** sơ đồ hai tiến trình P1 và P2 nối nhau qua Redis, kèm các mũi tên tới PostgreSQL, Mosquitto và trình duyệt. **Nguồn tham khảo:** bảng phân rã tiến trình ngay phía trên. **Kích thước:** ngang 14 cm. |

*Hình 2.3. Phân rã tiến trình phía Backend*

#### 2.3.2 Giao thức truyền thông MQTT

Hệ thống dùng đúng **ba topic**:

| # | Topic | Hướng | QoS | Nội dung |
|---|---|---|---|---|
| 1 | `data_sensors` | ESP8266 → Backend | 0 | Số liệu cảm biến, gửi mỗi 2 giây |
| 2 | `device_control` | Backend → ESP8266 | 1 | Lệnh bật/tắt thiết bị |
| 3 | `device_respond` | ESP8266 → Backend | 1 | Xác nhận thiết bị đã thực thi |

**Về mức QoS:** `data_sensors` dùng QoS 0 vì mất một mẫu trong 43.200 mẫu mỗi ngày không ảnh hưởng tới biểu đồ, trong khi bắt tay xác nhận của QoS 1 tốn thêm một vòng truyền cho mỗi mẫu. Ngược lại, `device_control` và `device_respond` dùng QoS 1 vì mất một lệnh điều khiển là người dùng thấy hệ thống hỏng.

Cấu trúc dữ liệu của ba topic:

```json
// data_sensors
{ "device_id": "esp8266_room01", "temperature": 28.5,
  "humidity": 72.0, "light": 350 }

// device_control
{ "request_id": "3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
  "device": "room01_lamp", "action": "ON" }

// device_respond
{ "request_id": "3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
  "device": "room01_lamp", "state": "ON", "status": "SUCCESS" }
```

Trường `request_id` là mã định danh duy nhất của mỗi lệnh, do backend sinh bằng `uuid4()`. Nó tồn tại vì lệnh đi ra và phản hồi đi về theo **hai đường khác nhau** — không có mã này thì backend không biết phản hồi vừa nhận ứng với lệnh nào.

### 2.4 Thiết kế cơ sở dữ liệu

Toàn bộ dữ liệu nghiệp vụ nằm trong **năm bảng**, chia làm ba nhóm: hai bảng **danh mục** mô tả *cái gì đang tồn tại*, hai bảng **lịch sử** ghi lại *chuyện gì đã xảy ra*, và một bảng **người dùng** cho biết *ai đã làm*.

![Sơ đồ thực thể liên kết](docs/img/erd.png){ width=90% }

*Hình 2.4. Sơ đồ thực thể — liên kết (ERD)*

| Bảng | Vai trò | Nhịp ghi |
|---|---|---|
| `sensors_sensordevice` | Danh mục cảm biến | Tĩnh, 3 dòng |
| `sensors_sensordata` | Số đo | ~129.600 dòng/ngày |
| `devices_device` | Thiết bị chấp hành | Tĩnh, 2 dòng |
| `devices_actionhistory` | Lịch sử thao tác | Vài chục dòng/ngày |
| `users_user` | Người thao tác | Tĩnh |

**Ba khái niệm dễ nhầm, nay là ba thứ tách bạch.** Cả ba đều hay được gọi chung là "thiết bị": *node* là bo mạch ESP8266 (`esp8266_room01`), *cảm biến* là bộ phận đo một đại lượng (`room01_temp`), *thiết bị chấp hành* là đối tượng bật/tắt được (`room01_lamp`). Node được lưu thành một cột trong cả hai bảng danh mục; hai khái niệm còn lại là hai bảng riêng.

**Quy ước đặt mã nghiệp vụ** theo mẫu `<vị trí>_<vai trò>`: `room01_temp`, `room01_humi`, `room01_lux`, `room01_lamp`, `room01_fan`. Nhìn mã là biết ngay thiết bị thuộc phòng nào, nên khi mở rộng sang phòng thứ hai chỉ cần thêm dữ liệu với tiền tố `room02_`.

#### 2.4.1 Bảng `sensors_sensordevice` — danh mục cảm biến

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | `bigserial` | Khóa chính kỹ thuật |
| `code` | `varchar(30)` `UNIQUE` | Mã nghiệp vụ: `room01_temp`, `room01_humi`, `room01_lux` |
| `name` | `varchar(100)` | Tên hiển thị: "Nhiệt độ phòng" |
| `metric_type` | `varchar(20)` | `TEMPERATURE` / `HUMIDITY` / `LIGHT` |
| `unit` | `varchar(10)` | Đơn vị hiển thị: `°C`, `%`, `lux` |
| `hardware_model` | `varchar(50)` | Linh kiện thực tế: `DHT11`, `LM393` |
| `node_id` | `varchar(50)` | Bo mạch chứa cảm biến |
| `min_value`, `max_value` | `double precision` | Ngưỡng hợp lệ **riêng của cảm biến đó** |
| `is_active` | `boolean` | `false` khi cảm biến đã tháo |
| `created_at`, `updated_at` | `timestamptz` | Mốc tạo và cập nhật |

Bảng này là **điểm mở rộng chính của hệ thống**. Lắp thêm cảm biến khí gas chỉ cần thêm một dòng vào đây và khởi động lại tiến trình MQTT worker — Dashboard tự hiện thêm một thẻ số liệu, bảng tra cứu tự có thêm lựa chọn trong bộ lọc, không sửa mã nguồn và không thay đổi cấu trúc bảng.

Ngưỡng hợp lệ đặt ở đây thay vì ghi cứng trong mã vì đó là **dữ liệu cấu hình**: hiệu chuẩn lại quang trở sau khi lắp mạch chỉ cần sửa một dòng dữ liệu.

Ràng buộc `UNIQUE (node_id, metric_type)` bảo đảm mỗi bo mạch chỉ có một cảm biến cho mỗi đại lượng. Nhờ đó backend ánh xạ được trường `temperature` trong gói tin MQTT sang đúng một dòng của bảng này mà firmware không phải gửi kèm mã cảm biến.

#### 2.4.2 Bảng `sensors_sensordata` — số đo

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | `bigserial` | Khóa chính |
| `sensor_id` | `bigint` `FK` | Cảm biến đã sinh ra số đo |
| `value` | `double precision` **`NOT NULL`** | Giá trị đo; đơn vị lấy qua khóa ngoại |
| `recorded_at` | `timestamptz` | Thời điểm backend nhận số liệu |

**Mỗi bản ghi là một số đo của một cảm biến**, không phải một cụm ba số đo. Một chu kỳ lấy mẫu 2 giây sinh ra **ba bản ghi** mang **cùng một** `recorded_at`; ràng buộc `UNIQUE (sensor_id, recorded_at)` bảo đảm một cảm biến không thể có hai số đo tại cùng một thời điểm.

Cách tổ chức này giải quyết dứt điểm vấn đề của mô hình cũ. Trước đây ba cột số đo đều phải cho phép `NULL` để xử lý trường hợp chỉ đọc được một phần cảm biến, kéo theo một hành vi khó giải thích: khi lọc theo khoảng giá trị, bản ghi có cột đó rỗng bị loại ở **cả hai chiều** so sánh, khiến tổng số bản ghi nhỏ hơn dự kiến mà không có lỗi nào. Nay cột `value` là `NOT NULL` — cảm biến không đọc được thì **không có bản ghi**, đúng nghĩa hơn và không còn hiện tượng bất ngờ nào.

Đổi lại, bảng nhận số dòng gấp ba (43.200 → 129.600 dòng/ngày) và dung lượng tăng khoảng 2,3 lần. Ở quy mô đề tài, tổng dung lượng sau bốn tháng vẫn dưới 1,5 GB.

Cột `recorded_at` do **backend sinh**, không lấy từ dữ liệu thiết bị gửi lên: ESP8266 không có đồng hồ thời gian thực, sau mỗi lần khởi động lại mốc thời gian của nó trở nên vô nghĩa, khiến biểu đồ có thể chạy lùi.

#### 2.4.3 Bảng `devices_device` — thiết bị chấp hành

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | `bigserial` | Khóa chính kỹ thuật, dùng trong URL API |
| `code` | `varchar(30)` `UNIQUE` | Mã nghiệp vụ (`room01_lamp`, `room01_fan`), dùng trong payload MQTT |
| `name` | `varchar(100)` | Tên hiển thị trên giao diện |
| `device_type` | `varchar(20)` | `LIGHT` / `FAN` / `OTHER` |
| `node_id` | `varchar(50)` | Bo mạch có chân điều khiển thiết bị này |
| `gpio_pin` | `varchar(10)` | Chân điều khiển, duy nhất **trong phạm vi một bo mạch** |
| `current_state` | `varchar(10)` | Trạng thái hiện tại: `ON` / `OFF` |
| `is_active` | `boolean` | `false` khi thiết bị đã tháo |
| `created_at` | `timestamptz` | Thời điểm tạo bản ghi |
| `updated_at` | `timestamptz` | Lần đổi trạng thái gần nhất — bằng đúng `responded_at` của lệnh `SUCCESS` cuối cùng |

Bảng có cả `id` lẫn `code` vì hai mã phục vụ hai mục đích khác nhau: `id` do CSDL sinh, dùng cho URL và khóa ngoại; `code` là chuỗi cố định để firmware so sánh (`if (device == "room01_lamp")`) — chạy lại migration ở máy khác có thể cho `id` khác, còn `code` thì không đổi.

**Chân GPIO chỉ duy nhất trong phạm vi một bo mạch, không phải trên toàn hệ thống.** Chân `D5` của bo phòng 1 và chân `D5` của bo phòng 2 là hai chân vật lý khác nhau, dùng cả hai là hoàn toàn hợp lệ. Đây là lý do ràng buộc duy nhất đặt trên cặp `(node_id, gpio_pin)` chứ không riêng `gpio_pin`. Nguyên tắc này áp dụng đối xứng cho bảng danh mục cảm biến: **một tài nguyên vật lý chỉ duy nhất trong phạm vi bo mạch sở hữu nó**.

#### 2.4.4 Bảng `users_user` — người thao tác

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | `bigserial` | Khóa chính |
| `username` | `varchar(150)` `UNIQUE` | Tên đăng nhập |
| `password` | `varchar(128)` | Mật khẩu **đã băm** |
| `full_name` | `varchar(100)` | Họ và tên, hiển thị ở cột "Người thao tác" |
| `role` | `varchar(20)` | `ADMIN` / `OPERATOR` / `VIEWER` |
| `is_active` | `boolean` | `false` khi tài khoản ngừng sử dụng |
| `date_joined`, `last_login` | `timestamptz` | Mốc tạo tài khoản và lần đăng nhập gần nhất |

Bảng kế thừa lớp `AbstractUser` có sẵn của Django thay vì tự dựng từ đầu. Lý do quan trọng nhất không phải là tiết kiệm công sức mà là **khả năng mở rộng**: cấu hình `AUTH_USER_MODEL` gần như không thay đổi được sau lần chạy migration đầu tiên, vì Django ghi khóa ngoại tới bảng người dùng vào nhiều bảng hệ thống ngay từ đầu. Khai báo mô hình người dùng riêng ngay lúc này là cách duy nhất để bổ sung chức năng đăng nhập ở giai đoạn sau mà không phải xóa và tạo lại toàn bộ cơ sở dữ liệu. Hai lý do phụ: có sẵn cơ chế băm mật khẩu — tự lưu mật khẩu dạng thô là lỗi bảo mật cơ bản kể cả khi chưa dùng tới — và có sẵn trang quản trị.

Cột `role` hiện **chỉ mang tính mô tả**, chưa dùng để chặn thao tác. Nó là chỗ móc sẵn cho phần phân quyền ở hướng phát triển; thêm một cột vào bảng vài dòng lúc này gần như không tốn gì, còn thêm sau khi đã có dữ liệu thật thì tốn một lần migration.

#### 2.4.5 Bảng `devices_actionhistory` — lịch sử thao tác

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | `bigserial` | Khóa chính |
| `device_id` | `bigint` `FK` | Thiết bị được điều khiển |
| `user_id` | `bigint` `FK`, cho phép `NULL` | **Người đã thao tác** |
| `request_id` | `uuid` `UNIQUE` | Mã ghép cặp lệnh gửi đi với phản hồi nhận về |
| `action` | `varchar(10)` | Lệnh yêu cầu: `ON` / `OFF` |
| `status` | `varchar(10)` | `PENDING` / `SUCCESS` / `FAILED` |
| `error_message` | `varchar(255)` | Lý do thất bại, `NULL` khi thành công |
| `created_at` | `timestamptz` | Thời điểm gửi lệnh — mốc tính timeout 5 giây |
| `responded_at` | `timestamptz` | Thời điểm lệnh **kết thúc**: lúc nhận `device_respond`, hoặc lúc vòng quét đánh dấu hết giờ. `NULL` khi còn `PENDING` |

Cột `user_id` **cho phép rỗng** vì có những lệnh không do người dùng giao diện phát ra: lệnh thử bằng công cụ dòng lệnh khi kiểm thử, dữ liệu khởi tạo, kịch bản kiểm thử tự động. Ép trường này bắt buộc sẽ buộc phải bịa ra một "người dùng hệ thống" giả. Giao diện hiển thị dấu `—` cho các bản ghi này, **không** ghi "Hệ thống" hay "Ẩn danh" — hai chữ đó gợi ý rằng tồn tại một tài khoản mang tên như vậy, trong khi sự thật là *không biết ai*.

Giá trị `user_id` được ghi **một lần** ở bước tạo bản ghi và không bao giờ đổi; tiến trình cập nhật kết quả chỉ chạm vào ba cột `status`, `responded_at`, `error_message`.

Cột `responded_at` mang nghĩa "thời điểm kết thúc" chứ không chỉ là "thời điểm nhận phản hồi": một lệnh hết giờ không hề có phản hồi nào nhưng vẫn được ghi mốc thời gian tại lúc bị đánh `FAILED`. Nhờ vậy cột dẫn xuất `latency_ms` (`responded_at − created_at`) luôn có giá trị với mọi bản ghi đã kết thúc — lệnh thành công cho vài trăm mili-giây, lệnh hết giờ luôn rơi vào dải 5.000–6.000 ms.

Cả ba khóa ngoại của hệ thống đều đặt `on_delete=PROTECT`: không cho xóa cảm biến, thiết bị hay người dùng nếu còn bản ghi tham chiếu tới. Đối tượng ngừng sử dụng thì đặt `is_active = false` chứ không xóa, để bảo toàn lịch sử theo NFR-06.

#### 2.4.6 Ràng buộc toàn vẹn

Toàn bộ **18 ràng buộc** được khai báo ở tầng cơ sở dữ liệu, không chỉ ở tầng ứng dụng — để dữ liệu chèn thủ công qua công cụ quản trị cũng không lọt được giá trị rác:

| # | Bảng | Loại | Nội dung |
|---|---|---|---|
| 1 | người dùng | CHECK | `role` thuộc {`ADMIN`, `OPERATOR`, `VIEWER`} |
| 2 | danh mục cảm biến | UNIQUE | `code` không trùng |
| 3 | danh mục cảm biến | UNIQUE | `(node_id, metric_type)` — mỗi bo chỉ một cảm biến cho mỗi đại lượng |
| 4 | danh mục cảm biến | CHECK | `metric_type` thuộc {`TEMPERATURE`, `HUMIDITY`, `LIGHT`} |
| 5 | danh mục cảm biến | CHECK | `min_value < max_value` |
| 6 | số đo | FOREIGN KEY | `sensor_id` tham chiếu danh mục cảm biến, chặn xóa cảm biến còn số đo |
| 7 | số đo | UNIQUE | `(sensor_id, recorded_at)` — một cảm biến không có hai số đo cùng thời điểm |
| 8 | số đo | CHECK | `value` nằm trong dải rộng −1000 → 100000 (lưới an toàn) |
| 9 | thiết bị | UNIQUE | `code` không trùng |
| 10 | thiết bị | UNIQUE | `(node_id, gpio_pin)` — hai thiết bị dùng chung một chân **trên cùng một bo** là lỗi phần cứng |
| 11 | thiết bị | CHECK | `current_state` thuộc {`ON`, `OFF`} |
| 12 | thiết bị | CHECK | `device_type` thuộc {`LIGHT`, `FAN`, `OTHER`} |
| 13 | lịch sử thao tác | FOREIGN KEY | `device_id` tham chiếu bảng thiết bị |
| 14 | lịch sử thao tác | FOREIGN KEY | `user_id` tham chiếu bảng người dùng, cho phép rỗng |
| 15 | lịch sử thao tác | UNIQUE | `request_id` không trùng (BR-06) |
| 16 | lịch sử thao tác | CHECK | `action` thuộc {`ON`, `OFF`} |
| 17 | lịch sử thao tác | CHECK | `status` thuộc {`PENDING`, `SUCCESS`, `FAILED`} |
| 18 | lịch sử thao tác | CHECK | `status = PENDING` **khi và chỉ khi** `responded_at` rỗng |

Ràng buộc số 18 đáng chú ý nhất: nó chặn được lỗi lập trình quên đặt mốc thời gian khi cập nhật trạng thái, và chính nó là lý do luồng phát hiện hết giờ **bắt buộc** phải ghi `responded_at` dù không nhận được phản hồi nào.

**Về việc kiểm tra ngưỡng hợp lệ của số đo (BR-02).** Ngưỡng nay là dữ liệu nằm ở bảng danh mục, mà ràng buộc `CHECK` của hệ quản trị **không tham chiếu được sang bảng khác**. Vì vậy việc kiểm tra do MQTT worker đảm nhiệm — nó đọc ngưỡng của đúng cảm biến rồi loại bỏ số đo vượt ngưỡng và ghi log kèm nội dung gói tin gốc. Ràng buộc số 8 chỉ là lưới an toàn thô, chặn dữ liệu rác hiển nhiên khi có người chèn tay qua công cụ quản trị. Đây là cái giá phải trả cho việc đưa ngưỡng vào dữ liệu, và cần nêu rõ thay vì tuyên bố hệ thống bảo vệ hai tầng ngang nhau.

#### 2.4.7 Chỉ mục

| # | Bảng | Cột | Phục vụ |
|---|---|---|---|
| 1 | số đo | `(recorded_at giảm dần, sensor_id)` | Sắp xếp mặc định (BR-09), lọc theo khoảng thời gian, phân trang |
| 2 | số đo | `(sensor_id, recorded_at)` *(sinh kèm ràng buộc `UNIQUE`)* | Lấy số đo mới nhất của từng cảm biến, vẽ biểu đồ, lọc theo cảm biến |
| 3 | lịch sử thao tác | `created_at` giảm dần | Sắp xếp mặc định của màn hình Action History |
| 4 | lịch sử thao tác | `(device_id, created_at giảm dần)` | Lọc lịch sử theo thiết bị |
| 5 | lịch sử thao tác | `created_at` **chỉ với** `status = 'PENDING'` | Vòng quét phát hiện hết giờ, chạy mỗi giây |
| 6 | lịch sử thao tác | `user_id` | Lọc lịch sử theo người thao tác |
| 7 | lịch sử thao tác | `status` | Lọc theo trạng thái `SUCCESS` / `FAILED` |

Chỉ mục số 5 là **chỉ mục bộ phận**: vòng quét chạy 86.400 lần mỗi ngày nhưng ở trạng thái bình thường số bản ghi `PENDING` gần như bằng 0, nên chỉ mục này chỉ chứa vài dòng và tra cứu gần như tức thời.

Chỉ mục số 2 là một lựa chọn thiết kế đáng nói: nó **gánh hai vai** cùng lúc — vừa là ràng buộc nghiệp vụ "một cảm biến không có hai số đo cùng thời điểm", vừa là chỉ mục chính cho mọi truy vấn theo cảm biến. Cùng một cấu trúc dữ liệu, thêm ý nghĩa mà không thêm chi phí ghi. Cũng vì đã có nó nên khóa ngoại `sensor_id` được khai báo **không** tạo chỉ mục đơn cột riêng, tránh một chỉ mục trùng chức năng phải cập nhật ở cả 129.600 lượt ghi mỗi ngày.

Chỉ mục số 1 **bắt buộc phải gồm hai cột**. Ba số đo cùng một chu kỳ có `recorded_at` giống hệt nhau; nếu chỉ sắp xếp theo thời gian thì hệ quản trị được tự do trả về chúng theo thứ tự bất kỳ, và thứ tự có thể khác nhau giữa hai lần gọi — hậu quả là khi người dùng lật trang, có dòng xuất hiện hai lần còn dòng khác biến mất. Đây là loại lỗi chỉ lộ ra khi sang trang thứ hai nên rất dễ lọt qua các lần thử tay.

**Cột `value` cố ý không đánh chỉ mục.** Bảng nhận 129.600 lượt ghi mỗi ngày, trong khi lọc theo giá trị là thao tác thủ công vài lần mỗi phiên làm việc. Thêm nữa, điều kiện lọc theo giá trị luôn đi kèm điều kiện chọn cảm biến — vốn đã được chỉ mục số 2 phục vụ và thu hẹp tập dữ liệu còn một phần ba trước khi phải so sánh giá trị.

---

## 3. THIẾT KẾ CHI TIẾT

### 3.1 Biểu đồ Use Case

Hệ thống có **7 use case** với 3 tác nhân. Người dùng là tác nhân chính của UC-01 đến UC-06; thiết bị IoT là tác nhân chính của UC-07 — một use case chạy tự động theo chu kỳ, không do người dùng khởi xướng.

![Biểu đồ Use Case](docs/img/usecase-diagram.png){ width=85% }

*Hình 3.1. Biểu đồ Use Case tổng thể*

| ID | Tên use case | Tác nhân chính | Ưu tiên |
|---|---|---|---|
| UC-01 | Xem Dashboard giám sát | Người dùng | Cao |
| UC-02 | Điều khiển bật/tắt thiết bị | Người dùng | Cao |
| UC-03 | Xem lịch sử số liệu cảm biến | Người dùng | Cao |
| UC-04 | Tìm kiếm, lọc, sắp xếp, phân trang | Người dùng | Trung bình |
| UC-05 | Xem lịch sử thao tác thiết bị | Người dùng | Cao |
| UC-06 | Xem trang Profile | Người dùng | Thấp |
| UC-07 | Thu thập và truyền số liệu *(tự động)* | Thiết bị IoT | Cao |

Ba quan hệ giữa các use case:

| Quan hệ | Từ | Đến | Giải thích |
|---|---|---|---|
| `«extend»` | UC-04 | UC-03 | Tìm kiếm/lọc/sắp xếp là **tùy chọn** — UC-03 vẫn hoàn thành trọn vẹn nếu người dùng không thao tác gì |
| `«extend»` | UC-04 | UC-05 | Tương tự với bảng lịch sử thao tác |
| `«include»` | UC-02 | UC-05 | Mỗi lần điều khiển **luôn luôn** sinh một bản ghi lịch sử — bắt buộc, không phải tùy chọn |

Riêng **phân trang** cần phân biệt hai việc khác nhau, vì tên UC-04 có chứa từ này:

- **Việc hệ thống luôn trả dữ liệu theo trang** là một phần **luồng cơ sở** của UC-03 và UC-05 — người dùng không làm gì thì hệ thống vẫn phân trang. Phần này *không* thuộc UC-04.
- **Thao tác chuyển trang** do người dùng chủ động thực hiện thì thuộc UC-04 (bước 7 của luồng chính).

Nói cách khác, quan hệ `«extend»` ở trên chỉ áp cho phần **tùy chọn** — tìm kiếm, lọc, sắp xếp và chuyển trang — chứ không áp cho cơ chế phân trang mặc định.

### 3.2 Đặc tả use case

Phần này đặc tả đầy đủ cả **bảy** use case theo cùng một khuôn mẫu: bảng thuộc tính, luồng chính, luồng thay thế, luồng ngoại lệ, và bảng truy vết cuối mỗi use case (quy tắc nghiệp vụ, dữ liệu vào/ra, yêu cầu đặc biệt, yêu cầu chức năng liên quan).

Quy ước mã luồng dùng thống nhất trong toàn bộ phần này: **`A`** là luồng thay thế — hệ thống vẫn đi tới kết quả có ý nghĩa, chỉ khác đường; **`E`** là luồng ngoại lệ — có lỗi xảy ra và use case kết thúc sớm hoặc kết thúc thất bại.

#### 3.2.1 UC-01 — Xem Dashboard giám sát

| Thuộc tính | Nội dung |
|---|---|
| **Mã / Tên** | UC-01 — Xem Dashboard giám sát |
| **Tác nhân chính** | Người dùng |
| **Tác nhân phụ** | — |
| **Mô tả** | Người dùng theo dõi số liệu nhiệt độ, độ ẩm, ánh sáng hiện tại của phòng và diễn biến của chúng theo thời gian |
| **Độ ưu tiên** | Cao |
| **Tần suất** | Rất cao — là màn hình mặc định khi mở ứng dụng |
| **Kích hoạt** | Người dùng truy cập đường dẫn gốc `/` hoặc chọn mục "Dashboard" trên thanh điều hướng |
| **Tiền điều kiện** | Backend (tiến trình ASGI) đang chạy và truy cập được cơ sở dữ liệu |
| **Hậu điều kiện thành công** | Dashboard hiển thị số liệu mới nhất; kết nối WebSocket được thiết lập và giao diện tự cập nhật |
| **Hậu điều kiện thất bại** | Hiển thị thông báo lỗi; không thay đổi trạng thái hệ thống |

**Luồng chính**

| # | Tác nhân | Hành động |
|---|---|---|
| 1 | Người dùng | Truy cập trang Dashboard |
| 2 | Hệ thống | Gọi API lấy **danh mục cảm biến**, **số đo mới nhất của từng cảm biến** và N chu kỳ gần nhất cho biểu đồ (mặc định N = 20, theo BR-10) |
| 3 | Hệ thống | Hiển thị **một thẻ số liệu cho mỗi cảm biến trong danh mục** — hiện là 3 thẻ: Nhiệt độ (°C), Độ ẩm (%), Ánh sáng (lux). Nhãn và đơn vị lấy từ danh mục, không ghi cứng trong mã (FR-17) |
| 4 | Hệ thống | Hiển thị biểu đồ đường diễn biến số liệu theo trục thời gian |
| 5 | Hệ thống | Gọi API lấy danh sách thiết bị kèm trạng thái hiện tại, hiển thị các công tắc |
| 6 | Hệ thống | Mở kết nối WebSocket tới `/ws/realtime/` |
| 7 | Hệ thống | Mỗi khi nhận sự kiện `sensor.data`, cập nhật thẻ số liệu và thêm điểm mới vào biểu đồ |

**Luồng thay thế**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| A1 | Chưa có bản ghi cảm biến nào trong cơ sở dữ liệu | Hiển thị `--` trên cả 3 thẻ, biểu đồ trống kèm dòng chữ "Chưa có dữ liệu" |
| A2 | Không nhận được số liệu mới quá 30 giây (BR-07) | Hiển thị nhãn "Thiết bị ngoại tuyến" cạnh tiêu đề; số liệu cũ vẫn giữ nguyên nhưng làm mờ |
| A3 | Một cảm biến có trong danh mục nhưng chưa từng gửi số đo nào | Thẻ của cảm biến đó hiển thị `--`; các thẻ còn lại vẫn hiện số liệu bình thường |

**Luồng ngoại lệ**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| E1 | Kết nối WebSocket bị ngắt | Hiển thị chỉ báo "Mất kết nối"; tự động thử kết nối lại mỗi 5 giây; khi thành công thì tải lại số liệu mới nhất |
| E2 | API trả về lỗi 5xx | Hiển thị thông báo "Không tải được dữ liệu" kèm nút "Thử lại" |

| | |
|---|---|
| **Quy tắc nghiệp vụ** | BR-02, BR-07, BR-10, BR-11 |
| **Dữ liệu vào** | Không có |
| **Dữ liệu ra** | Mảng số đo mới nhất — mỗi phần tử gồm mã cảm biến, tên, đơn vị, giá trị, mốc thời gian; danh sách thiết bị kèm `current_state` |
| **Yêu cầu đặc biệt** | Độ trễ cập nhật ≤ 1 giây (NFR-02); biểu đồ giữ tối đa 20 chu kỳ gần nhất để không phình bộ nhớ trình duyệt |
| **FR liên quan** | FR-01, FR-02, FR-03, FR-12, FR-15, FR-17 |

> **Vì sao vẫn cần gọi API dù đã có WebSocket.** WebSocket chỉ đẩy dữ liệu **phát sinh sau** khi kết nối được thiết lập. Nếu chỉ dựa vào nó, người dùng mở trang sẽ thấy màn hình trống cho tới khi mẫu đầu tiên về — và trống vô hạn nếu thiết bị đang ngoại tuyến. Các lời gọi API ở bước 2 và 5 dựng **trạng thái ban đầu**, WebSocket lo phần **thay đổi tiếp theo**.

#### 3.2.2 UC-02 — Điều khiển bật/tắt thiết bị

| Thuộc tính | Nội dung |
|---|---|
| **Mã / Tên** | UC-02 — Điều khiển bật/tắt thiết bị |
| **Tác nhân chính** | Người dùng |
| **Tác nhân phụ** | MQTT Broker, Thiết bị IoT |
| **Mô tả** | Người dùng bật hoặc tắt một thiết bị (đèn, quạt) từ giao diện web và nhận xác nhận thực thi từ phần cứng |
| **Độ ưu tiên** | Cao — đây là use case trọng tâm của đồ án |
| **Tần suất** | Cao |
| **Kích hoạt** | Người dùng bấm công tắc của một thiết bị trên Dashboard |
| **Tiền điều kiện** | Broker đang chạy; thiết bị đã kết nối và đang subscribe topic `device_control`; thiết bị tồn tại trong bảng thiết bị |
| **Hậu điều kiện thành công** | Chân GPIO đổi mức logic; `current_state` được cập nhật; một bản ghi lịch sử có trạng thái `SUCCESS` |
| **Hậu điều kiện thất bại** | Bản ghi lịch sử mang trạng thái `FAILED`; `current_state` **không đổi**; giao diện trả công tắc về trạng thái cũ |

**Luồng chính**

| # | Tác nhân | Hành động |
|---|---|---|
| 1 | Người dùng | Bấm công tắc của thiết bị |
| 2 | Frontend | Khóa công tắc chặn bấm trùng, gửi `POST /api/devices/{id}/control` **kèm mã người thao tác** (tùy chọn) |
| 3 | Backend | Kiểm tra thiết bị tồn tại, hành động hợp lệ, và thiết bị không còn lệnh nào đang chờ (BR-04) |
| 4 | Backend | Sinh `request_id` duy nhất |
| 5 | Backend | Ghi bản ghi lịch sử với trạng thái `PENDING`, **lưu kèm người thao tác** (BR-12) |
| 6 | Backend | Publish lệnh lên topic `device_control` với QoS 1 |
| 7 | Broker | Chuyển tiếp lệnh tới thiết bị IoT |
| 8 | Thiết bị IoT | Đặt mức logic chân GPIO: `HIGH` nếu `ON`, `LOW` nếu `OFF` |
| 9 | Thiết bị IoT | Publish xác nhận lên `device_respond` kèm đúng `request_id` |
| 10 | Backend | Đối chiếu `request_id`, cập nhật lịch sử sang `SUCCESS` và cập nhật trạng thái thiết bị |
| 11 | Backend | Phát sự kiện `device.state` tới mọi client qua WebSocket |
| 12 | Frontend | Mở khóa công tắc, cập nhật trạng thái |

**Luồng thay thế**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| A1 | Người dùng bấm lại công tắc khi lệnh trước còn `PENDING` | Công tắc đang bị khóa nên thao tác không có hiệu lực (BR-04) |
| A2 | Một tab trình duyệt khác vừa đổi trạng thái cùng thiết bị | Sự kiện `device.state` đẩy về mọi client; giao diện đồng bộ theo trạng thái mới nhất |
| A3 | Yêu cầu không kèm mã người thao tác — lệnh phát bằng công cụ dòng lệnh hoặc kịch bản kiểm thử | Hệ thống vẫn thực hiện lệnh bình thường; bản ghi lịch sử để trống trường người thao tác, giao diện hiển thị `—` (BR-12) |

**Luồng ngoại lệ**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| E1 | Quá 5 giây không nhận được phản hồi | Cập nhật lịch sử sang `FAILED`, đẩy thông báo lỗi qua WebSocket, giao diện trả công tắc về trạng thái cũ |
| E2 | Không kết nối được tới Broker | Trả HTTP `503`; **không** ghi bản ghi lịch sử |
| E3 | Mã thiết bị không tồn tại | Trả HTTP `404` |
| E4 | Giá trị hành động không thuộc {`ON`, `OFF`} | Trả HTTP `400` |
| E5 | Nhận phản hồi có `request_id` không tồn tại hoặc đã xử lý | Bỏ qua, ghi log cảnh báo |
| E6 | Thiết bị còn một lệnh chưa kết thúc (trạng thái `PENDING`) | Trả HTTP `409`; **không** ghi bản ghi lịch sử; giao diện báo "Thiết bị đang bận" |

| | |
|---|---|
| **Quy tắc nghiệp vụ** | BR-03, BR-04, BR-05, BR-06, BR-12 |
| **Dữ liệu vào** | `device_id`, `action` (`ON`/`OFF`), `user_id` *(tùy chọn)* |
| **Dữ liệu ra** | `request_id`, `status`, `current_state`, người thao tác |
| **Yêu cầu đặc biệt** | Tổng độ trễ từ lúc bấm tới lúc LED đổi trạng thái ≤ 2 giây (NFR-01) |
| **FR liên quan** | FR-04, FR-05, FR-06, FR-08, FR-09, FR-18 |

> **Vì sao có luồng E6.** Đây là phần **máy chủ** của quy tắc BR-04. Khóa công tắc ở giao diện (luồng A1) chỉ có tác dụng trong một tab trình duyệt: nếu người dùng mở hai tab, tab thứ hai không hề biết tab thứ nhất vừa gửi lệnh, vì trạng thái `PENDING` không sinh ra sự kiện WebSocket nào. Hệ thống sẽ sinh ra hai bản ghi `PENDING` cùng hai lệnh MQTT cho một thiết bị. Kiểm tra ở máy chủ là nơi duy nhất chặn được tình huống này. Bản ghi `PENDING` luôn tự thoát sau tối đa 6 giây nhờ cơ chế phát hiện hết giờ, nên `409` không thể khóa thiết bị vĩnh viễn.

#### 3.2.3 UC-03 — Xem lịch sử số liệu cảm biến

| Thuộc tính | Nội dung |
|---|---|
| **Mã / Tên** | UC-03 — Xem lịch sử số liệu cảm biến |
| **Tác nhân chính** | Người dùng |
| **Tác nhân phụ** | — |
| **Mô tả** | Người dùng tra cứu toàn bộ số liệu cảm biến đã ghi nhận dưới dạng bảng |
| **Độ ưu tiên** | Cao |
| **Tần suất** | Trung bình |
| **Kích hoạt** | Người dùng chọn mục "Data Sensor" trên thanh điều hướng |
| **Tiền điều kiện** | Backend đang chạy |
| **Hậu điều kiện thành công** | Bảng dữ liệu hiển thị đúng trang được yêu cầu |
| **Hậu điều kiện thất bại** | Hiển thị thông báo lỗi, không thay đổi trạng thái hệ thống |
| **Điểm mở rộng** | *Sau bước 4* — có thể kích hoạt UC-04 |

**Luồng chính**

| # | Tác nhân | Hành động |
|---|---|---|
| 1 | Người dùng | Chọn mục "Data Sensor" |
| 2 | Hệ thống | Gọi `GET /api/sensors` với tham số mặc định: trang 1, 10 bản ghi/trang, sắp xếp `recorded_at` giảm dần (BR-08, BR-09) |
| 3 | Hệ thống | Hiển thị bảng gồm các cột: **ID · Mã cảm biến · Cảm biến · Giá trị · Đơn vị · Thời gian**. Mỗi dòng là một số đo của một cảm biến; ba dòng của cùng một chu kỳ mang cùng mốc thời gian (BR-11) |
| 4 | Hệ thống | Hiển thị thanh phân trang ở góc dưới bên phải kèm tổng số bản ghi |

**Luồng thay thế**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| A1 | Bảng chưa có bản ghi nào | Hiển thị dòng "Không có dữ liệu"; ẩn thanh phân trang |
| A2 | Người dùng yêu cầu trang vượt quá số trang hiện có | API trả về mã `404` kèm mã lỗi `PAGE_NOT_FOUND`; giao diện **coi đây là trạng thái rỗng**, hiển thị trang trống kèm gợi ý quay lại trang 1 chứ không hiện màn hình lỗi |

**Luồng ngoại lệ**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| E1 | API lỗi hoặc quá thời gian chờ | Hiển thị "Không tải được dữ liệu" kèm nút "Thử lại" |

| | |
|---|---|
| **Quy tắc nghiệp vụ** | BR-08, BR-09, BR-11 |
| **Dữ liệu vào** | `page`, `page_size`, `ordering` (tùy chọn) |
| **Dữ liệu ra** | `count`, `next`, `previous`, `results[]` — mỗi phần tử gồm mã và tên cảm biến, giá trị, đơn vị, mốc thời gian |
| **Yêu cầu đặc biệt** | Phản hồi ≤ 500 ms với bảng tới 100.000 bản ghi (NFR-03) — cần chỉ mục trên `recorded_at` |
| **FR liên quan** | FR-07, FR-10, FR-11, FR-17 |

> **Vì sao có hai cột "Mã cảm biến" và "Cảm biến".** Mã (`room01_temp`) là chuỗi cố định đi trong gói tin MQTT và xuất hiện trong nhật ký hệ thống, cũng là giá trị dùng cho tham số lọc. Tên (`Nhiệt độ phòng`) là thứ người dùng đọc. Cả hai đều là cột chuỗi và ô tìm kiếm tác động tới cả hai, nên gõ `temp` hay `nhiệt` đều ra đúng tập bản ghi.
>
> **Vì sao không còn cột "Node".** Thông tin bo mạch đã chuyển lên bảng danh mục cảm biến nên không lặp lại ở từng dòng số đo. Khi lắp thêm bo mạch thứ hai, người dùng phân biệt qua chính mã cảm biến — `room01_temp` với `room02_temp` — mà không cần thêm cột (FR-16).
>
> **Một trang 10 dòng chỉ chứa 3⅓ chu kỳ.** Đây là hệ quả trực tiếp của việc tách một chu kỳ thành ba dòng: trước đây 10 dòng là 10 mốc thời gian (20 giây dữ liệu), nay chỉ còn khoảng 6 giây. Giao diện vì vậy có sẵn lựa chọn 15 hoặc 30 dòng mỗi trang để một trang chứa được số chu kỳ trọn vẹn.

#### 3.2.4 UC-04 — Tìm kiếm, lọc, sắp xếp, phân trang dữ liệu

| Thuộc tính | Nội dung |
|---|---|
| **Mã / Tên** | UC-04 — Tìm kiếm, lọc, sắp xếp, phân trang dữ liệu |
| **Tác nhân chính** | Người dùng |
| **Tác nhân phụ** | — |
| **Mô tả** | Người dùng thu hẹp và sắp xếp lại tập dữ liệu đang hiển thị trong bảng |
| **Độ ưu tiên** | Trung bình |
| **Tần suất** | Trung bình |
| **Quan hệ** | `«extend»` UC-03 và UC-05 |
| **Kích hoạt** | Người dùng nhập từ khóa, chọn bộ lọc, hoặc bấm vào tiêu đề cột |
| **Tiền điều kiện** | Đang ở màn hình Data Sensor hoặc Action History; bảng đã hiển thị |
| **Hậu điều kiện thành công** | Bảng hiển thị tập dữ liệu đã lọc/sắp xếp, đặt lại về trang 1 |

**Luồng chính**

| # | Tác nhân | Hành động |
|---|---|---|
| 1 | Người dùng | Nhập từ khóa vào ô tìm kiếm và/hoặc chọn khoảng thời gian (từ ngày — đến ngày) |
| 1b | Người dùng | *(tùy chọn, chỉ ở màn hình Data Sensor)* Chọn một cảm biến từ dropdown "Cảm biến" rồi nhập khoảng giá trị, ví dụ *Nhiệt độ phòng, từ 30 trở lên* |
| 1c | Người dùng | *(tùy chọn, chỉ ở màn hình Action History)* Chọn thiết bị, trạng thái, hành động hoặc **người thao tác** từ các dropdown |
| 2 | Frontend | Chờ 300 ms sau lần gõ cuối rồi mới gửi yêu cầu, tránh gọi API liên tục |
| 3 | Hệ thống | Gọi API kèm tham số `search`, `ordering`, khoảng thời gian và — nếu đã chọn cảm biến — mã cảm biến cùng khoảng giá trị |
| 4 | Hệ thống | Trả về dữ liệu đã lọc, đặt lại `page = 1` |
| 5 | Hệ thống | Cập nhật bảng và tổng số bản ghi khớp điều kiện |
| 6 | Người dùng | *(tùy chọn)* Bấm tiêu đề cột để đổi thứ tự sắp xếp — bấm lần đầu tăng dần, bấm lại giảm dần |
| 7 | Người dùng | *(tùy chọn)* Chuyển trang bằng thanh phân trang, giữ nguyên điều kiện lọc |

**Luồng thay thế**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| A1 | Không có bản ghi nào khớp | Hiển thị "Không tìm thấy kết quả phù hợp" kèm nút "Xóa bộ lọc" |
| A2 | Người dùng xóa hết điều kiện lọc | Trở về trạng thái mặc định của UC-03/UC-05 |

**Luồng ngoại lệ**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| E1 | Giá trị nhập vào ô lọc không đúng kiểu (ví dụ chữ cái ở ô giá trị) | Giao diện dùng ô nhập kiểu số nên không gõ được chữ; nếu vẫn gọi API trực tiếp với giá trị sai kiểu thì trả về HTTP `400` |
| E2 | Đầu khoảng lớn hơn cuối khoảng — áp dụng cho **cả khoảng thời gian lẫn khoảng giá trị** | Trả về HTTP `400`; giao diện tô đỏ đúng cặp ô nhập bị sai |
| E3 | `page_size` vượt giới hạn cho phép | Hệ thống tự giới hạn về 100 (BR-08) |
| E4 | Nhập khoảng giá trị mà **chưa chọn cảm biến** | Giao diện để hai ô Từ/Đến ở trạng thái vô hiệu nên không nhập được; nếu vẫn gọi API trực tiếp thì trả về HTTP `400` |

| | |
|---|---|
| **Quy tắc nghiệp vụ** | BR-08, BR-09 |
| **Dữ liệu vào** | `search`, `ordering`, `page`, `page_size`, khoảng thời gian, cảm biến kèm khoảng giá trị, bộ lọc thiết bị / trạng thái / hành động / người thao tác |
| **Dữ liệu ra** | Tập bản ghi đã lọc kèm thông tin phân trang |
| **Yêu cầu đặc biệt** | Điều kiện lọc phải được giữ nguyên khi chuyển trang |
| **FR liên quan** | FR-10, FR-11 |

> **Vì sao có luồng E4.** Ba cảm biến đo ba đại lượng có **đơn vị khác nhau**. Điều kiện "giá trị từ 28 đến 30" áp chung cho cả bảng sẽ gộp *28 °C* với *28 lux* vào cùng một tập kết quả — một con số vô nghĩa. Vì vậy hai ô nhập khoảng giá trị chỉ mở ra sau khi người dùng đã chọn một cảm biến, và giao diện có một dòng chú thích giải thích điều này ngay cạnh bộ lọc.
>
> **Một bẫy của mô hình cũ đã biến mất.** Trước đây, khi lọc theo khoảng giá trị của một cột, các bản ghi có cột đó rỗng bị loại khỏi kết quả ở **cả hai chiều** so sánh — vì trong SQL mọi phép so sánh với giá trị rỗng đều không thỏa mãn. Hệ quả là tổng số bản ghi nhỏ hơn người dùng dự đoán mà không có thông báo lỗi nào. Từ khi mỗi số đo là một bản ghi riêng và cột giá trị không cho phép rỗng, hiện tượng này không còn.

#### 3.2.5 UC-05 — Xem lịch sử thao tác thiết bị

| Thuộc tính | Nội dung |
|---|---|
| **Mã / Tên** | UC-05 — Xem lịch sử thao tác thiết bị |
| **Tác nhân chính** | Người dùng |
| **Tác nhân phụ** | — |
| **Mô tả** | Người dùng tra cứu toàn bộ các lần bật/tắt thiết bị đã thực hiện kèm kết quả thực thi |
| **Độ ưu tiên** | Cao |
| **Tần suất** | Trung bình |
| **Kích hoạt** | Người dùng chọn mục "Action History"; hoặc được gọi tự động bởi UC-02 để ghi bản ghi |
| **Tiền điều kiện** | Backend đang chạy |
| **Hậu điều kiện thành công** | Bảng lịch sử thao tác hiển thị đúng trang được yêu cầu |
| **Điểm mở rộng** | *Sau bước 3* — có thể kích hoạt UC-04 |

**Luồng chính**

| # | Tác nhân | Hành động |
|---|---|---|
| 1 | Người dùng | Chọn mục "Action History" |
| 2 | Hệ thống | Gọi `GET /api/actions` với tham số mặc định (trang 1, 10 bản ghi, `created_at` giảm dần) |
| 3 | Hệ thống | Hiển thị bảng gồm các cột: **ID · Thiết bị · Hành động · Người thao tác · Trạng thái · Độ trễ · Thời gian** |
| 4 | Hệ thống | Tô màu trạng thái để dễ đọc: `SUCCESS` xanh · `FAILED` đỏ · `PENDING` vàng |

**Luồng thay thế**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| A1 | Chưa có thao tác nào | Hiển thị "Chưa có thao tác nào được thực hiện" |
| A2 | Có bản ghi đang ở trạng thái `PENDING` | Hiển thị biểu tượng đang chờ; tự cập nhật riêng dòng đó khi nhận sự kiện WebSocket, không tải lại cả bảng |
| A3 | Bản ghi không xác định được người thao tác (BR-12) | Cột "Người thao tác" hiển thị dấu `—` |

**Luồng ngoại lệ**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| E1 | API lỗi hoặc quá thời gian chờ | Hiển thị "Không tải được dữ liệu" kèm nút "Thử lại" |

| | |
|---|---|
| **Quy tắc nghiệp vụ** | BR-05, BR-08, BR-09, BR-12 |
| **Dữ liệu vào** | `page`, `page_size`, `ordering`, bộ lọc (tùy chọn, gồm cả lọc theo người thao tác) |
| **Dữ liệu ra** | `id`, mã và tên thiết bị, `action`, người thao tác *(có thể rỗng)*, `status`, `created_at`, `responded_at`, `latency_ms` |
| **Yêu cầu đặc biệt** | Không được mất bản ghi kể cả khi lệnh thất bại (NFR-06) |
| **FR liên quan** | FR-08, FR-10, FR-11, FR-18 |

> **Vì sao có cột "Người thao tác".** Cột này trả lời trực tiếp câu hỏi *ai đã bật cái đèn này* (FR-18) — thứ mà bảng lịch sử của mô hình cũ không cho biết. Cột "Thiết bị" hiển thị cả mã lẫn tên (`room01_lamp · Đèn phòng`) vì mã là thứ đi trong gói tin MQTT và xuất hiện trong nhật ký hệ thống, còn tên là thứ người dùng đọc.
>
> Bản ghi không xác định được người thao tác hiển thị dấu `—`. Giao diện **không** ghi "Hệ thống" hay "Ẩn danh": hai chữ đó gợi ý rằng tồn tại một tài khoản mang tên như vậy, trong khi sự thật là không biết ai. Màn hình cũng có bộ lọc riêng cho phép liệt kê đúng nhóm bản ghi này.

> **Vì sao có cột "Độ trễ".** Cột này hiển thị `latency_ms` — khoảng cách giữa `created_at` và `responded_at`, do API tính chứ không lưu thành cột trong cơ sở dữ liệu. Nó là **bằng chứng đo được của NFR-01** ngay trên giao diện: lệnh thành công thường vài trăm mili-giây, còn lệnh hết giờ luôn rơi vào dải 5.000–6.000 ms, đúng như BR-03 kèm chu kỳ quét 1 giây. Bản ghi còn `PENDING` chưa có `responded_at` nên ô này để dấu `—`.

#### 3.2.6 UC-06 — Xem trang Profile

| Thuộc tính | Nội dung |
|---|---|
| **Mã / Tên** | UC-06 — Xem trang Profile |
| **Tác nhân chính** | Người dùng (chủ yếu là giảng viên chấm bài) |
| **Tác nhân phụ** | — |
| **Mô tả** | Hiển thị thông tin sinh viên thực hiện và các liên kết tới sản phẩm bàn giao |
| **Độ ưu tiên** | Thấp |
| **Tần suất** | Thấp |
| **Kích hoạt** | Người dùng chọn mục "Profile" |
| **Tiền điều kiện** | Không |
| **Hậu điều kiện thành công** | Trang hiển thị đầy đủ thông tin và 4 liên kết hoạt động |

**Luồng chính**

| # | Tác nhân | Hành động |
|---|---|---|
| 1 | Người dùng | Chọn mục "Profile" |
| 2 | Hệ thống | Hiển thị ảnh đại diện, họ tên, MSSV, lớp, tên đề tài, tên giảng viên hướng dẫn |
| 3 | Hệ thống | Hiển thị 4 liên kết: **GitHub repository · Báo cáo PDF · Figma design · API docs (Swagger/Postman)** |
| 4 | Người dùng | Bấm một liên kết, hệ thống mở trang đích ở tab mới |

**Luồng ngoại lệ**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| E1 | Một liên kết chưa được cấu hình | Hiển thị nút ở trạng thái vô hiệu kèm chú thích "Đang cập nhật" |

| | |
|---|---|
| **Quy tắc nghiệp vụ** | — |
| **Dữ liệu vào** | Không có |
| **Dữ liệu ra** | Thông tin sinh viên, thông tin đề tài và các đường dẫn |
| **Yêu cầu đặc biệt** | Nội dung lấy từ cấu hình (`.env`), không viết cứng trong mã Frontend |
| **FR liên quan** | FR-13 |

> Use case này là use case duy nhất **không có biểu đồ tuần tự riêng** ở mục 3.4: nó chỉ gồm một lời gọi `GET /api/profile` trả về dữ liệu tĩnh đọc từ file cấu hình, không có tương tác nhiều bước nào để vẽ.

#### 3.2.7 UC-07 — Thu thập và truyền số liệu cảm biến *(tự động)*

| Thuộc tính | Nội dung |
|---|---|
| **Mã / Tên** | UC-07 — Thu thập và truyền số liệu cảm biến |
| **Tác nhân chính** | Thiết bị IoT (ESP8266) |
| **Tác nhân phụ** | MQTT Broker |
| **Mô tả** | Thiết bị tự động đọc cảm biến theo chu kỳ, đóng gói và gửi số liệu về hệ thống để lưu trữ và hiển thị |
| **Độ ưu tiên** | Cao |
| **Tần suất** | Rất cao — mỗi 2 giây, khoảng 43.200 gói tin mỗi ngày, sinh ra 129.600 bản ghi |
| **Kích hoạt** | Bộ định thời trên thiết bị (BR-01) |
| **Tiền điều kiện** | ESP8266 đã kết nối WiFi và Broker; MQTT worker đang chạy và subscribe `data_sensors` |
| **Hậu điều kiện thành công** | **Một bản ghi cho mỗi cảm biến đọc được**, tất cả mang cùng một mốc thời gian (BR-11); sự kiện `sensor.data` được phát tới mọi client |
| **Hậu điều kiện thất bại** | Không ghi bản ghi; ghi log lỗi; hệ thống vẫn hoạt động bình thường |

**Luồng chính**

| # | Tác nhân | Hành động |
|---|---|---|
| 1 | Thiết bị IoT | Đọc nhiệt độ và độ ẩm từ DHT11 |
| 2 | Thiết bị IoT | Đọc giá trị analog từ quang trở (chân A0) và quy đổi ra lux |
| 3 | Thiết bị IoT | Đóng gói dữ liệu thành chuỗi JSON kèm `device_id` |
| 4 | Thiết bị IoT | Publish lên topic `data_sensors` với QoS 0 |
| 5 | Broker | Chuyển tiếp message tới MQTT worker đang subscribe |
| 6 | Backend | Phân tích JSON; **tra danh mục cảm biến** theo cặp *(mã bo mạch, đại lượng đo)* để tìm cảm biến ứng với từng trường số đo |
| 7 | Backend | Kiểm tra từng số đo với ngưỡng hợp lệ **riêng của cảm biến đó** (BR-02) |
| 8 | Backend | Tính mốc thời gian **một lần**, rồi ghi **mỗi số đo thành một bản ghi** trong cùng một giao dịch (BR-11) |
| 9 | Backend | Gửi sự kiện `sensor.data` qua Redis channel layer để phát ra WebSocket — **một sự kiện cho cả chu kỳ**, không phải ba |

**Luồng thay thế**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| A1 | Đọc DHT11 trả về `NaN` | Bỏ qua chu kỳ này, không publish, ghi log trên Serial Monitor |
| A2 | Chỉ đọc được một phần cảm biến | Vẫn publish phần đọc được; Backend ghi bản ghi cho các cảm biến có số đo và **không ghi gì** cho cảm biến bị lỗi. Trên biểu đồ, đường của cảm biến đó đứt một đoạn tại mốc tương ứng |

**Luồng ngoại lệ**

| Mã | Điều kiện | Xử lý |
|---|---|---|
| E1 | Mất kết nối WiFi | Thiết bị thử kết nối lại mỗi 5 giây; dữ liệu trong thời gian mất kết nối bị bỏ qua (không có bộ đệm) |
| E2 | Mất kết nối Broker | Tự động kết nối lại trong vòng lặp chính, giữ nguyên client ID |
| E3 | Một số đo vượt ngưỡng hợp lệ của cảm biến tương ứng (BR-02) | Backend loại bỏ **đúng số đo đó** và ghi log cảnh báo kèm nội dung message gốc; các số đo còn lại trong cùng chu kỳ vẫn được lưu |
| E4 | Message không phải JSON hợp lệ | Backend bỏ qua, ghi log, **không** làm dừng tiến trình worker |
| E5 | Gói tin có trường số đo không khớp cảm biến nào trong danh mục | Backend bỏ qua trường đó, ghi log một lần; các trường còn lại xử lý bình thường |

| | |
|---|---|
| **Quy tắc nghiệp vụ** | BR-01, BR-02, BR-11 |
| **Dữ liệu vào** | Tín hiệu từ DHT11 và quang trở |
| **Dữ liệu ra** | JSON gồm `device_id`, `temperature`, `humidity`, `light` — **gói tin của firmware không đổi**, việc tách thành ba bản ghi do Backend đảm nhiệm |
| **Yêu cầu đặc biệt** | Worker phải tự phục hồi sau lỗi, không được dừng vì một message hỏng (NFR-16). Danh mục cảm biến nạp vào bộ nhớ một lần lúc khởi động, nên thêm hoặc sửa cảm biến phải khởi động lại worker |
| **FR liên quan** | FR-01, FR-07, FR-12, FR-14, FR-17 |

> **Vì sao luồng A2 tồn tại.** DHT11 và quang trở là hai cảm biến độc lập; hỏng một cái không có nghĩa là mất cả chu kỳ đo. Hệ thống ghi bản ghi cho các cảm biến đọc được và **không ghi gì** cho cảm biến lỗi. Ở mô hình cũ, ba số đo nằm chung một dòng nên phải ghi một dòng có ô rỗng — kéo theo nhiều hệ quả khó giải thích khi lọc dữ liệu (mục 3.2.4). Nay "không đo được" thể hiện bằng **sự vắng mặt của bản ghi**, đúng nghĩa hơn.
>
> **Vì sao ba số đo phải mang cùng một mốc thời gian.** Biểu đồ trên Dashboard xoay bảng theo mốc thời gian: mỗi mốc là một điểm trên trục hoành, ba đường lấy giá trị tại mốc đó. Nếu ba bản ghi lệch nhau dù chỉ vài phần nghìn giây, mỗi mốc chỉ còn một đường có dữ liệu — biểu đồ vỡ hoàn toàn. Đây cũng là lý do backend tách một chu kỳ thành ba bản ghi, thay vì để firmware gửi ba gói tin riêng: ba gói tin sẽ tới ở ba thời điểm khác nhau.

### 3.3 Quy tắc nghiệp vụ

| Mã | Quy tắc |
|---|---|
| BR-01 | Thiết bị gửi số liệu theo chu kỳ **2 giây** |
| BR-02 | Mỗi cảm biến có **ngưỡng hợp lệ riêng** lưu trong danh mục. Giá trị hiện hành: nhiệt độ −10→60 °C, độ ẩm 0→100 %, ánh sáng 0→2000 lux. Số đo ngoài ngưỡng bị loại bỏ — **chỉ số đo đó**, không phải cả chu kỳ |
| BR-03 | Quá **5 giây** không nhận được phản hồi thì lệnh bị coi là thất bại |
| BR-04 | Trong lúc một lệnh đang chờ, thiết bị đó không nhận lệnh mới — giao diện khóa công tắc, **và** máy chủ từ chối yêu cầu trùng bằng `409 DEVICE_BUSY` |
| BR-05 | Mỗi lệnh điều khiển sinh **đúng một** bản ghi lịch sử, bất kể thành công hay thất bại |
| BR-06 | `request_id` là duy nhất trong toàn hệ thống |
| BR-07 | Thiết bị bị coi là **ngoại tuyến** nếu không có số liệu mới trong **30 giây** |
| BR-08 | Phân trang mặc định **10 bản ghi/trang**, tối đa **100** |
| BR-09 | Thứ tự sắp xếp mặc định: **thời gian giảm dần** |
| BR-10 | Biểu đồ trên Dashboard hiển thị **20 chu kỳ gần nhất** |
| BR-11 | Mỗi số đo của mỗi cảm biến được lưu thành **một bản ghi riêng**. Các số đo trong cùng một chu kỳ mang **cùng một mốc thời gian**, và một cảm biến không thể có hai số đo tại cùng một thời điểm |
| BR-12 | Mỗi lệnh điều khiển ghi lại **người thao tác**. Lệnh không xác định được người phát ra thì để trống trường này và giao diện hiển thị `—` |

### 3.4 Biểu đồ tuần tự

Sáu biểu đồ tuần tự mô tả các luồng nghiệp vụ chính. Luồng điều khiển thiết bị được vẽ **hai lần** ở hai mức trừu tượng khác nhau: mức nghiệp vụ coi backend là một hộp đen, mức triển khai mở hộp đen đó thành hai tiến trình.

#### 3.4.1 Điều khiển thiết bị — mức nghiệp vụ

![Sequence điều khiển thiết bị mức nghiệp vụ](docs/img/SD01_DieuKhienThietBi_NghiepVu.png){ width=95% }

*Hình 3.2. Biểu đồ tuần tự — điều khiển thiết bị (mức nghiệp vụ)*

Điểm đáng chú ý: bước gửi phản hồi HTTP xảy ra **ngay sau khi publish lệnh**, không chờ phần cứng xác nhận. Máy chủ trả về mã `202 Accepted` mang nghĩa "đã tiếp nhận, kết quả sẽ có sau", còn kết quả thật đi về theo đường WebSocket. Nếu chờ phản hồi rồi mới trả lời, mỗi lần bấm công tắc sẽ chiếm một luồng xử lý của máy chủ trong tối đa 5 giây.

#### 3.4.2 Điều khiển thiết bị — mức triển khai

![Sequence điều khiển thiết bị mức triển khai](docs/img/SD-02_Dieukhienbattatthietbi.png){ width=95% }

*Hình 3.3. Biểu đồ tuần tự — điều khiển thiết bị (mức triển khai)*

Biểu đồ này cho thấy ba điểm chỉ nhìn được ở mức tiến trình: lệnh đi ra từ P1 nhưng phản hồi về ở P2; Redis là cầu nối bắt buộc để P2 đẩy được dữ liệu ra WebSocket; và P1 tạo một client MQTT ngắn hạn cho mỗi lần gọi API thay vì dùng chung kết nối với P2.

#### 3.4.3 Thu thập số liệu cảm biến

![Sequence thu thập số liệu](docs/img/SD03_ThuThapSoLieu.png){ width=95% }

*Hình 3.4. Biểu đồ tuần tự — thu thập và truyền số liệu cảm biến*

#### 3.4.4 Mở Dashboard và thiết lập realtime

![Sequence mở Dashboard](docs/img/SD-04.png){ width=95% }

*Hình 3.5. Biểu đồ tuần tự — mở Dashboard và thiết lập kênh realtime*

Dashboard gọi **bốn API HTTP** để dựng trạng thái ban đầu — danh mục cảm biến, số đo mới nhất, dữ liệu biểu đồ và danh sách thiết bị — sau đó mới mở WebSocket để nhận các thay đổi tiếp theo. WebSocket chỉ đẩy dữ liệu phát sinh **sau** khi kết nối được thiết lập — nếu chỉ dựa vào nó, người dùng mở trang sẽ thấy màn hình trống cho tới khi mẫu dữ liệu đầu tiên về, và trống vô hạn nếu thiết bị đang ngoại tuyến.

#### 3.4.5 Phát hiện timeout 5 giây

![Sequence phát hiện timeout](docs/img/SD-05.png){ width=95% }

*Hình 3.6. Biểu đồ tuần tự — phát hiện lệnh quá thời gian chờ*

Cơ chế phát hiện timeout đặt ở **vòng quét chạy mỗi giây trong tiến trình worker**, không dùng bộ hẹn giờ trong tiến trình web. Lý do: bộ hẹn giờ sống trong bộ nhớ, khởi động lại máy chủ là mất sạch và các bản ghi chờ sẽ mắc kẹt vĩnh viễn. Vòng quét đọc trạng thái từ CSDL nên **tự phục hồi** sau khi khởi động lại.

Hệ quả cần lưu ý: độ trễ thực tế là **5–6 giây chứ không phải đúng 5**, vì một bản ghi vừa hết hạn ngay sau khi vòng quét đi qua sẽ phải chờ tới lượt sau.

#### 3.4.6 Tra cứu lịch sử có lọc và phân trang

![Sequence tra cứu lịch sử](docs/img/SD-06.png){ width=95% }

*Hình 3.7. Biểu đồ tuần tự — tra cứu lịch sử có lọc và phân trang*

### 3.5 Thiết kế giao diện

Giao diện gồm 4 màn hình, bố cục chung là thanh điều hướng dọc bên trái và vùng nội dung bên phải.

| ⬛ CHÈN HÌNH 3.8 |
|---|
| **Cần chèn:** ảnh chụp thiết kế Figma màn hình **Dashboard** — 3 thẻ số liệu, biểu đồ đường, panel công tắc thiết bị. **Kích thước:** ngang 15 cm. |

*Hình 3.8. Thiết kế màn hình Dashboard*

| ⬛ CHÈN HÌNH 3.9 |
|---|
| **Cần chèn:** ảnh chụp Figma màn hình **Data Sensor** — ô tìm kiếm, dropdown chọn cảm biến, 2 ô nhập khoảng giá trị *(ở trạng thái vô hiệu khi chưa chọn cảm biến)*, 2 ô chọn ngày, dòng chú thích giải thích ràng buộc đó, bảng 6 cột (ID · Mã cảm biến · Cảm biến · Giá trị · Đơn vị · Thời gian) với **ba dòng liên tiếp cùng một mốc thời gian**, thanh phân trang. |

*Hình 3.9. Thiết kế màn hình Data Sensor*

| ⬛ CHÈN HÌNH 3.10 |
|---|
| **Cần chèn:** ảnh chụp Figma màn hình **Action History** — bảng 7 cột (ID · Thiết bị · Hành động · **Người thao tác** · Trạng thái · Độ trễ · Thời gian), trạng thái tô màu (`SUCCESS` xanh, `FAILED` đỏ, `PENDING` vàng), cột Độ trễ để `—` với bản ghi còn `PENDING`, và **ít nhất một dòng có cột Người thao tác để `—`** để minh họa lệnh không xác định được người phát ra. |

*Hình 3.10. Thiết kế màn hình Action History*

| ⬛ CHÈN HÌNH 3.11 |
|---|
| **Cần chèn:** ảnh chụp Figma màn hình **Profile** — ảnh đại diện, thông tin sinh viên, 4 nút liên kết. |

*Hình 3.11. Thiết kế màn hình Profile*

**Liên kết Figma:** `<điền link Figma tại đây>`

### 3.6 Thiết kế API

#### 3.6.1 Quy ước chung

| Mục | Quy ước |
|---|---|
| Địa chỉ gốc | `http://localhost:8000/api` |
| Định dạng | JSON, tên trường `snake_case` |
| Mốc thời gian | ISO-8601 theo giờ UTC, kết thúc bằng `Z` |
| Xác thực | Không — chưa có màn hình đăng nhập, hệ thống chạy trong mạng LAN. Người thao tác được nêu kèm trong thân yêu cầu điều khiển (FR-18) |
| Phân trang | `{ count, next, previous, results }`, mặc định 10 bản ghi/trang |
| Cấu trúc lỗi | `{ "error": { "code", "message", "details" } }` |

#### 3.6.2 Bảng tổng hợp endpoint

| # | Phương thức | Đường dẫn | Chức năng | UC |
|---|---|---|---|---|
| 1 | `GET` | `/api/sensors/devices` | Danh mục cảm biến | UC-01, UC-03 |
| 2 | `GET` | `/api/sensors/latest` | Số đo mới nhất **của từng cảm biến** — trả về một mảng | UC-01 |
| 3 | `GET` | `/api/sensors/chart` | N chu kỳ gần nhất cho biểu đồ | UC-01 |
| 4 | `GET` | `/api/sensors` | Bảng số đo, có lọc/sắp xếp/phân trang | UC-03, UC-04 |
| 5 | `GET` | `/api/devices` | Danh sách thiết bị kèm trạng thái | UC-01 |
| 6 | `POST` | `/api/devices/{id}/control` | Gửi lệnh bật/tắt, kèm mã người thao tác *(tùy chọn)* | UC-02 |
| 7 | `GET` | `/api/actions` | Bảng lịch sử thao tác | UC-05, UC-04 |
| 8 | `GET` | `/api/profile` | Thông tin sinh viên và liên kết bàn giao | UC-06 |
| 9 | `WS` | `/ws/realtime/` | Kênh đẩy sự kiện thời gian thực | UC-01, UC-02 |

Bảng có 9 dòng nhưng hệ thống chỉ có **8 endpoint REST**: dòng số 9 là một kênh WebSocket, không phải endpoint HTTP. Đây cũng là lý do trang tài liệu Swagger sinh tự động chỉ liệt kê 8 mục (kịch bản T-17 ở mục 4.2) — chuẩn OpenAPI chỉ mô tả được giao thức HTTP, không mô tả được WebSocket và MQTT. Hai giao diện đó được đặc tả bằng tay ở mục 3.6.4 và 2.3.2.

Endpoint số 1 là điểm mở rộng đáng chú ý: giao diện dựng ba thẻ số liệu trên Dashboard và danh sách lựa chọn trong bộ lọc **từ dữ liệu trả về của endpoint này**, không ghi cứng ba đại lượng trong mã. Lắp thêm cảm biến thứ tư thì giao diện tự có thêm thẻ và thêm lựa chọn.

#### 3.6.3 Tham số truy vấn dùng chung

Hai endpoint dạng bảng — `/api/sensors` và `/api/actions` — dùng chung một bộ tham số, hiện thực UC-04:

| Tham số | Kiểu | Mặc định | Ghi chú |
|---|---|---|---|
| `page` | số nguyên | `1` | Vượt quá tổng số trang → `404 PAGE_NOT_FOUND` |
| `page_size` | số nguyên | `10` | Cho phép 1 → 100; lớn hơn 100 thì **tự hạ về 100**, không báo lỗi (BR-08) |
| `search` | chuỗi | — | Khớp một phần, không phân biệt hoa thường |
| `ordering` | chuỗi | theo từng endpoint | Tiền tố `-` nghĩa là giảm dần; chỉ nhận các cột được liệt kê sẵn |

Bộ lọc riêng của từng endpoint:

| Endpoint | Tham số lọc |
|---|---|
| `/api/sensors` | `sensor` · `node` · `recorded_at__gte` / `__lte` · `value__gte` / `__lte` |
| `/api/actions` | `device` · `user` · `status` · `action` · `created_at__gte` / `__lte` |

Mọi điều kiện nối với nhau bằng phép **và**.

**Hai tham số khoảng giá trị bắt buộc phải đi kèm tham số chọn cảm biến.** Ba cảm biến đo ba đại lượng có đơn vị khác nhau, nên điều kiện "giá trị từ 28 đến 30" áp cho cả bảng sẽ gộp *28 °C* với *28 lux* vào cùng một tập kết quả. Thiếu tham số `sensor` thì máy chủ trả về lỗi `400`; giao diện phản ánh ràng buộc này bằng cách để hai ô nhập ở trạng thái vô hiệu cho tới khi người dùng chọn cảm biến (mục 3.2.4, luồng E4).

So với mô hình dữ liệu cũ, bộ lọc gọn đi một nửa: sáu tham số theo từng cột số đo nay gộp thành hai, vì cột đại lượng đã trở thành một khóa ngoại thay vì ba cột riêng biệt.

Ô tìm kiếm của `/api/sensors` tác động lên **hai cột chuỗi** — mã cảm biến và tên cảm biến — nên gõ `temp` hay `nhiệt` đều ra đúng tập bản ghi. Ở mô hình cũ, bảng số liệu chỉ có đúng một cột chuỗi là mã bo mạch, khiến ô tìm kiếm gần như không dùng được.

Tham số `user` của `/api/actions` nhận thêm một giá trị đặc biệt để liệt kê các lệnh **không xác định được người thao tác**. Không có giá trị này thì không có cách nào lọc ra nhóm bản ghi đó, vì tham số bỏ trống được hiểu là "không lọc" chứ không phải "lọc lấy dòng rỗng".

**Mốc thời gian gửi lên phải kèm múi giờ**, ví dụ `2026-08-17T00:00:00+07:00`. Chuỗi thiếu múi giờ sẽ bị hiểu là giờ UTC, khiến khoảng "từ 0 giờ" thực chất bắt đầu từ 7 giờ sáng — sai lệch 7 tiếng mà không có thông báo lỗi nào.

#### 3.6.4 Bảng mã lỗi toàn hệ thống

Mọi phản hồi lỗi đều mang cùng một hình dạng `{ "error": { "code", "message", "details" } }`, trong đó `code` là mã ổn định để giao diện rẽ nhánh, còn `message` là câu tiếng Việt hiển thị được ngay. Toàn hệ thống dùng đúng **7 mã**:

| Mã lỗi | HTTP | Khi nào xảy ra | Luồng use case |
|---|---|---|---|
| `VALIDATION_ERROR` | `400` | Thân yêu cầu hoặc tham số truy vấn sai kiểu, sai giá trị | UC-02 E4, UC-04 E1 |
| `INVALID_RANGE` | `400` | Đầu khoảng lớn hơn cuối khoảng — dùng chung cho cả khoảng thời gian lẫn khoảng giá trị số | UC-04 E2 |
| `NOT_FOUND` | `404` | Không có tài nguyên tương ứng | UC-02 E3 |
| `PAGE_NOT_FOUND` | `404` | Số trang vượt quá tổng số trang | UC-03 A2 |
| `DEVICE_BUSY` | `409` | Thiết bị còn một lệnh chưa kết thúc | UC-02 E6 |
| `BROKER_UNAVAILABLE` | `503` | Không kết nối hoặc không publish được lên Broker | UC-02 E2 |
| `INTERNAL_ERROR` | `500` | Lỗi không lường trước phía máy chủ | — |

Dùng một mã `INVALID_RANGE` chung cho cả hai loại khoảng, thay vì tách thành hai mã, để giao diện chỉ cần một nhánh xử lý; muốn biết ô nào nhập sai thì đọc trường `details`.

#### 3.6.5 Đặc tả endpoint trọng tâm

**`POST /api/devices/{id}/control`** — gửi lệnh bật/tắt thiết bị.

Thân yêu cầu:

```json
{ "action": "ON", "user_id": 1 }
```

Trường `user_id` là **tùy chọn** (FR-18, BR-12). Phạm vi đề tài chưa có màn hình đăng nhập nên máy chủ không có cách nào tự suy ra ai đang thao tác; ép trường này bắt buộc sẽ chặn luôn các đường gọi hợp lệ khác như lệnh thử bằng công cụ dòng lệnh hay kịch bản kiểm thử tự động. Trường này nằm trong **thân yêu cầu** chứ không phải phần đầu HTTP vì nó là **dữ liệu nghiệp vụ** được ghi vào bản ghi lịch sử, không phải thông tin xác thực; khi bổ sung đăng nhập ở giai đoạn sau, danh tính sẽ lấy từ phiên làm việc và trường này bị bỏ đi.

Phản hồi `202 Accepted`:

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

Các mã lỗi:

| HTTP | Mã lỗi | Điều kiện | Có ghi lịch sử không? |
|---|---|---|---|
| `400` | `VALIDATION_ERROR` | Thiếu `action`, giá trị ngoài {`ON`,`OFF`}, hoặc `user_id` trỏ tới người dùng không tồn tại | Không |
| `404` | `NOT_FOUND` | Thiết bị không tồn tại hoặc đã tháo | Không |
| `409` | `DEVICE_BUSY` | Thiết bị còn một lệnh chưa kết thúc | Không |
| `503` | `BROKER_UNAVAILABLE` | Không kết nối được tới Broker | **Không** — bản ghi bị cuộn ngược |

Toàn bộ xử lý nằm trong một giao dịch CSDL. Điều này cần thiết vì luồng chính ghi bản ghi `PENDING` **trước** khi publish, nhưng đặc tả lại yêu cầu broker hỏng thì không được để lại bản ghi nào — chỉ có cơ chế cuộn ngược giao dịch mới dung hòa được hai điều này.

**Ví dụ gọi bằng dòng lệnh:**

```bash
curl -X POST http://localhost:8000/api/devices/1/control \
     -H "Content-Type: application/json" \
     -d '{"action":"ON"}'
```

#### 3.6.6 Giao diện WebSocket

Kênh `/ws/realtime/` là kênh **một chiều** từ máy chủ tới trình duyệt, dùng đúng **hai loại sự kiện**:

```json
// sensor.data — phát mỗi khi ghi thành công một bản ghi cảm biến
{ "type": "sensor.data", "device_id": "esp8266_room01",
  "temperature": 28.5, "humidity": 72.0, "light": 350,
  "recorded_at": "2026-08-17T10:30:02.451231Z" }

// device.state — phát khi một lệnh điều khiển kết thúc
{ "type": "device.state", "device_id": 1, "device": "room01_lamp",
  "current_state": "ON", "request_id": "3f2b8c1e-…",
  "status": "SUCCESS", "error_message": null }
```

Trường hợp lệnh thất bại vì hết thời gian chờ **không sinh ra sự kiện thứ ba**, mà dùng lại `device.state` với `status` là `FAILED` và `error_message` có nội dung. Nhờ vậy giao diện chỉ cần **một** hàm xử lý duy nhất cho mọi kết cục của một lệnh: đối chiếu `request_id`, mở khóa công tắc, rồi đặt trạng thái theo giá trị nhận được.

Kênh này là **một chiều**: message do trình duyệt gửi lên sẽ bị bỏ qua và chỉ ghi log. Việc điều khiển thiết bị vẫn đi bằng `POST` qua HTTP, vì nó cần trả về được các mã lỗi `400` / `404` / `409` / `503` ở mục 3.6.4 — thứ mà WebSocket không có sẵn cơ chế biểu diễn.

Bốn quy tắc phía giao diện gắn với kênh này:

| # | Quy tắc | Nguồn |
|---|---|---|
| 1 | Mở WebSocket **sau khi** các lời gọi HTTP ban đầu hoàn tất | UC-01 |
| 2 | Đứt kết nối thì thử lại mỗi 5 giây; kết nối lại được thì gọi lại API số liệu mới nhất để bù khoảng trống | UC-01 E1 |
| 3 | Quá 30 giây không nhận `sensor.data` thì hiện nhãn "Thiết bị ngoại tuyến" | BR-07 |
| 4 | Mỗi lệnh có một bộ đếm dự phòng khoảng 7 giây, phòng trường hợp WebSocket đứt đúng lúc lệnh đang chạy — hết giờ thì tự mở khóa công tắc và gọi lại danh sách thiết bị để lấy trạng thái thật | BR-03 |

Quy tắc số 4 tồn tại vì nếu thiếu nó, một lần đứt kết nối đúng thời điểm sẽ khiến công tắc bị khóa vĩnh viễn: sự kiện `device.state` báo kết thúc lệnh sẽ không bao giờ tới nơi.

---

## 4. KẾT QUẢ THỬ NGHIỆM VÀ KẾT LUẬN

> **Ghi chú:** chương này là khung để điền sau khi hoàn thành lập trình và chạy thử. Các bảng kịch bản đã được chuẩn bị sẵn, chỉ cần bổ sung cột kết quả và ảnh chụp màn hình.

### 4.1 Môi trường thử nghiệm

| Thành phần | Cấu hình |
|---|---|
| Máy chủ | `<hệ điều hành, CPU, RAM>` |
| Phiên bản phần mềm | Python `<…>` · Django `<…>` · PostgreSQL `<…>` · Redis `<…>` · Mosquitto `<…>` |
| Thiết bị | ESP8266 NodeMCU, firmware biên dịch bằng Arduino IDE `<…>` |
| Mạng | WiFi 2.4 GHz, `<tên mạng>` |
| Trình duyệt | `<Chrome/Edge phiên bản …>` |
| Thời gian chạy thử | `<ngày … tới ngày …>` |

### 4.2 Kết quả kiểm thử chức năng

| # | Kịch bản | Kết quả mong đợi | Kết quả thực tế | Đạt |
|---|---|---|---|---|
| T-01 | Bật hệ thống, quan sát Dashboard | 3 thẻ hiển thị số liệu, tự cập nhật mỗi 2 giây | | |
| T-02 | Hà hơi vào cảm biến DHT11 | Độ ẩm tăng rõ rệt trong ≤ 2 giây | | |
| T-03 | Che quang trở bằng tay | Giá trị ánh sáng giảm rõ rệt trong ≤ 2 giây | | |
| T-04 | Bấm bật "Đèn" trên giao diện | LED 1 sáng trong ≤ 2 giây, công tắc chuyển ON | | |
| T-05 | Bấm tắt "Đèn" | LED 1 tắt, công tắc chuyển OFF | | |
| T-06 | Bật/tắt "Quạt" | Chỉ LED 2 đổi trạng thái, LED 1 không bị ảnh hưởng | | |
| T-07 | Rút nguồn ESP8266 rồi bấm bật đèn | Sau 5–6 giây hiện thông báo lỗi, lịch sử ghi `FAILED` | | |
| T-08 | Mở trang Data Sensor | Bảng hiển thị đủ 6 cột (ID · Mã cảm biến · Cảm biến · Giá trị · Đơn vị · Thời gian), phân trang hoạt động | | |
| T-08b | Quan sát ba dòng liên tiếp của cùng một chu kỳ | Ba dòng mang **cùng một mốc thời gian**, thứ tự Nhiệt độ → Độ ẩm → Ánh sáng | | |
| T-09 | Lọc số liệu theo khoảng thời gian | Chỉ hiển thị bản ghi trong khoảng đã chọn | | |
| T-10 | Chọn cảm biến "Nhiệt độ phòng" rồi bấm tiêu đề cột "Giá trị" | Sắp xếp tăng dần, bấm lần nữa thì giảm dần | | |
| T-10b | Chưa chọn cảm biến, thử nhập khoảng giá trị | Hai ô Từ/Đến ở trạng thái vô hiệu, không nhập được | | |
| T-11 | Mở Action History sau khi bật/tắt vài lần | Mỗi thao tác có đúng một bản ghi trạng thái `SUCCESS` | | |
| T-11b | Xem cột "Người thao tác" của các bản ghi vừa tạo | Hiển thị đúng tên người đã gửi lệnh; bản ghi tạo bằng công cụ dòng lệnh hiển thị `—` | | |
| T-12 | Mở trang Profile | 4 liên kết đều mở đúng trang đích | | |
| T-13 | Chạy `mosquitto_sub -t "data_sensors"` | Thấy chuỗi JSON xuất hiện mỗi 2 giây | | |
| T-14 | Chạy `mosquitto_pub -t "device_control"` gửi lệnh ON | LED sáng, `device_respond` trả về `SUCCESS` | | |
| T-15 | Mở 2 tab trình duyệt, bật đèn ở tab 1 | Tab 2 tự cập nhật mà không cần tải lại | | |
| T-16 | Tắt tiến trình worker, mở lại Dashboard | Vẫn tải được dữ liệu lịch sử, hiện "Thiết bị ngoại tuyến" | | |
| T-17 | Mở `/api/schema/swagger-ui/` | Swagger UI liệt kê đủ **8** endpoint, gọi thử được | | |
| T-18 | Thêm một dòng vào danh mục cảm biến rồi khởi động lại tiến trình worker | Dashboard tự hiện thêm một thẻ số liệu mà không phải sửa mã nguồn | | |

**Tỷ lệ đạt:** `<số ca đạt>` / 21 ca.

### 4.3 Kết quả kiểm thử API

Nhóm **25 kịch bản** kiểm thử riêng cho tầng API, thực hiện bằng Postman hoặc `curl`. Từ A-00 đến A-15 chạy được ngay khi chưa lắp mạch — chỉ cần Mosquitto và lệnh `mosquitto_pub` để giả lập thiết bị; ba ca cuối cần Frontend hoặc phần cứng thật.

| # | Kịch bản | Kết quả mong đợi | Kết quả thực tế | Đạt |
|---|---|---|---|---|
| A-00 | `GET /api/sensors/devices` | Mảng thuần 3 phần tử kèm mã, tên, đơn vị | | |
| A-01 | `GET /api/sensors/latest` khi cơ sở dữ liệu rỗng | `200` kèm mảng rỗng | | |
| A-02 | Gửi một message giả bằng `mosquitto_pub` rồi gọi lại A-01 | `200` kèm **3 phần tử**, cả ba cùng một mốc thời gian | | |
| A-02b | Sau A-02, gọi `GET /api/sensors` | Tổng số bản ghi tăng đúng **3**, ba dòng đầu cùng mốc thời gian | | |
| A-02c | Gửi message thiếu trường độ ẩm rồi gọi lại | Tổng số bản ghi chỉ tăng **2**; không có dòng nào cho cảm biến độ ẩm ở mốc đó | | |
| A-03 | `GET /api/sensors/chart` | Mảng tối đa 20 phần tử, **tăng dần** theo thời gian, mỗi phần tử đủ 3 khóa | | |
| A-03b | Sau A-02c, gọi lại `GET /api/sensors/chart` | Phần tử của mốc thiếu số đo có trường độ ẩm rỗng, **không** bị loại khỏi mảng | | |
| A-04 | `GET /api/sensors?page_size=500` | `200`, tự hạ về đúng 100 bản ghi | | |
| A-05 | `GET /api/sensors?page_size=abc` | `400 VALIDATION_ERROR` | | |
| A-06 | `GET /api/sensors?page=99999` | `404 PAGE_NOT_FOUND` | | |
| A-07 | Lọc khoảng thời gian với ngày đầu lớn hơn ngày cuối | `400 INVALID_RANGE` | | |
| A-07b | `?sensor=room01_temp&value__gte=35&value__lte=20` | `400 INVALID_RANGE`, `details` chỉ đúng cặp tham số giá trị | | |
| A-07c | `?sensor=room01_temp&value__gte=30` kèm khoảng thời gian | `200`, mọi bản ghi thỏa **cả hai** điều kiện và đều thuộc cảm biến nhiệt độ | | |
| A-07d | `?value__gte=30` **không kèm** tham số chọn cảm biến | `400 VALIDATION_ERROR`, thông báo yêu cầu chọn cảm biến trước | | |
| A-07e | `?search=độ ẩm` | Chỉ trả về bản ghi của cảm biến độ ẩm | | |
| A-07f | Lấy trang 1 rồi trang 2 với `?ordering=-value&page_size=3` | Không có bản ghi nào xuất hiện ở **cả hai** trang | | |
| A-08 | `GET /api/devices` | Mảng thuần 2 phần tử, **không** bọc trong `count`/`results` | | |
| A-09 | `POST /api/devices/999/control` | `404 NOT_FOUND` | | |
| A-10 | `POST /api/devices/1/control` với `action` sai | `400 VALIDATION_ERROR`, `details.action` có nội dung | | |
| A-11 | `POST /api/devices/1/control` với `{"action":"on"}` | `202` — chuỗi viết thường được tự chuẩn hóa | | |
| A-11b | `POST /api/devices/1/control` kèm `user_id` hợp lệ | `202` kèm thông tin người thao tác; bản ghi lịch sử hiện đúng tên | | |
| A-11c | `POST /api/devices/1/control` **không** kèm `user_id` | `202` với trường người thao tác rỗng; giao diện hiển thị `—` | | |
| A-11d | `POST /api/devices/1/control` với `user_id` không tồn tại | `400 VALIDATION_ERROR` | | |
| A-11e | Lọc lịch sử theo nhóm "không xác định người thao tác" sau A-11c | Trả về đúng bản ghi vừa tạo | | |
| A-12 | Tắt Mosquitto rồi gửi lệnh điều khiển | `503`, lịch sử **không** có bản ghi mới | | |
| A-13 | Gửi 2 lệnh liên tiếp trong 1 giây | Lần đầu `202`, lần sau `409 DEVICE_BUSY`; chỉ sinh **một** bản ghi | | |
| A-14 | Sau A-13, chờ 7 giây rồi gửi lại | `202` — bản ghi cũ đã tự chuyển `FAILED` | | |
| A-15 | `GET /api/actions?status=FAILED` sau A-14 | Có ít nhất 1 bản ghi, `error_message` nói về hết thời gian chờ | | |
| A-16 | Mở 2 tab trình duyệt, bật đèn ở tab 1 | Tab 2 nhận `device.state` và tự đổi công tắc | | |
| A-17 | Rút nguồn thiết bị rồi bấm bật đèn | Sau 5–6 giây nhận sự kiện `FAILED` | | |
| A-18 | Mở `/api/schema/swagger-ui/` | Liệt kê đủ **8** endpoint REST, gọi thử được | | |

**Tỷ lệ đạt:** `<số ca đạt>` / 25 ca.

Bốn kịch bản đáng chú ý nhất vì bắt được lỗi mà thử tay khó phát hiện: **A-02b** và **A-02c** kiểm chứng quy tắc "một gói tin vào phải ra đúng ba bản ghi cùng mốc thời gian, cảm biến lỗi thì thiếu bản ghi chứ không phải có bản ghi rỗng"; **A-03b** kiểm chứng rằng chu kỳ thiếu số đo vẫn nằm trên biểu đồ, vì nếu backend bỏ cả chu kỳ thì trục thời gian bị co lại mà nhìn biểu đồ không nhận ra; **A-07f** kiểm chứng thứ tự sắp xếp có cột phá hòa — lỗi chỉ lộ ra khi lật sang trang thứ hai.

| ⬛ CHÈN HÌNH 4.1 |
|---|
| **Cần chèn:** ảnh chụp màn hình Swagger UI tại `/api/schema/swagger-ui/`, thấy rõ danh sách endpoint. |

*Hình 4.1. Giao diện tài liệu API sinh tự động*

### 4.4 Ảnh chụp màn hình hệ thống

| ⬛ CHÈN HÌNH 4.2 |
|---|
| **Cần chèn:** ảnh chụp mạch phần cứng đã lắp hoàn chỉnh, có LED đang sáng. |

*Hình 4.2. Mạch phần cứng hoàn chỉnh*

| ⬛ CHÈN HÌNH 4.3 |
|---|
| **Cần chèn:** ảnh chụp màn hình Dashboard đang chạy thật, có số liệu và biểu đồ. |

*Hình 4.3. Màn hình Dashboard khi hệ thống hoạt động*

| ⬛ CHÈN HÌNH 4.4 |
|---|
| **Cần chèn:** ảnh chụp màn hình Data Sensor và Action History (ghép 2 ảnh hoặc để 2 hình riêng). |

*Hình 4.4. Màn hình tra cứu lịch sử*

| ⬛ CHÈN HÌNH 4.5 |
|---|
| **Cần chèn:** ảnh chụp terminal chạy 3 tiến trình (Mosquitto, daphne, mqtt_worker) và log khi có lệnh điều khiển đi qua. |

*Hình 4.5. Nhật ký hệ thống khi thực thi lệnh điều khiển*

### 4.5 Đánh giá

**Về mức độ đáp ứng yêu cầu:** `<điền sau — đối chiếu với bảng FR ở §1.4, nêu rõ yêu cầu nào đạt, yêu cầu nào chưa>`

**Về hiệu năng:** `<điền sau — đo độ trễ thực tế và đối chiếu với NFR-01, NFR-02, NFR-03>`

| Chỉ tiêu | Yêu cầu | Đo được | Đánh giá |
|---|---|---|---|
| Độ trễ điều khiển (NFR-01) | ≤ 2 giây | | |
| Độ trễ cập nhật giao diện (NFR-02) | ≤ 1 giây | | |
| Thời gian phản hồi API (NFR-03) | ≤ 500 ms | | |

### 4.6 Kết luận

`<điền sau — tóm tắt những gì đã xây dựng được, khoảng 2 đoạn>`

Gợi ý nội dung cần nêu:

- Hệ thống đã hoàn thành ba lớp: firmware thu thập số liệu, backend xử lý và lưu trữ, giao diện web giám sát và điều khiển.
- Các quyết định thiết kế đáng chú ý và lý do đằng sau: tách backend thành hai tiến trình, dùng `request_id` để ghép cặp lệnh với phản hồi, phát hiện timeout bằng vòng quét trong worker thay vì bộ hẹn giờ.
- Kết quả kiểm thử đạt được so với mục tiêu ban đầu ở §1.2.

### 4.7 Hạn chế và hướng phát triển

**Hạn chế của phiên bản hiện tại**

| # | Hạn chế | Ảnh hưởng |
|---|---|---|
| 1 | Không có đăng nhập và phân quyền | Chỉ chạy được trong mạng nội bộ tin cậy |
| 2 | Chỉ giám sát được một phòng | Muốn thêm phòng phải sửa cấu trúc nhóm WebSocket |
| 3 | Dữ liệu trong lúc thiết bị mất kết nối bị bỏ qua, không có bộ đệm | Biểu đồ có khoảng đứt |
| 4 | Thiết bị chấp hành mô phỏng bằng LED, chưa điều khiển tải điện thật | Chưa dùng được trong thực tế |
| 5 | Cảm biến DHT11 có sai số lớn (±2 °C, ±5 %RH) | Số liệu chỉ mang tính tham khảo |

**Hướng phát triển**

| # | Hướng | Nội dung |
|---|---|---|
| 1 | Mở rộng nhiều phòng | Tách nhóm WebSocket theo phòng, bổ sung bảng quản lý phòng |
| 2 | Bổ sung xác thực | Token cho REST API, HTTPS/WSS, giới hạn tần suất gọi |
| 3 | Cảnh báo vượt ngưỡng | Gửi thông báo khi nhiệt độ hoặc độ ẩm vượt ngưỡng cấu hình |
| 4 | Điều khiển thiết bị điện thật | Thay LED bằng module relay, bổ sung biện pháp an toàn điện |
| 5 | Xử lý dữ liệu dài hạn | Tổng hợp số liệu theo giờ, xóa dữ liệu thô cũ hơn 90 ngày |
| 6 | Nâng cấp cảm biến | Thay DHT11 bằng DHT22 hoặc SHT31 để tăng độ chính xác |

---

# PHỤ LỤC

## A. Danh mục tài liệu thiết kế

Toàn bộ đặc tả cần thiết để hiểu và đánh giá hệ thống đã nằm trong ba chương đầu của báo cáo này. Bảng dưới liệt kê các tài liệu thiết kế **gốc** được lập trong quá trình phát triển — chúng chi tiết hơn ở một số điểm kỹ thuật (mã nguồn mô hình dữ liệu, câu lệnh tạo bảng, ma trận truy vết đầy đủ, mã nguồn PlantUML của các sơ đồ) và được nộp kèm nếu giảng viên yêu cầu:

| Tài liệu | Nội dung | Tương ứng mục nào trong báo cáo |
|---|---|---|
| Đặc tả yêu cầu phần mềm (SRS) | 7 use case, 18 yêu cầu chức năng, 16 yêu cầu phi chức năng, 21 kịch bản nghiệm thu | Chương 1, mục 4.2 |
| Mô hình Use Case | Biểu đồ use case, đặc tả chi tiết 7 use case, 12 quy tắc nghiệp vụ, ma trận truy vết use case ↔ yêu cầu | Mục 3.1, 3.2, 3.3 |
| Biểu đồ tuần tự | 6 biểu đồ kèm bảng mô tả từng thông điệp và ma trận truy vết | Mục 3.4 |
| Thiết kế cơ sở dữ liệu | Sơ đồ thực thể — liên kết 5 bảng, 18 ràng buộc, 7 chỉ mục, mã mô hình dữ liệu, câu lệnh tạo bảng | Mục 2.4 |
| Đặc tả API | 8 endpoint REST, 2 sự kiện WebSocket, 3 topic MQTT, 25 kịch bản kiểm thử | Mục 2.3.2, 3.6, 4.3 |

## B. Hướng dẫn chạy hệ thống

Hệ thống cần **ba tiến trình chạy song song**, mở trên ba cửa sổ dòng lệnh:

```bash
# Cửa sổ 1 — MQTT Broker
mosquitto -c mosquitto.conf -v

# Cửa sổ 2 — API và WebSocket
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Cửa sổ 3 — MQTT worker
python manage.py mqtt_worker
```

Redis chạy nền bằng Docker:

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

Kiểm tra nhanh luồng MQTT mà không cần phần cứng:

```bash
# Lắng nghe số liệu cảm biến
mosquitto_sub -h localhost -p 1883 -t "data_sensors" -u <user> -P <pass>

# Giả lập thiết bị gửi số liệu
mosquitto_pub -h localhost -p 1883 -t "data_sensors" -u <user> -P <pass> \
  -m '{"device_id":"esp8266_room01","temperature":28.5,"humidity":72,"light":350}'
```

## C. Liên kết bàn giao

| Sản phẩm | Đường dẫn |
|---|---|
| Mã nguồn (GitHub) | `<điền link>` |
| Thiết kế giao diện (Figma) | `<điền link>` |
| Tài liệu API (Swagger) | `http://localhost:8000/api/schema/swagger-ui/` |
| Postman Collection | `docs/postman_collection.json` |
| Video demo | `<điền link nếu có>` |

---

# TÀI LIỆU THAM KHẢO

[1] OASIS, *MQTT Version 3.1.1 — OASIS Standard*, 2014.

[2] Aosong Electronics, *DHT11 Humidity & Temperature Sensor — Datasheet*.

[3] Espressif Systems, *ESP8266EX Datasheet*, phiên bản mới nhất.

[4] Django Software Foundation, *Django Documentation*, <https://docs.djangoproject.com/>

[5] Encode, *Django REST Framework Documentation*, <https://www.django-rest-framework.org/>

[6] Django Channels Project, *Channels Documentation*, <https://channels.readthedocs.io/>

[7] Eclipse Foundation, *Eclipse Mosquitto — An open source MQTT broker*, <https://mosquitto.org/>

[8] The PostgreSQL Global Development Group, *PostgreSQL 16 Documentation*, <https://www.postgresql.org/docs/16/>

[9] Nguyễn Quốc Uy, *Bài giảng học phần IoT và Ứng dụng*, Học viện Công nghệ Bưu chính Viễn thông, 2026.
