# CLAUDE.md — Dự án IoT: Hệ thống giám sát & điều khiển phòng

> File này là "bộ nhớ dự án". Mỗi khi mở phiên làm việc mới, đọc file này trước.
> Cập nhật lại file này mỗi khi có quyết định thiết kế mới.

---

## 0. TRẠNG THÁI HIỆN TẠI

**Cập nhật lần cuối: 18/09/2026** — phiên 9.

> 🆕 **Phiên 9:** **Backend Django đã code xong và chạy thật end-to-end** (`backend/`). Kế hoạch từng module + chỗ lệch khỏi mã mẫu trong tài liệu: `backend/PLAN.md`; cách chạy + bản đồ code: `backend/README.md`. Chi tiết và việc còn treo ở **§0.2o**.

> **Phiên 8:** broker MQTT đã chuyển sang **port 1884**; `05-API.md` lên **v2.1 — thêm đăng nhập bằng token**; chuẩn bị code **Frontend** (React + MSW). Chi tiết và việc còn treo ở **§0.2n**.

> ✅ **Mô hình dữ liệu v2.0 đã đồng bộ xong toàn bộ `.md` + bản vẽ + ảnh ERD** (§0.2k). Còn lại: **dựng Word** (người dùng tự làm — §0.2h) và **chụp lại 4 ảnh màn hình** từ file HTML.

### 0.1 Đã xong

| # | Việc | Kết quả |
|---|---|---|
| 1 | Trích xuất yêu cầu từ 12 ảnh chụp bảng + `in4.txt` | Toàn bộ nội dung đã ghi lại ở §1–§3 |
| 2 | **Chốt stack** | Django 5 + DRF + Channels + Redis + PostgreSQL 16 + React (§5) |
| 3 | **SRS v0.4** | `docs/01-SRS.md` — 8 chương, 7 UC, 16 FR, 16 NFR, 17 ca UAT |
| 4 | **Use Case v1.3** | `docs/02-UseCase.md` — sơ đồ PlantUML + Mermaid, 7 UC đặc tả đầy đủ, 10 BR, ma trận truy vết |
| 5 | **Pipeline xuất Word** | `tools/build_body.py` + `tools/assemble.py` (§5.4) |
| 6 | **Bản Word đầu tiên** | `docs/01-SRS.docx` — 22 trang, bìa + mục lục tự động theo mẫu PTIT |
| 7 | **Thiết kế CSDL v1.2** *(phiên 2)* | `docs/04-Database.md` — ERD, 3 bảng, 12 ràng buộc, 7 chỉ mục, `models.py`, DDL, seed, ma trận truy vết |
| 8 | **Sequence Diagram v1.2** *(phiên 3)* | `docs/03-Sequence.md` — 6 sơ đồ SD-01→SD-06 (PlantUML + Mermaid), bảng thông điệp, 2 sự kiện WS, ma trận truy vết SD ↔ UC/BR |
| 9 | **Xuất PNG các sơ đồ** *(phiên 3)* | `docs/img/` — 8 ảnh: `usecase-diagram.png`, `erd.png`, 6 sequence |
| 10 | **API Docs v1.3** *(phiên 4–5)* | `docs/05-API.md` — 13 chương: 7 endpoint REST + 1 kênh WS (2 sự kiện) + 3 topic MQTT, cấu trúc lỗi thống nhất 7 mã, 21 ca kiểm thử API, mã mẫu cho tuần 3 |
| 13 | **Mockup 4 màn hình** *(phiên 5)* | **Hai dạng, dùng cho hai việc khác nhau:**<br>· `docs/wireframe.html` — **bản thuyết minh**: 4 màn hình + 4 trạng thái phụ + bảng màu/kích thước + ghi chú thiết kế. Để đọc và chụp ảnh. Đã xuất bản: <https://claude.ai/code/artifact/182f98e3-6eda-436a-962e-aa2a70084a81><br>· `docs/wireframe/*.html` — **bản để nhập vào Figma**: 4 file rời, **CSS nhúng thẳng trong file, tự đứng độc lập**. Ban đầu tôi tách ra `_base.css` dùng chung → mở lên mất hết style (icon phóng to, layout xếp dọc thành một cột). Đã bỏ, đừng tách lại.<br>⚠️ *(sửa cuối phiên 5)* Khung **không còn ghim cứng 1180×660** mà **co giãn lấp đầy cửa sổ trình duyệt** (rộng 100%, tối đa 1680px, cao 100vh) — bản cũ để thừa viền xám hai bên trên màn hình rộng. Kích thước khung Figma giờ = kích thước cửa sổ lúc chụp/nhập, nên **đặt cửa sổ đúng cỡ muốn có (ví dụ 1440×900) trước khi chụp**. Chi tiết cách co giãn ở §0.2e |
| 12 | **BÁO CÁO TỔNG v0.1** *(phiên 5)* | `docs/BaoCao.md` → `docs/BaoCao-moi.docx` — **48 trang, 76 bảng, 9 sơ đồ đã nhúng**. *(phiên 6)* Chương 3 nay **đặc tả đầy đủ cả 7 use case** theo một khuôn mẫu thống nhất (thuộc tính · luồng chính · luồng thay thế · luồng ngoại lệ · bảng truy vết), thay vì chỉ 2 use case trọng tâm như bản cũ — đây là phần GV chấm kỹ nhất. Đã có **Hình 2.1** kiến trúc tổng thể. Đúng 4 chương theo ảnh 5: C1 Tổng quan · C2 Thiết kế hệ thống · C3 Thiết kế chi tiết · C4 Kết quả thử nghiệm + Kết luận. Kèm Phụ lục A/B/C và Tài liệu tham khảo |
| 14 | **Rà soát chéo bản vẽ ↔ tài liệu** *(cuối phiên 5)* | Đối chiếu từng con số trên 4 màn hình với `01-SRS.md`, `02-UseCase.md`, `05-API.md`, `04-Database.md`. Sửa 11 điểm lệch, chốt **một bộ dữ liệu mẫu duy nhất** dùng chung cho mọi tài liệu (§0.2f). Thêm `docs/wireframe/05-trang-thai.html` gồm 5 trạng thái phụ. Sửa lây sang `01-SRS.md` v0.3, `02-UseCase.md` v1.2, `05-API.md` v1.2, `BaoCao.md` |
| 15 | **Rà soát chéo toàn bộ tài liệu ↔ bản Word** *(phiên 6)* | Đối chiếu `BaoCao.docx`/`01-SRS.docx` với `.md` bằng Pandoc (so từng dòng), rồi soát mâu thuẫn nghiệp vụ giữa 5 tài liệu. **Sửa 7 lỗi nghiệp vụ + 5 lỗi hình thức**, dựng lại cả 2 bản Word. Chi tiết ở §0.2g |
| 16 | **Thiết kế CSDL v2.0** *(phiên 7)* | `docs/04-Database.md` — 3 → **5 bảng** theo yêu cầu GV: tách danh mục cảm biến, số đo lưu từng cảm biến một dòng, thêm bảng người dùng. 18 ràng buộc, 4 lệnh `CREATE INDEX`, models + DDL + seed viết lại. **Mới chỉ sửa đúng file này** — xem §0.2k và §16 của chính tài liệu đó |
| 11 | **Bổ sung lọc theo khoảng giá trị số đo** *(cuối phiên 4)* | Sửa đồng bộ 4 file: `02-UseCase.md` v1.1 (UC-04) · `03-Sequence.md` v1.1 (ghi chú SD-06) · `04-Database.md` v1.1 (§5.2) · `05-API.md` v1.1 (§4.3, §7.3). **Sơ đồ UC, 6 sequence và schema CSDL không đổi — không phải xuất lại ảnh, không phát sinh migration** |

### 0.2k ⚠️ PHIÊN 7 — GV yêu cầu đổi mô hình dữ liệu (ĐANG LÀM DỞ)

**Bối cảnh:** báo cáo xong ngày 20/08, GV yêu cầu ba việc:
1. Phần Data Sensor **không lưu trạng thái của cả một bộ công cụ** mà lưu **từng cảm biến** — mỗi dòng gồm ID cảm biến, tên, giá trị, thời gian.
2. Thêm bảng lưu **thông tin các cảm biến**.
3. Thêm bảng **người dùng** để biết ai đã thao tác vào thiết bị.

**Đã làm xong (phiên 7):** `04-Database.md` **v2.0** · `01-SRS.md` **v0.5** · `02-UseCase.md` **v2.0** · `05-API.md` **v2.0** · `03-Sequence.md` **v2.0** · bộ dữ liệu mẫu §0.2f · 5 file bản vẽ HTML · `docs/img/erd.png` · `BaoCao.md`.
**Còn lại:** dựng Word (người dùng tự làm) và chụp lại 4 ảnh màn hình Figma.

| Quyết định | Lý do |
|---|---|
| `sensor_data` tách đôi: `sensors_sensordevice` (danh mục) + `sensors_sensordata` (số đo, 4 cột `id · sensor_id · value · recorded_at`) | Đúng yêu cầu GV. Được thêm: **cột `NULL` biến mất** (không đo được ⇒ không có dòng), kéo theo **bẫy lọc `NULL` ở §0.2d cũng biến mất**; bộ lọc 6 tham số còn 2; thêm cảm biến không cần `ALTER TABLE` |
| **Giữ nguyên payload MQTT** — ESP vẫn gửi 1 message 3 trường, worker tách thành 3 dòng | Cho ESP publish 3 message riêng thì nhân ba lưu lượng WiFi **và** 3 dòng lệch `recorded_at` → không xoay bảng vẽ biểu đồ được |
| ⚠️ `recorded_at` **cấm dùng `auto_now_add`**, phải `default=timezone.now` và worker tính mốc **một lần** rồi truyền cho cả 3 dòng | `auto_now_add` gọi `timezone.now()` riêng cho từng đối tượng kể cả trong `bulk_create` → 3 dòng lệch vài micro-giây → biểu đồ mỗi mốc chỉ có 1 đường. Ràng buộc `UNIQUE` **không** bắt được lỗi này; kiểm bằng truy vấn ở `04-Database.md` §11.2 |
| ⚠️ `Meta.ordering = ["-recorded_at", "-id"]`, chỉ mục cũng gồm cả `id` | 3 dòng cùng chu kỳ có `recorded_at` **giống hệt nhau**; chỉ `ORDER BY recorded_at` thì thứ tự không xác định → lật trang bị lặp dòng/mất dòng. Bản 1.2 không gặp vì mỗi chu kỳ 1 dòng |
| `UNIQUE (sensor_id, recorded_at)` thay cho chỉ mục ghép thường | Cùng một cấu trúc B-tree, thêm ý nghĩa nghiệp vụ, không thêm chi phí ghi. Khóa ngoại `sensor` khai `db_index=False` để không tạo chỉ mục trùng trên bảng ghi 129.600 dòng/ngày |
| Ngưỡng BR-02 chuyển vào cột `min_value`/`max_value` của bảng danh mục | Là dữ liệu cấu hình, không phải logic; hiệu chuẩn quang trở ở tuần 2 sửa một dòng là xong. **Cái giá:** `CHECK` không tham chiếu chéo bảng được ⇒ tầng CSDL chỉ còn lưới an toàn thô `value BETWEEN -1000 AND 100000`. **Phải sửa câu "ràng buộc hai tầng ngang nhau" trong báo cáo cho trung thực** |
| Bảng người dùng kế thừa **`AbstractUser`**, **chưa** làm màn hình đăng nhập | Có sẵn băm mật khẩu + admin. Quan trọng nhất: `AUTH_USER_MODEL` gần như **không đổi được sau lần `migrate` đầu tiên** — khai ngay từ đầu là cách duy nhất để tuần sau thêm đăng nhập mà không phải `DROP DATABASE` |
| `action_history.user_id` cho phép **`NULL`**, `on_delete=PROTECT` | Có lệnh không do người nào bấm (seed, `mosquitto_pub` tuần 2, script test). Ép `NOT NULL` phải bịa "người dùng hệ thống" giả. Giao diện hiển thị `—`, **không** ghi "Hệ thống"/"Ẩn danh" — hai chữ đó gợi ý có tài khoản tên như vậy |
| Ánh sáng đổi từ `integer` sang `double precision` | Bảng chỉ có một cột `value` chung cho cả ba đại lượng, phải chọn kiểu bao trùm. API làm tròn khi `metric_type = LIGHT` |
| `UNIQUE (node_id, metric_type)` ở bảng danh mục | Nhờ nó worker ánh xạ được trường `temperature` trong payload sang đúng một dòng mà firmware không phải gửi kèm mã cảm biến |
| **`devices_device` thêm cột `node_id`**, đổi `UNIQUE (gpio_pin)` → **`UNIQUE (node_id, gpio_pin)`** | Ràng buộc cũ **chặn oan** ngay khi lắp bo mạch thứ hai: chân `D5` của bo phòng 1 và `D5` của bo phòng 2 là hai chân vật lý khác nhau, dùng cả hai là hợp lệ. Nguyên tắc chung: **một tài nguyên vật lý chỉ duy nhất trong phạm vi bo mạch sở hữu nó**, không phải toàn hệ thống — đối xứng với `UNIQUE (node_id, metric_type)` của bảng cảm biến |
| **Đổi quy ước đặt mã nghiệp vụ** sang `<vị trí>_<vai trò>` | Xem bảng đối chiếu ngay bên dưới. Mã phẳng `led1, led2, led3` không cho biết thiết bị ở phòng nào; `led2` lại đang mang tên "Quạt trần" (chắc chắn bị hỏi khi vấn đáp); và `light_01` (cảm biến ánh sáng) trùng nghĩa với "đèn". Làm ở phiên này thì chỉ là tìm–thay trong tài liệu, để tới tuần 3 thì phải sửa đồng thời cả firmware |
| **Giữ 3 topic MQTT dùng chung** cho mọi bo, không tách theo bo | Chạy **đúng** nhờ `code` duy nhất toàn cục — bo không có thiết bị mang mã đó thì bỏ qua, chỉ hơi tốn sóng. Tách topic (`device_control/room01`, subscribe `data_sensors/+`) phải sửa SRS §4.3, API §6 và firmware, trong khi đồ án chốt phạm vi một phòng. Cột `node_id` ở cả hai bảng danh mục đã sẵn sàng cho việc đó — ghi vào "hướng phát triển" |
| `Meta.ordering` là `["-recorded_at", "sensor_id"]`, **không** phải `["-recorded_at", "-id"]` | Cả hai đều cho thứ tự xác định duy nhất, nhưng `sensor_id` tăng dần cho ra thứ tự **đọc được** trên bảng Data Sensor: mỗi chu kỳ hiện *Nhiệt độ → Độ ẩm → Ánh sáng* đúng thứ tự danh mục. Dùng `-id` thì ra thứ tự ngược |

**⚠️ BẢNG ĐỔI TÊN MÃ — mọi tài liệu, bản vẽ và firmware phải theo đúng bảng này:**

| Loại | Tên cũ | **Tên mới** |
|---|---|---|
| Cảm biến nhiệt độ | `temp_01` | `room01_temp` |
| Cảm biến độ ẩm | `humi_01` | `room01_humi` |
| Cảm biến ánh sáng | `light_01` | **`room01_lux`** *(không phải `room01_light`)* |
| Đèn phòng | `led1` | `room01_lamp` |
| Quạt trần | `led2` | `room01_fan` |
| Node | `esp8266_room01` | *(giữ nguyên)* |

Phòng thứ hai sau này: `room02_temp`, `room02_lamp`… và **được phép dùng lại chân `D5`/`D6`** nhờ ràng buộc mới.

> ⚠️ **Phải đổi tên xong TRƯỚC khi viết dòng firmware đầu tiên ở tuần 2.** Sau đó thì mỗi lần đổi mã là phải sửa đồng thời chuỗi so sánh trong firmware, seed CSDL và mọi ví dụ payload — nạp firmware mà quên sửa CSDL thì lệnh điều khiển **im lặng không có tác dụng**, không có thông báo lỗi nào.

**Ba mã mới phải bổ sung ngược lên SRS/UseCase, nếu không sẽ "mồ côi"** (đúng bài học §0.2g): **FR-17** danh mục cảm biến · **FR-18** ghi nhận người thao tác · **BR-11** mỗi số đo một bản ghi, cùng chu kỳ cùng mốc thời gian.

> ⚠️ **BÀI HỌC PHIÊN 7 — mỗi sơ đồ tồn tại ở HAI dạng, sửa một dạng là sinh mâu thuẫn.** `03-Sequence.md` viết mỗi sơ đồ bằng **cả PlantUML lẫn Mermaid**, và cùng một thao tác (`INSERT action_history`) xuất hiện ở **6 chỗ** trải trên SD-01, SD-02, SD-05 và khối `alt` §2.4. Bản 2.0 tôi chỉ thêm `user_id` vào đúng một chỗ (M-05 bản PlantUML của SD-01) nên ba sơ đồ mô tả cùng một thao tác lại nói ba kiểu — người dùng phát hiện khi xuất lại ảnh SD-02. Đã vá ở bản **2.0.1**.
>
> ⇒ **Cách phòng:** sửa nhãn trong sơ đồ xong thì `grep` chính chuỗi vừa sửa trên toàn file, đối chiếu số lần xuất hiện. Đừng tin là đã sửa hết chỉ vì đã sửa bản PlantUML.

**Hai thay đổi hành vi phải sửa ở tài liệu khác, dễ quên:**
- **UC-07 E3 đổi nghĩa**: trước là "số đo ngoài ngưỡng ⇒ loại **cả bản ghi**", nay là loại **đúng số đo hỏng**, hai số đo còn lại vẫn lưu.
- **`GET /api/sensors/latest` trả mảng** thay vì một object ⇒ quy tắc `204 No Content` khi bảng rỗng phải viết lại.

**Bộ dữ liệu mẫu chuẩn §0.2f phải tính lại:** 20 mốc × 3 cảm biến = 60 dòng; tổng `12.045` bản ghi cũ ⇒ **36.134** số đo mới (12.045 × 3 trừ 1 số đo độ ẩm thiếu ở mốc `17:29:54`). Phần **lịch sử thao tác giữ nguyên**, chỉ thêm cột người thao tác.

### 0.2n PHIÊN 8 (14/09/2026) — đổi port MQTT, thêm đăng nhập, chuẩn bị code Frontend

**A. Đổi port MQTT 1883 → 1884**

| Việc | Trạng thái |
|---|---|
| `C:\Program Files\mosquitto\mosquitto.conf`, dòng cuối `listener 1884 0.0.0.0`, rồi khởi động lại | ✅ Đã kiểm: `netstat` thấy 1884; có mật khẩu gửi được, không mật khẩu bị `not authorised` |
| Luật tường lửa `Mosquitto MQTT 1884` (Private) | ✅ Đã tạo. Luật cũ `Mosquitto MQTT 1883` vẫn còn, chưa xoá |
| Firmware `MQTT_PORT = 1884` | ✅ Đã sửa trong `.ino`, **chưa nạp lại mạch** |
| Lệnh `-p 1884` trong `docs/BTH2-huongdan-terminal-demo.md` (thêm Phần 3 đổi port, Phần 4 đổi tài khoản) và `docs/BTH2.md` | ✅ |
| `docs/BTH2.md` dòng 91–93 — bảng kết quả đã chạy thật ngày 02/09 | **Cố ý giữ 1883**, vì hôm đó chạy ở 1883 |
| `docs/BTH2.docx` còn 1 lệnh `-p 1883` | ⬜ Người dùng tự sửa trong Word |
| Tài liệu thiết kế còn ghi 1883: `01-SRS.md` (5 chỗ), `05-API.md` §6.1, `03-Sequence.md`, `BaoCao.md` (3 chỗ), `img/architecture.svg`, chính file này (§2.2, §2.3, §5) | ⬜ **Chưa hỏi người dùng có muốn đổi hay không** |

- ⚠️ **Mạng WiFi:** firmware vào hotspot `Luu Duc Anh` với `MQTT_HOST = "172.20.10.5"`. Ngày 14/09 laptop lại ở `PTIT_WIFI 6` (IP `172.11.210.192`, loại **Public**) ⇒ mạch không thể thấy broker dù port đã đúng. Laptop phải vào đúng hotspot đó và kiểm IP của card `Wi-Fi`. Mạng Public vẫn thông cổng nhờ 2 luật tường lửa tên `mosquitto` (theo chương trình, mọi cổng) — **đừng xoá hai luật đó**.
- Người dùng **đã từ chối** lượt thêm mục kiểm tra `MQTT_HOST`/IP vào Bước 4 của file hướng dẫn (từ chối rồi chuyển ngay sang chủ đề Frontend). Chưa rõ là không muốn nội dung đó hay chỉ muốn đổi việc ⇒ **hỏi lại trước khi thêm**.
- Bài học: broker chỉ đọc `mosquitto.conf` **lúc khởi động** ⇒ thứ tự bắt buộc là sửa → lưu → `Restart-Service mosquitto`. Sửa tay bằng Notepad mở từ cửa sổ Admin là đủ, không bắt buộc tạo `.bak`.

**B. Thêm đăng nhập — `05-API.md` v2.1** *(thay thế dòng "chưa làm màn hình đăng nhập" ở §0.2k)*

| Quyết định người dùng chốt | Chi tiết |
|---|---|
| Đăng nhập bảo vệ **toàn bộ 4 màn hình** | Chưa đăng nhập thì chỉ thấy trang Login |
| **Token thật của DRF** (`rest_framework.authtoken`) | `POST /api/auth/login` · `POST /api/auth/logout`; header `Authorization: Token <key>`; 8 → **10 endpoint** |
| **Bỏ `user_id` khỏi thân `POST .../control`** | Lấy `request.user`; `user_id` gửi kèm bị bỏ qua. Cột `action_history.user_id` **vẫn cho `NULL`** (bản ghi không đi qua API) |
| Frontend dùng **MSW** giả lập backend | Có backend thật thì tắt MSW, không sửa chỗ gọi API |
| Thứ tự: **sửa `05-API.md` trước → code Frontend → đồng bộ các tài liệu còn lại sau** | Bước 1 đã xong ở phiên 8 |

Các chi tiết tôi tự chốt trong `05-API.md` v2.1 (lý do đầy đủ ở §2.2, §2.7, §5.1, §11.2 của file đó):
- Sai mật khẩu → **`400 INVALID_CREDENTIALS`**; `401 UNAUTHENTICATED` chỉ mang nghĩa "chưa đăng nhập hoặc phiên đã hết" ⇒ Frontend chỉ cần một bộ chặn `401` chung. Tổng 7 → **9 mã lỗi**.
- WebSocket nhận **`?token=`**; sai thì `accept()` rồi `close(code=4401)`. Đóng trước `accept()` thì trình duyệt chỉ thấy `1006` và Frontend thử kết nối lại mãi.
- ⚠️ `DEFAULT_AUTHENTICATION_CLASSES` **chỉ có `TokenAuthentication`** — có `SessionAuthentication` đứng đầu thì thiếu token ra `403` thay vì `401`.
- View đăng nhập đặt `authentication_classes = []` (token cũ đã thu hồi không chặn việc đăng nhập lại); trường `password` dùng `trim_whitespace=False`.
- Không có `GET /api/auth/me`. Mỗi người dùng một token, không hết hạn ⇒ đăng xuất ở một nơi là mất đăng nhập ở mọi nơi.
- Swagger vẫn mở được khi chưa đăng nhập; nút Authorize phải gõ cả chữ `Token `.
- §10: bản 2.0 ghi "25 ca" nhưng bảng thật có 31 dòng ⇒ nay **36 ca** (thêm A-19 → A-23). ⚠️ `BaoCao.md` và bản Word vẫn ghi 25.
- §4.7 đã đổi `ThS.` → `TS.` (hết việc treo ở §0.3).

**Mã mới đang "mồ côi" — phải bổ sung ngược lên tài liệu trước (bài học §0.2g):** **UC-08** Đăng nhập/Đăng xuất · **FR-19** · **BR-13** mọi thao tác yêu cầu đăng nhập · hai mã lỗi `INVALID_CREDENTIALS`, `UNAUTHENTICATED`. Việc phải làm **sau khi code xong Frontend**: `01-SRS.md` (§8.2 còn ghi "không đăng nhập") · `02-UseCase.md` kèm **xuất lại `usecase-diagram.png`** · `04-Database.md` nhắc bảng `authtoken_token` · wireframe màn Login · `BaoCao.md` và bản Word (người dùng tự sửa Word).

**C. Frontend — đã dựng khung chạy được với dữ liệu giả (14/09/2026).** Code ở `frontend/`, cách chạy + tài khoản + công tắc giả lập lỗi ở `frontend/README.md`. `backend/` vẫn trống.

| Quyết định | Lý do |
|---|---|
| React 19 + Vite 8 + React Router 7 + Recharts 3 + Axios, viết bằng **JavaScript** | Stack §5 và quy ước `camelCase` cho JS ở §6 |
| **CSS Modules**; bảng màu, kích thước chép nguyên từ `docs/wireframe/*.html` vào `src/styles/` | Giao diện khớp bản vẽ; màn Login chưa có bản vẽ nên tự dựng theo cùng bảng màu |
| **Không dùng thư viện state** — `AuthContext` (token) + `RealtimeContext` (một kết nối WebSocket cho cả app) | Chỉ hai thứ dùng chung toàn app; dữ liệu bảng mỗi trang tự gọi API |
| **MSW** giả lập đủ 10 endpoint + WebSocket, bật bằng `VITE_USE_MOCK=true` ở `.env.development` | Có Django thì đổi `false`, không sửa dòng code gọi API nào |
| Dữ liệu mock **tính ngược từ toạ độ polyline** của `01-dashboard.html` | Khớp §0.2f — đã kiểm **23/23** con số bằng script Node (36.134 bản ghi, lọc ra 1.284, biến thiên −0.1/−14.4/+262, chuỗi 79→88…) |
| Lệnh điều khiển mới trong mock dùng **đồng hồ riêng bắt đầu 17:31:45** | Lệnh id 88 của bộ mẫu lúc 17:31:44 **muộn hơn** mốc Dashboard 17:30:02; dùng chung đồng hồ thì lệnh vừa bấm bị xếp dưới lệnh 88 |
| Bộ lọc "Người thao tác" chỉ có *Tất cả / Của tôi / Không rõ* | ⚠️ API **không có** endpoint danh sách người dùng. Muốn dropdown chọn từng người thì phải thêm `GET /api/users` vào `05-API.md` trước |

**Kiểm chứng:** `npm run build` qua; script điều khiển Chrome headless qua DevTools Protocol (`scratchpad/ui-check.mjs`, không nằm trong repo) đạt **22/22** — chặn trang khi chưa đăng nhập, sai mật khẩu, quay về đúng trang, thẻ số, biểu đồ đứt nét, WebSocket, bấm công tắc `ĐANG GỬI…` → ON, lọc 1.288 bản ghi, khoảng giá trị ngược, lịch sử + lọc `none`, profile, đăng xuất.

**Lưu ý khi demo bằng mock:** 5–6 giây đầu sau khi tải trang, bấm **đèn** nhận `409 DEVICE_BUSY` vì lệnh id 88 còn `PENDING` — đúng BR-04, không phải lỗi.

**Chưa làm:** tách gói JS (~700 kB, chủ yếu Recharts — Vite cảnh báo nhưng không lỗi) · lựa chọn `page_size` lớn hơn cho Data Sensor (`05-API.md` §12 điểm 2c) · bản vẽ màn Login.

### 0.2o PHIÊN 9 (18/09/2026) — code Backend

**Kết quả:** `backend/` — Django 5.2.17 + DRF 3.18 + Channels 4.3 + paho-mqtt 2.1 trên Python 3.14, venv ở `backend/.venv`. 6 app `core · users · sensors · devices · realtime · mqtt`, mỗi app cùng bộ file `models · serializers · filters · services · views · admin` — **logic nghiệp vụ nằm ở `services.py`**, dùng chung cho API view và MQTT worker.

| Kiểm chứng | Kết quả |
|---|---|
| `python manage.py test` (không cần broker/Redis) | **52/52** — tên test mang mã ca `A-xx` của `05-API.md` §10 |
| End-to-end thật: daphne + `mqtt_worker` + `fake_esp` + Mosquitto 1884 + Redis (script Node trong scratchpad, không nằm trong repo) | **15/15** chế độ thường, **16/16** chế độ `--no-respond` (FAILED sau 5,6 s; 409 khi còn PENDING) |
| `POST .../control` | 70–100 ms (NFR-01 ≤ 200 ms) |
| `spectacular --validate --fail-on-warn` | 0 cảnh báo, đủ 10 endpoint chính |
| Sai mật khẩu MQTT / sai cổng | `503` sau 27 ms / 2 s |

**Hạ tầng trên máy (khác §0.4 cũ):** PostgreSQL **18** đã cài, service `postgresql-x64-18`, DB `iot_room`, tài khoản `postgres` (mật khẩu trong `backend/.env`, không commit). Redis dùng container **`redis-dev`** có sẵn (tự bật cùng Docker Desktop), **database số 5** để không đụng dự án khác. MQTT: `iotuser` / cổng 1884.

**Hai lỗi thật bắt được khi chạy end-to-end — đã sửa trong code, ⚠️ CHƯA sửa tài liệu:**
1. **`publish()` bên trong `transaction.atomic()` (mã mẫu `05-API.md` §7.4, SD-01 §2.4) là sai.** ESP giả lập trả lời sau ~20 ms, sớm hơn lúc commit → worker không thấy bản ghi PENDING, bỏ qua phản hồi, 5 giây sau đánh FAILED trong khi đèn đã bật. Code nay **commit PENDING trước rồi mới publish; broker lỗi thì xoá bản ghi** → hành vi với người dùng vẫn đúng UC-02 E2 (503, không để lại lịch sử). Phải sửa lại `05-API.md` §4.5 (đoạn "Vì sao 503 không để lại bản ghi"), §7.4, và `03-Sequence.md` SD-01 §2.4 + bảng thông điệp. Câu trả lời vấn đáp "vì sao dãy id có lỗ hổng" vẫn đúng.
2. **`MQTT_HOST=localhost` làm mỗi lần publish chậm ~2 giây** (Windows thử IPv6 `::1` trước, Mosquitto chỉ nghe IPv4) → vỡ NFR-01. Dùng `127.0.0.1`. Firmware không bị ảnh hưởng (dùng IP LAN).

**Lệch có chủ đích khác so với mã mẫu** (bảng đầy đủ ở `backend/PLAN.md` §4): cột phá hoà của `/api/sensors` là `sensor_id` **rồi `id`** (chỉ `sensor_id` thì `?ordering=-value` vẫn hoà) · lỗi 500 cũng trả JSON `INTERNAL_ERROR` · `INVALID_RANGE` nhận diện bằng mã lỗi gắn vào `ValidationError` chứ không so chuỗi · publisher chờ CONNACK trước khi publish · `send_command` khoá dòng thiết bị (`select_for_update`) để 2 tab đồng thời không cùng ghi PENDING.

**Lưu ý vận hành:**
- `fake_esp` giả lập ESP8266 — **không chạy cùng mạch thật** (hai "thiết bị" cùng trả lời một lệnh).
- Sửa ngưỡng / thêm cảm biến trong `/admin/` → phải khởi động lại `mqtt_worker` (danh mục nạp một lần).
**Đã nối frontend với backend thật (cuối phiên 9).** `frontend/.env.development` → `VITE_USE_MOCK=false`; `frontend/.env` đổi `localhost` → **`127.0.0.1`** cho cả API lẫn WebSocket (trình duyệt thử IPv6 `::1` trước, daphne chỉ nghe IPv4 → mỗi kết nối mới chậm ~220 ms; thử cho daphne nghe cả `::` thì Django lại từ chối host `[::1]` — bỏ). Trang vẫn mở ở `localhost:5173` nên CORS / Origin của WebSocket không đổi. Chrome headless + CDP (`scratchpad/ui-real.mjs`, không nằm trong repo) đạt **22/24** — 2 ca trượt là lỗi kịch bản, không phải lỗi hệ thống (chu kỳ thiếu độ ẩm đúng UC-07 A2; logout đã thu hồi token trên server nhưng script đọc log mạng quá sớm). Không có lỗi JavaScript nào; GET đầu trang ~390 ms (4 request song song xếp hàng trên luồng đồng bộ của daphne), các lần sau ~90 ms; bấm công tắc → mở khoá sau ~230 ms.
- ⚠️ **Đăng nhập mất ~1,5 giây** — do Django 5.2 băm PBKDF2 1.000.000 vòng, sai mật khẩu cũng tốn đúng chừng đó (chống dò thời gian). Có chủ đích, **đừng hạ số vòng**; nếu bị hỏi khi demo thì giải thích như vậy.
- Muốn quay lại dữ liệu giả MSW: đặt `VITE_USE_MOCK=true` rồi khởi động lại `npm run dev`.
- ⚠️ Dừng tiến trình nền trên Windows: dừng lớp shell `npm` **không** dừng tiến trình `node` con → cổng 5173 vẫn bị chiếm. Kiểm bằng `netstat -ano | findstr :5173`.

**✅ Đã chạy với MẠCH THẬT (18/09/2026, cuối phiên 9)** — firmware đã nạp lại với cổng 1884, người dùng tự cắm. Kiểm ở backend: 110 chu kỳ đầu **đủ 3 số đo cả 110**; 16 lệnh bật/tắt đèn + quạt **đều SUCCESS**, độ trễ khứ hồi **89–273 ms** (ESP giả lập ~20 ms — chênh do WiFi thật); ánh sáng dao động 39–1024 (module LM393 vẫn chỉ có `DO`).
- ⚠️ **Chu kỳ đầu tiên sau khi cấp điện DHT11 trả số rác** — `0.9 °C` và `0 %` — không phải `NaN` nên firmware không lọc, và vẫn nằm trong ngưỡng BR-02 nên backend cũng nhận. Từ chu kỳ 2 trở đi đúng (30 °C / 78 %). **Chưa sửa.** Hướng sửa đề xuất: ở firmware bỏ lần đọc đầu (đọc nháp một lần trong `setup()` sau `dht.begin()` rồi `delay(2000)`), vì chỉ firmware biết "vừa khởi động". Không nên nâng ngưỡng dưới của độ ẩm để chặn, vì đó là thay đổi BR-02 phải sửa lại tài liệu.
- Laptop lúc chạy thử ở WiFi `Tenda_75D990_5G` (IP `192.168.67.103`) — khác cấu hình hotspot cũ trong firmware; kiểm lại `MQTT_HOST` mỗi lần đổi mạng.

**Chốt điểm treo `04-Database.md` §14 điểm 4 — trạng thái sau khi mạch mất điện** *(người dùng phát hiện khi rút mạch lúc đèn đang ON: cắm lại đèn tắt nhưng giao diện vẫn ON)*. Người dùng chọn **"giao diện theo mạch"** (không chọn "mạch tự khôi phục trạng thái cũ" — cách đó lật ngược quyết định "không tự bật đèn" ở `05-API.md` §6.1).
- **Firmware** `publishStateReport()`: mỗi lần (kết nối lại) broker gửi lên **`device_respond`** mỗi thiết bị một gói `{"device","state","status":"REPORT"}`, **không có `request_id`**. Dùng lại topic cũ để giữ đúng 3 topic GV chốt. ⚠️ **Đã sửa file `.ino`, CHƯA nạp lại mạch.**
- **Backend** `devices.services.sync_reported_state()` + nhánh `REPORT` trong `mqtt/handlers.py`: cập nhật `current_state`, phát `device.state` với **`request_id: null`**, status `SUCCESS`; **không ghi Action History**. Trạng thái không đổi thì im lặng. `current_state` nay đổi ở **hai** chỗ, cả hai đều do phần cứng xác nhận.
- **Frontend không sửa**: sự kiện `device.state` nào cũng cập nhật công tắc; chỉ việc mở khoá mới cần khớp `request_id`.
- `fake_esp` cũng gửi REPORT khi kết nối → tắt/bật lại nó là diễn lại được cảnh rút điện. 55/55 test; chạy thật trên broker đạt.
- ⚠️ **Tài liệu chưa sửa:** `05-API.md` §6.4 (thêm dạng gói REPORT), §5.3 (`request_id` có thể `null`), §6.5; `04-Database.md` §6.2 (quy tắc cập nhật `current_state` thêm dòng "thiết bị tự báo") và §14 điểm 4 (đánh dấu đã chốt); `03-Sequence.md` có thể thêm một sơ đồ nhỏ.
- Còn hở: trong lúc mạch đang rút, công tắc vẫn hiện trạng thái cũ cho tới khi mạch cắm lại; chỉ có nhãn "Thiết bị ngoại tuyến" sau 30 giây (BR-07). Muốn báo ngay lúc mất kết nối thì dùng Last Will của MQTT — chưa làm.

**⚠️ Lỗi thứ 3 bắt được khi chạy mạch thật — WebSocket sập mỗi ~11 giây khi mạch ngoại tuyến** *(người dùng tưởng là "tự kết nối lại mỗi 5 giây vì thiết bị ngoại tuyến")*. Nguyên nhân: **redis-py 8 mặc định `socket_timeout = 5` giây, trùng đúng `brpop_timeout = 5` của channels_redis.** Mạch chạy thì 2 giây có một `sensor.data` nên không bao giờ chờ đủ 5 giây; mạch rút ra thì lệnh chờ tin nhắn của consumer ném `redis.exceptions.TimeoutError` → WebSocket sập (không kịp `group_discard`, thành viên "ma" dồn tới 73 trong Redis) → frontend nối lại sau 5 giây → chu kỳ 6 + 5 ≈ 11 giây. Mọi kiểm thử trước đều lọt vì luôn có dữ liệu đổ về. **Sửa:** `CHANNEL_LAYERS` khai host dạng dict với `"socket_timeout": 15`; ghim `redis==8.1.0` trong `requirements.txt`; test `RedisTimeoutConfigTests` chặn tái phát (56/56). Kiểm lại: giữ WebSocket 25 giây không có sự kiện → không sập; kết nối của trình duyệt sống liên tục.
- Cách soi tình trạng kết nối: `docker exec redis-dev redis-cli -n 5 zrange asgi:group:realtime 0 -1 withscores` — mỗi dòng là một tab đang mở, điểm số là thời điểm tham gia.

**Firmware — bỏ lần đọc DHT11 đầu tiên (đã sửa `.ino`, CHƯA nạp):** trong `setup()` sau `dht.begin()`: `delay(2000)` → `dht.read()` đọc nháp rồi bỏ → `lastSend = millis()`. Dòng cuối bắt buộc: thư viện Adafruit DHT **trả lại kết quả cũ trong bộ đệm nếu hai lần đọc cách nhau < 2 giây** (`MIN_INTERVAL 2000`, `DHT.cpp` dòng 239); WiFi nối nhanh thì lần đọc thật sẽ trả đúng số rác vừa bỏ.

**Tài liệu đọc code frontend:** `frontend/HUONG-DAN-DOC-CODE.md` — thứ tự nên đọc, sơ đồ khởi động, từng file làm gì, component nào dùng ở đâu, 3 luồng chính, bảng "muốn sửa X mở file nào". `frontend/README.md` đã trỏ tới nó và sửa câu cũ "Backend Django chưa dựng".

**Việc tiếp theo:** ① nạp lại firmware (có `publishStateReport` + bỏ lần đọc DHT11 đầu) rồi thử rút/cắm khi đèn ON · ② sửa tài liệu theo lỗi 1 và mục REPORT ở trên · ③ các việc đồng bộ UC-08/FR-19/BR-13 còn treo từ §0.2n.

### 0.2p PHIÊN 10 (24/09/2026) — Frontend: gộp 2 ô ngày thành MỘT ô "Thời điểm"

**Người dùng chốt:** bỏ cặp *Từ ngày / Đến ngày*, thay bằng **một ô duy nhất**, nhập **gần đúng**, gõ tay hoặc bấm nút lịch. Áp cho cả `DataSensorPage` và `ActionHistoryPage`.

| Quyết định | Chi tiết |
|---|---|
| **Gõ tới đâu lọc trọn đơn vị tới đó** | `17/08/2026` → cả ngày · `… 17` → trọn giờ · `… 17:29` → trọn phút · `… 17:29:24` → đúng giây (ra 3 dòng của một chu kỳ). Hàm `parseApproxVN()` ở `frontend/src/utils/format.js` sinh cặp `__gte`/`__lte` — **API và backend không phải sửa gì** |
| Dấu ngăn cách nào cũng nhận | `29/10/2026-17/29/24`, `29.10.2026 17.29`, `2026-10-29T17:29:24` đều hợp lệ. Nhận cả thứ tự năm-trước vì ô lịch trả về dạng đó |
| **Ô chữ + nút lịch**, không dùng thẳng `datetime-local` làm ô hiển thị | `datetime-local` bắt điền đủ mọi ô mới cho ra giá trị ⇒ không nhập gần đúng được. Nút lịch mở ô `datetime-local` ẩn bằng `showPicker()`; ô ẩn **phải được render** (chỉ `opacity:0`), để `display:none` là Chrome ném `InvalidStateError`. Component `DateTimeInput` trong `components/Filters.jsx` |
| Có dòng ghi chú "Đang lọc thời gian: …" dưới bộ lọc | Nói rõ khoảng thật sự đang áp, khỏi đoán khi gõ thiếu đuôi |
| Gõ sai định dạng → báo lỗi ngay, **không gọi API** | Cùng cách chặn cục bộ như UC-04 E2 |

> ⚠️ **Lỗi thật bắt được khi chạy thử — cận trên phải bọc hết phần lẻ của giây.** `recorded_at` lưu tới micro-giây (mock: `17:29:54.451`; backend thật: `timezone.now()`), nên `...__lte=17:29:54+07:00` **loại sạch chính giây đó** → lọc "đúng giây" ra bảng rỗng. Đã sửa: cận trên là `…59.999999` / `…24.999999`. Bài học áp cho mọi chỗ so sánh mốc thời gian khác.

**Bốn việc sửa tiếp trong cùng phiên** (người dùng thử thật rồi báo):

| Việc | Chi tiết |
|---|---|
| ⚠️ **Cột "Thời gian" đảo thành ngày-trước-giờ-sau** (`17/08/2026 · 17:30:04`) | Đây chính là nguyên nhân "lọc theo giây bị lỗi": cột hiển thị **giờ trước** nên chép y nguyên vào ô lọc thì ô báo sai định dạng, bảng giữ kết quả cũ ⇒ tưởng lọc hỏng. Sửa `fmtDateTime()`. **Nguyên tắc: thứ tự hiển thị phải trùng thứ tự ô nhập, vì người dùng luôn chép từ bảng sang ô lọc** |
| `parseApproxVN` nhận thêm **thứ tự giờ-trước** và ký tự `·` | Nhận diện bằng **vị trí nhóm 4 chữ số** (năm): đầu → ISO, thứ ba → ngày trước, cuối → giờ trước. Chép nguyên `17:29:54 · 17/08/2026` kiểu cũ vẫn chạy |
| Nới ô lọc cho khỏi cắt chữ | `.searchBox` 180→**232px**, `.select` 128→**164px** ("Ánh sáng phòng" bị cụt), `.dtBox` **214px** (đủ chứa chuỗi chép từ bảng). Action History sang 2 hàng lọc — chấp nhận, hàng có `flex-wrap` |
| Thêm ô **"Dòng/trang"** chọn từ `PAGE_SIZE_OPTIONS = [8, 10, 12, 20]` | Dropdown thay vì gõ tay: `page_size` sai kiểu bị DRF im lặng bỏ qua (ca A-05). Mặc định vẫn **10** (BR-08, mọi ví dụ tài liệu tính theo 10). Đổi cỡ trang thì `page` về 1. Backend cho tối đa 100 nên 8/12/20 đều hợp lệ. Xử xong điểm treo `05-API.md` §12 điểm 2c |

**Dọn giao diện (cùng phiên, người dùng yêu cầu):** bỏ hẳn các dòng ghi chú `fNote` — "Hai ô Giá trị chỉ mở khi…", "Đang lọc theo một cảm biến…", "Đang lọc thời gian: …" — và dòng `v0.1 · dữ liệu giả (MSW)` ở chân sidebar (kéo theo `approxLabel()` trong `format.js` và `.foot` trong `Layout.module.css` thành mã chết, đã xoá). **Dòng báo lỗi đỏ giữ nguyên.** Placeholder ô Thời điểm đổi từ số cụ thể sang khuôn **`dd/mm/yyyy hh/mm/ss`**. *(Ô gợi ý tài khoản/mật khẩu MSW ở màn Login vẫn còn — chưa được yêu cầu bỏ.)*

**Kiểm chứng:** `npm run build` qua · script Chrome headless + CDP (`scratchpad/ui-when.mjs` **13/13**, `scratchpad/ui2.mjs` **11/11**, không nằm trong repo), không có lỗi JS: một ô duy nhất trên cả 2 trang, 4 mức độ chính xác, gõ sai → báo lỗi, nút lịch điền ngược lại ô chữ, mốc `17:29:54` thiếu độ ẩm ra **đúng 2 dòng**, chép nguyên mốc từ bảng → đúng 3 dòng của chu kỳ, chọn 8/20 dòng/trang, không ô lọc nào cắt chữ.

> ⚠️ **Bẫy khi viết kịch bản CDP** (mất 2 lượt): mỗi `Runtime.evaluate` dùng **chung phạm vi toàn cục**, nên `const s = …` ở lần gọi thứ hai ném `Identifier 's' has already been declared` — lệnh im lặng không chạy, trông hệt như lỗi ứng dụng. Luôn bọc trong `(() => { … })()`.

**⚠️ Tài liệu chưa sửa theo:** `01-SRS.md` §4.1 (sơ đồ màn Data Sensor / Action History còn vẽ 2 ô ngày, chưa có ô Dòng/trang) · `02-UseCase.md` UC-04 · `05-API.md` §4.3/§4.6 ví dụ lọc theo khoảng thời gian và §12 điểm 2c (đã xử) · `docs/wireframe/02-data-sensor.html`, `03-action-history.html`, `wireframe.html` (cả thứ tự cột Thời gian) · `BaoCao.md` và bản Word.

### 0.2 Các quyết định thiết kế đã chốt trong phiên 1

| Quyết định | Lý do |
|---|---|
| Backend **Django**, không dùng FastAPI | Người dùng đã quen Django và Redis; đổi lại phải chạy 2 tiến trình |
| Chấp nhận **2 tiến trình + Redis** | Django đồng bộ, không giữ được vòng lặp MQTT trong tiến trình web (§5.1) |
| Thêm trường **`request_id`** vào `device_control` / `device_respond` | Bảng của GV không có; thiếu nó thì BE không biết phản hồi ứng với bản ghi `action_history` nào |
| UC-04 là **`«extend»`** UC-03/UC-05, không phải `«include»` | Phân trang nằm trong luồng cơ sở; tìm kiếm/lọc/sắp xếp là tùy chọn (`02-UseCase.md` §4.1) |
| Thêm **`«include»` UC-02 → UC-05** | Mỗi lệnh điều khiển luôn sinh một bản ghi lịch sử (BR-05) |
| Giữ **6 lifeline** như bảng GV cho sequence chính | Vẽ thêm 1 sequence "mức triển khai" riêng để giải thích Redis |
| Redis **không** vào `02-UseCase` và `04-Database` | Không phải actor, không lưu dữ liệu nghiệp vụ — chỉ xuất hiện ở SRS và Sequence |

### 0.2b Quyết định thiết kế CSDL đã chốt trong phiên 2 *(chi tiết ở `04-Database.md`)*

> ⚠️ **Bốn dòng dưới đây đã bị bản v2.0 thay thế (§0.2k), đừng áp dụng lại:** ~~`sensor_data.device_id` không phải khóa ngoại~~ (nay là FK thật, node chuyển lên `sensor.node_id`) · ~~ba cột số đo cho phép `NULL`~~ (nay `value` là `NOT NULL`, không đo được thì không có dòng) · ~~ràng buộc BR-02 đặt ở cả 2 tầng ngang nhau~~ (tầng CSDL nay yếu hơn hẳn) · ~~không tạo bảng cho người dùng~~ (nay có `users_user`). Các dòng còn lại vẫn có hiệu lực.

| Quyết định | Lý do |
|---|---|
| `recorded_at` do **backend** sinh, bỏ qua `timestamp` trong payload | ESP8266 không có RTC; lấy giờ thiết bị thì biểu đồ có thể nhảy lùi (§2.1) |
| `sensor_data.device_id` **không** phải khóa ngoại | Node cảm biến (`esp8266_room01`) khác khái niệm thiết bị chấp hành (`led1`) — hai thứ cùng tên "device" (§2.2) |
| Giữ cả `devices.id` (khóa kỹ thuật) lẫn `devices.code` (khóa nghiệp vụ) | URL API dùng `id`; payload MQTT dùng `code` vì firmware cần chuỗi cố định, không phụ thuộc số thứ tự CSDL sinh ra |
| `current_state` lưu sẵn ở bảng `devices` | Phi chuẩn hóa có chủ đích, tránh N truy vấn con mỗi lần mở Dashboard; chỉ cập nhật ở đúng một chỗ trong mã |
| Chỉ cập nhật `current_state` khi `SUCCESS` | Cột này phản ánh trạng thái vật lý **đã xác nhận**, không phải ý định người dùng |
| `request_id` kiểu `uuid` (16 byte) | Nhanh hơn so sánh chuỗi, `uuid4()` duy nhất mà không cần hỏi CSDL (BR-06) |
| Timeout 5s xử lý bằng **vòng quét trong `mqtt_worker`**, không dùng `threading.Timer` | Trạng thái nằm trong CSDL nên tự khôi phục sau khi khởi động lại tiến trình (§5.3) |
| Ràng buộc BR-02 đặt ở **cả 2 tầng** (worker + `CheckConstraint`) | Worker để ghi log message gốc; CSDL là lưới an toàn khi chèn tay qua `psql`/admin |
| Khóa ngoại `on_delete=PROTECT` | NFR-06 — không được mất lịch sử. **Lưu ý:** Django không sinh `ON DELETE RESTRICT` trong DDL, đây là quy tắc tầng ứng dụng (§9.1) |
| Ba cột số đo cho phép `NULL` | UC-07 luồng A2: đọc được một phần vẫn ghi bản ghi. Đặt mặc định 0 thì `0 °C` bị hiểu nhầm là số đo thật |
| Không tạo bảng cho trang Profile | Dữ liệu tĩnh một dòng, đọc từ `.env` |

### 0.2c Quyết định thiết kế Sequence đã chốt trong phiên 3 *(chi tiết ở `03-Sequence.md`)*

| Quyết định | Lý do |
|---|---|
| `POST .../control` trả **`202 Accepted` ngay**, không chờ phần cứng | Chờ `device_respond` thì request treo 5 giây và giữ một thread của `daphne`. Kết quả đẩy về sau qua WebSocket — đúng bản chất bất đồng bộ của MQTT (SD-01 §2.5) |
| Toàn bộ view `control` bọc trong **`transaction.atomic()`** | UC-02 E2 nói broker hỏng thì *không* ghi `action_history`, nhưng luồng chính lại ghi `PENDING` **trước** khi publish. Chỉ rollback mới dung hòa được hai điều này (SD-01 §2.4) |
| Timeout **không** sinh sự kiện WS thứ ba | Dùng lại `device.state` với `status:"FAILED"` + `error_message`, giữ đúng hợp đồng 2 sự kiện của SRS §4.4; FE chỉ cần một hàm xử lý cho mọi kết cục của lệnh (§8.2) |
| Ghi nhận **độ trễ timeout thực tế là 5–6 giây**, không phải đúng 5 | Vòng quét chạy mỗi 1 giây nên bản ghi vừa hết hạn phải chờ lượt sau. Nói rõ trong báo cáo thay vì để người chấm tự phát hiện (SD-05 §6.3) |
| Frontend có **bộ đếm dự phòng ~7 giây** tự mở khóa công tắc | WebSocket đứt đúng lúc lệnh đang chạy thì `device.state` không bao giờ tới → công tắc khóa vĩnh viễn (SD-05 §6.3) |
| BR-07 (ngoại tuyến 30s) phát hiện ở **Frontend** | FE vốn đã nhận sự kiện realtime, chỉ cần `setTimeout` đặt lại mỗi lần có `sensor.data`; backend không phải đếm giờ (SD-04 §5.3) |
| **UC-06 không có sequence riêng** | Chỉ một lời gọi `GET /api/profile` trả dữ liệu tĩnh từ `.env`, không có tương tác nhiều bước để vẽ (§9) |
| SD-06 gộp chung UC-03/UC-04/UC-05 | Ba use case dùng cùng một khuôn DRF (search/filter/ordering/pagination), chỉ khác endpoint và tên cột |
| Màn hình lịch sử **không** dùng WebSocket | Bảng lịch sử là ảnh chụp tại một thời điểm; tự chèn dòng mỗi 2 giây thì dòng đang đọc trôi xuống liên tục (§7.2) |

### 0.2d Quyết định thiết kế API đã chốt trong phiên 4 *(chi tiết ở `05-API.md` §11)*

| Quyết định | Lý do |
|---|---|
| **`409 DEVICE_BUSY`** khi thiết bị còn lệnh `PENDING` — mở rộng BR-04 xuống tầng máy chủ | Khóa công tắc ở Frontend chỉ có tác dụng trong **một tab**; kịch bản T-15 mở 2 tab là lách qua được, sinh 2 bản ghi `PENDING` và 2 lệnh MQTT. Máy chủ là nơi duy nhất chặn được (`05-API.md` §4.5) |
| **`trailing_slash=False`** cho `DefaultRouter` | Mặc định sinh `/api/sensors/`; gọi `POST /api/devices/1/control` thiếu `/` sẽ bị `APPEND_SLASH` chuyển hướng `301` và **mất toàn bộ body** — lệnh điều khiển biến mất im lặng (§2.5) |
| **`TIME_ZONE = "UTC"`** trong `settings.py`, API luôn trả hậu tố `Z` | DRF tuần tự hóa datetime theo `settings.TIME_ZONE`. Đặt `Asia/Ho_Chi_Minh` thì API trả `+07:00`, lệch với mọi ví dụ ở 4 tài liệu trước. Đổi sang giờ VN là việc của Frontend (§2.4) |
| **Bộ lọc thời gian phải kèm múi giờ** (`2026-08-17T00:00:00+07:00`) | Chuỗi thiếu offset bị hiểu là UTC → khoảng "từ 0h" thực chất bắt đầu 7h sáng, **sai 7 tiếng mà không có lỗi nào** (§2.4) |
| **Cấu trúc lỗi thống nhất** `{error:{code,message,details}}` + bộ xử lý ngoại lệ tùy chỉnh | DRF mặc định trả `{"detail":…}` cho ngoại lệ nhưng `{"action":[…]}` cho lỗi serializer — 2 hình dạng trong cùng 1 API, FE phải viết 2 nhánh và không có mã lỗi ổn định (§2.6, mã ở §7.4) |
| **`204 No Content`** cho `/api/sensors/latest` khi bảng rỗng | Bảng rỗng là trạng thái bình thường lúc mới cài, không phải lỗi. `404` gây hiểu nhầm sai URL; `200` kèm toàn `null` bắt FE kiểm `null` từng trường (§4.1) |
| **`/api/sensors/chart` trả thứ tự tăng dần**, bỏ `id` và `device_id` | Recharts vẽ theo thứ tự phần tử trong mảng. Truy vấn vẫn `DESC LIMIT 20` để dùng index rồi đảo trong Python — nếu để FE đảo thì phải nhớ quy ước này ở thêm một chỗ nữa (§4.2) |
| **`GET /api/devices` không phân trang** | Bảng cố định 2 dòng. ⚠️ Phải đặt `pagination_class = None` vì `PAGE_SIZE` là cấu hình toàn cục, nếu không FE nhận `undefined` khi duyệt mảng (§4.4) |
| Thiết bị `is_active = false` → **`404`**, không phải `403`/`409` | Thiết bị đã tháo không có trong `GET /api/devices`, coi như không tồn tại dưới góc nhìn API. Cài đặt gọn: `get_object_or_404(Device.objects.filter(is_active=True), pk=pk)` |
| **`search` của `/api/sensors` chỉ khớp `device_id`** | `SearchFilter` sinh `ILIKE`, chỉ dùng được cho cột chuỗi — bảng này có đúng một cột chuỗi (§4.3) |
| **Lọc theo khoảng giá trị số đo** — 6 tham số `temperature__gte/lte`, `humidity__gte/lte`, `light__gte/lte` *(bổ sung cuối phiên 4)* | Hiện thực dropdown "Cột ▾" đã vẽ trên wireframe và lời hứa của FR-10. **Không thêm index** — xem ghi chú bên dưới (§4.3) |
| **Một mã lỗi `INVALID_RANGE` dùng chung** cho khoảng thời gian lẫn khoảng giá trị | FE chỉ cần một nhánh xử lý; ô nào sai thì đọc `details` (§2.6) |
| **API không trả nhãn tiếng Việt** cho enum (không có `*_display`) | FE vốn đã sở hữu toàn bộ chuỗi hiển thị; thêm `_display` là chia đôi trách nhiệm dịch ra hai nơi (§2.3) |
| **WebSocket một chiều**, message từ client chỉ ghi log rồi bỏ | Điều khiển cần mã lỗi 400/404/409/503 — thứ WebSocket không có sẵn cơ chế biểu diễn (§5.1) |
| **Không dùng `retain`** ở cả 3 topic MQTT | ESP8266 khởi động lại sẽ nhận lại lệnh `device_control` cũ và **tự bật đèn** (§6.1) |
| P1 dùng **client ID ngẫu nhiên** `backend_api_<hex>` | Broker ngắt kết nối cũ khi trùng client ID → hai lệnh bấm gần nhau tự đá nhau ra khỏi broker (§6.1) |

> ⚠️ **Hai điều phải nhớ về bộ lọc theo giá trị số đo** (thêm cuối phiên 4) — **điểm 1 đã hết hiệu lực từ v2.0 (§0.2k): không còn cột `NULL` nên không còn hiện tượng này. Điểm 2 vẫn đúng, nay áp cho cột `value`.**
> 1. **Bản ghi có số đo `null` bị loại khỏi kết quả** ở *cả hai* chiều — `temperature__gte=30` và `temperature__lte=30` đều không khớp dòng có `temperature = NULL`, vì mọi phép so sánh với `NULL` trong SQL đều không thỏa mãn. Hệ quả: `count` khi lọc theo nhiệt độ nhỏ hơn khi lọc theo thời gian tương ứng. Đúng chuẩn SQL nhưng dễ bị hiểu là lỗi — Figma nên có chú thích cạnh bộ lọc.
> 2. **Ba cột số đo vẫn không có index**, có chủ đích: 43.200 lượt ghi/ngày so với vài lượt lọc thủ công mỗi phiên, lại thêm độ chọn lọc thấp (nhiệt độ phòng chỉ dao động 25–32 °C nên `>= 30` khớp phần lớn số dòng, PostgreSQL sẽ bỏ qua index). Lý do đầy đủ ở `04-Database.md` §5.2 bản 1.1; cách đo lại ở §11.2.

> ⚠️ **Bẫy `paho-mqtt` phải nhớ khi code tuần 3** (`05-API.md` §7.4):
> 1. Bắt buộc gọi `loop_start()` **trước** `publish(qos=1)` rồi `wait_for_publish(timeout=2)`. Không có vòng lặp mạng chạy nền thì message chỉ nằm trong hàng đợi và `disconnect()` vứt nó đi — API vẫn trả `202` trong khi lệnh **chưa từng rời khỏi máy chủ**.
> 2. `paho-mqtt` **2.x** đổi chữ ký: `mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=…)`. Bản 1.6.x thì bỏ tham số đầu — cùng loại bẫy với `CheckConstraint(condition=)` của Django 5.1 ở §0.4.
> 3. `connect()` phải có timeout, nếu không broker chết sẽ treo request tới hết `keepalive`, phá vỡ NFR-01.

### 0.2e Quyết định về wireframe co giãn *(cuối phiên 5 — `docs/wireframe/*.html`)*

| Quyết định | Lý do |
|---|---|
| Khung `.app` **rộng 100%, tối đa 1680px, cao `100%` cửa sổ** thay cho `1180×660` ghim cứng | Trên màn hình rộng, bản cũ để thừa ~180px viền xám mỗi bên. Chặn 1680px để màn hình siêu rộng không kéo panel thiết bị ra quá to |
| **Biểu đồ tách làm hai phần**: nét vẽ nằm trong SVG `preserveAspectRatio="none"`, còn nhãn trục và chấm cuối đường vẽ bằng HTML đặt tuyệt đối | SVG cũ để `height:auto` nên **cao theo tỉ lệ bề ngang** — càng rộng càng cao, tràn khỏi cửa sổ. Kéo giãn tự do thì chữ và hình tròn trong SVG bị méo, nên phải đưa chúng ra ngoài. Nét vẽ giữ đúng 2.5px nhờ `vector-effect="non-scaling-stroke"` |
| Giữ nguyên `viewBox="48 20 623 336"` — đúng toạ độ cũ của vùng vẽ | Không phải tính lại 60 điểm dữ liệu của 3 đường; chỉ cắt bỏ phần lề chứa chữ |
| Cột thiết bị rộng `calc((100% - 32px)/3)` | Giữ đúng ý đồ cũ: mép trái panel thiết bị trùng mép trái thẻ số liệu thứ ba, ở **mọi** bề ngang cửa sổ |
| Bảng dùng **`colgroup` theo phần trăm**, không phải px | Cột px cố định thì bảng không lấp đầy thẻ khi cửa sổ rộng, thừa một mảng trắng bên phải |
| Thân bảng bọc trong `.tbl{overflow:auto}` + `thead th{position:sticky}` | Thanh phân trang luôn nằm sát đáy thẻ; cửa sổ thấp thì cuộn phần thân, tiêu đề cột vẫn thấy |
| Trang Profile xếp **2 cột** (thông tin ⟷ liên kết), 4 liên kết xếp dọc | Xếp chồng như cũ thì màn rộng chỉ dùng nửa trên, dưới toàn nền xám |
| `min-width:1100px` + `min-height:620px`, thiếu chỗ thì `.body` tự cuộn | Dưới ngưỡng đó bố cục 2 cột vỡ; cho cuộn còn hơn để các khối bị bóp méo |

### 0.2f Bộ dữ liệu mẫu chuẩn *(chốt cuối phiên 5 — dùng chung cho mọi tài liệu và bản vẽ)*

> ✅ **Đã tính lại theo mô hình v2.0** *(phiên 7)*. **Giá trị đo không đổi một số nào** — chỉ đổi cách đếm bản ghi và mã thiết bị.

Mọi con số ví dụ trong `05-API.md`, `docs/wireframe.html` và `docs/wireframe/*.html` **phải lấy từ đúng bộ này**. Sửa một chỗ thì sửa hết — phiên trước từng để cùng một bản ghi mang hai giá trị nhiệt độ khác nhau ở hai màn hình.

**Số liệu cảm biến** — 20 **chu kỳ** từ `17:29:24` đến `17:30:02`, cách nhau 2 giây, node `esp8266_room01`.
Mỗi chu kỳ sinh **3 bản ghi** (một cho mỗi cảm biến) mang **cùng một mốc thời gian** — trừ chu kỳ `17:29:54` chỉ có 2.

| Mốc | id các bản ghi | `room01_temp` | `room01_humi` | `room01_lux` |
|---|---|---|---|---|
| Chu kỳ mới nhất `17:30:02` | 36132 · 36133 · 36134 | 28.5 °C | 72.0 % | 350 lux |
| Chu kỳ cũ nhất trên biểu đồ `17:29:24` | 36076 · 36077 · 36078 | 27.6 °C | 70.2 % | 352 lux |
| `17:29:54` — **thiếu độ ẩm** | 36121 · *(không có)* · 36122 | 28.4 °C | **không có bản ghi** | 352 lux |
| Đỉnh độ ẩm `17:29:40` | — | — | 88.3 % | — |
| Đáy ánh sáng `17:29:42` | — | — | — | 88 lux |

- **Tổng số bản ghi: `36.134`** = 12.045 chu kỳ × 3 − 1 số đo thiếu. Con số lẻ này chính là bằng chứng của UC-07 A2, đừng làm tròn thành 36.135.
- Cửa sổ 20 chu kỳ trên biểu đồ trải từ **id 36076 → 36134**, tức **59 bản ghi** (không phải 60).
- Ba thẻ số liệu hiển thị chu kỳ mới nhất; biến thiên tính bằng **giá trị hiện tại − giá trị của 10 chu kỳ trước** (20 giây): `−0.1` · `−14.4` · `+262`.
- Chu kỳ `17:29:54` **không có bản ghi độ ẩm** (UC-07 A2) ⇒ **đường độ ẩm trên biểu đồ phải đứt một đoạn** tại mốc đó. Bảng Data Sensor **không hiện dòng nào** cho cảm biến độ ẩm ở mốc ấy — khác bản cũ vốn hiện dấu `—` trong một ô.
- Bộ lọc mẫu của màn Data Sensor: *cảm biến `room01_temp`, giá trị ≥ 28*, ngày 17/08 → **1.284 bản ghi khớp, 129 trang**. Con số này **giữ nguyên** so với bản cũ: lọc theo một cảm biến thì mỗi chu kỳ lại chỉ còn đúng một dòng.

**Lịch sử thao tác** — tổng 88 bản ghi, hai thiết bị `room01_lamp` (Đèn phòng) và `room01_fan` (Quạt trần):

| id | Thời gian | Thiết bị | Lệnh | **Người thao tác** | Kết quả | Trạng thái sau |
|---|---|---|---|---|---|---|
| 79 | 16:55:07 | Quạt trần | OFF | **`—`** | SUCCESS 421 ms | quạt OFF |
| 80 | 16:58:12 | Đèn phòng | ON | Lưu Đức Anh | SUCCESS 396 ms | đèn ON |
| 81 | 17:02:40 | Đèn phòng | OFF | Lưu Đức Anh | SUCCESS 377 ms | đèn OFF |
| 82 | 17:08:51 | Quạt trần | ON | Người vận hành | SUCCESS 443 ms | quạt ON |
| 83 | 17:12:19 | Đèn phòng | ON | Lưu Đức Anh | SUCCESS 401 ms | đèn ON |
| 84 | 17:15:33 | Đèn phòng | OFF | Người vận hành | SUCCESS 388 ms | **đèn OFF** ← `room01_lamp.updated_at` |
| 85 | 17:17:26 | Quạt trần | OFF | Người vận hành | SUCCESS 455 ms | quạt OFF |
| 86 | 17:20:02 | Quạt trần | ON | Lưu Đức Anh | **FAILED** 5.523 ms (timeout) | quạt vẫn OFF |
| 87 | 17:28:07 | Quạt trần | ON | Lưu Đức Anh | SUCCESS 412 ms | **quạt ON** ← `room01_fan.updated_at` |
| 88 | 17:31:44 | Đèn phòng | ON | Lưu Đức Anh | **PENDING** | đang chờ |

- ⇒ **Dòng 79 để `—` là có chủ đích** — minh họa `user_id = NULL` (BR-12), tương ứng lệnh thử bằng `mosquitto_pub` ở tuần 2. Nhờ nó bản vẽ và tài liệu giải thích được vì sao cột này cho phép rỗng, mà không phải bịa thêm bản ghi. Đây cũng là dòng dùng cho ca kiểm thử `?user=none` (`05-API.md` A-11e).
- ⇒ Hai tài khoản seed: `admin` — **Lưu Đức Anh** (id 1) và `operator` — **Người vận hành** (id 2).
- ⇒ Dashboard chụp lúc `17:30:02` phải hiển thị **đèn OFF, quạt ON** — đúng ví dụ `GET /api/devices` (`05-API.md` §4.4), trong đó `updated_at` của mỗi thiết bị bằng `responded_at` của lệnh `SUCCESS` gần nhất.
- ⇒ `id 88` chính là lệnh sinh ra phản hồi `202` ở §4.5 (`request_id` `3f2b8c1e-…`) và sự kiện WebSocket ở §5.3. Bản vẽ Action History chụp khi nó còn `PENDING`.
- ⇒ Mạch chuyện `86 FAILED → 87 SUCCESS` cho phép minh họa cả timeout lẫn thao tác bấm lại mà không cần bịa thêm bản ghi.

### 0.2g Rà soát chéo phiên 6 — 7 lỗi nghiệp vụ đã sửa

Nguyên tắc rút ra: **mỗi khi một tài liệu sau chốt thêm một quy định, phải hồi tố lên tài liệu trước**, nếu không quy định đó "mồ côi" — có mã lỗi trong API mà không truy vết được về quy tắc nghiệp vụ nào.

| # | Lỗi | Đã sửa thành | File bị ảnh hưởng |
|---|---|---|---|
| 1 | **`409 DEVICE_BUSY` mồ côi.** `05-API.md` chốt ở phiên 4 nhưng BR-04 và bảng ngoại lệ UC-02 không hề nhắc tới → đọc đặc tả UC-02 rồi mở Swagger thấy `409` là không giải thích được | Thêm **luồng ngoại lệ UC-02 E6**; BR-04 viết lại thành quy tắc **hai tầng** (FE khóa công tắc + BE trả `409`); bước 3 luồng chính thêm việc kiểm tra lệnh đang chờ; SD-01 §2.4 thêm nhánh `alt` E6 | `01-SRS.md` UC-02 A3 · `02-UseCase.md` UC-02 + BR-04 · `03-Sequence.md` §2.4, §9 · `04-Database.md` §11 · `05-API.md` §4.5, §9.2, A-13 · `BaoCao.md` §3.2.1, §3.3 |
| 2 | **Dữ liệu mẫu biểu đồ lệch bộ chuẩn §0.2f.** `05-API.md` §4.2 ghi mẫu `10:29:24Z` là 28.3 °C / 71.5 % / 349 lux, trong khi bản vẽ Dashboard vẽ 27.6 / 70.2 / 352 | Sửa theo bộ chuẩn (đã kiểm lại bằng toạ độ `polyline` của `01-dashboard.html`), thêm bản ghi `12041` thiếu độ ẩm + giải thích vì sao endpoint này **không** loại bản ghi `null` (khác §4.3) | `05-API.md` §4.2 |
| 3 | **Ngữ nghĩa `responded_at` mâu thuẫn luồng timeout.** Mô tả là "thời điểm nhận `device_respond`", nhưng lệnh hết giờ **không có** phản hồi nào mà vẫn phải ghi mốc này — bắt buộc, vì ràng buộc `action_responded_consistency` | Đổi thành **"thời điểm lệnh kết thúc"**; giải thích `latency_ms` của lệnh hết giờ (5.000–6.000 ms) là *thời gian chờ đã bỏ ra*, không phải thời gian phần cứng phản hồi | `04-Database.md` §3.1, §4.3, §5.1, §8.2 · `05-API.md` §4.6 · `BaoCao.md` §2.4.3 |
| 4 | T-07 ở SRS còn ghi "sau **5** giây" | "sau **5–6** giây", khớp chu kỳ vòng quét 1 giây | `01-SRS.md` §7 |
| 5 | Client ID MQTT: SRS ghi `backend_server`, API chốt `backend_worker` + `backend_api_<ngẫu nhiên>` | Sửa SRS theo API (P1 phải dùng ID ngẫu nhiên, xem §0.2d) | `01-SRS.md` §4.3 |
| 6 | Số ca kiểm thử API ghi **22**, thực tế **21** (A-01→A-18 + A-07b/c/d) | Sửa thành 21 ở mọi nơi | `05-API.md` §10, §13 · `BaoCao.md` §4.3, Phụ lục A |
| 7 | `CODE_BY_STATUS` ở `05-API.md` §7.5 sinh thêm `CONFLICT` và `SERVICE_UNAVAILABLE` — hai mã không có trong "danh sách 7 mã lỗi của toàn hệ thống" ở §2.7 | Map dùng đúng `DEVICE_BUSY` / `BROKER_UNAVAILABLE` | `05-API.md` §7.5 |

**Lỗi hình thức đã sửa kèm:** ví dụ `sensor.data` ở `03-Sequence.md` §8.2 dùng ngày `2026-08-14` (mọi nơi khác là `17`) · `request_id` mẫu trong SRS §4.3 không phải UUID · bảng `devices_device` ở `BaoCao.md` §2.4.2 thiếu `created_at`/`updated_at` (mà `updated_at` chính là trường `GET /api/devices` trả về) · bảng bàn giao SRS §8.3 còn ghi "SRS v0.1" · `tools/assemble.py` sửa 2 lỗi (xem §5.4).

**Hai điểm đã kiểm và KHÔNG phải lỗi — đừng báo lại:**
- `01-SRS.md` §6 (ERD mức khái niệm) thiếu `device_type` / `is_active` / `error_message`: cố ý, `04-Database.md` là bản có hiệu lực cho chi tiết vật lý.
- `04-Database.md` ghi "7 chỉ mục" trong khi bảng §5.2 có 8 dòng: con số 7 đếm theo **7 lệnh `CREATE INDEX`** trong DDL §9, còn bảng §5.2 gộp/tách khác đi. Không sai.

**Rủi ro cài đặt phát hiện kèm (chưa sửa được vì thuộc tuần 3):** ca **A-05** kỳ vọng `page_size=abc` → `400`, nhưng `PageNumberPagination` mặc định **im lặng bỏ qua** giá trị sai kiểu và trả `200`. Muốn A-05 đạt thì phải tự kiểm tra trong `StandardPagination` (`05-API.md` §7.1).

### 0.2h ⚠️ QUY TẮC BẮT BUỘC — không ghi đè file Word người dùng đang chỉnh

**Người dùng có chỉnh tay trực tiếp trong Word.** Pipeline `assemble.py` thì **sinh đè** file đích mỗi lần chạy, nên mọi chỉnh sửa tay đều bị xoá sạch ở lần dựng kế tiếp. Phiên 6 đã xảy ra đúng chuyện này: `docs/BaoCao.docx` bị ghi đè lúc 11:14 và không khôi phục được (máy **không** bật File History, **không** có Volume Shadow Copy, Word không để lại file `.asd` nào).

| Quy tắc | Chi tiết |
|---|---|
| **Hỏi trước khi dựng đè bất kỳ file `.docx` nào** | Kể cả `BaoCao.docx` và `01-SRS.docx`. Không tự ý chạy `assemble.py` lên file đã tồn tại |
| **Không chắc thì xuất ra tên tạm** | Dựng sang `BaoCao-tam.docx` rồi để người dùng tự đối chiếu, an toàn hơn là hỏi rồi đoán |
| **Kiểm tra trước khi ghi đè** | So `LastWriteTime` và kích thước file `.docx` với lần dựng gần nhất của mình. Lệch = người dùng đã mở Word sửa và lưu → **dừng lại, hỏi** |
| **Đổi tên thay vì dựng lại** | Khi người dùng chốt một bản, dùng `mv`/`Rename-Item` để giữ nguyên mọi chỉnh sửa tay, **đừng** dựng lại từ `.md` rồi ghi đè |

*(phiên 6)* Đã xảy ra một lần mất dữ liệu vì vi phạm quy tắc này: `BaoCao.docx` bị ghi đè lúc 11:14 và không khôi phục được — máy **không** bật File History, **không** có Volume Shadow Copy, Word không để lại file `.asd` nào.

### 0.2l ⚠️ Trạng thái các file Word *(cập nhật cuối phiên 7)*

| File | Nội dung | Vai trò |
|---|---|---|
| **`docs/BaoCao-moi - Copy.docx`** | Bản người dùng chỉnh tay **+ đã đồng bộ hoàn toàn sang mô hình v2.0** *(mục 2.4, chương 1, chương 3, bảng endpoint)* **+ chương 3 đã sắp xếp lại: sequence và ảnh Figma nằm trong từng use case** | ✅ **BẢN ĐANG DÙNG** |
| `docs/BaoCao-moi.docx` | Bản người dùng chỉnh tay, mục 2.4 **còn là mô hình 3 bảng cũ** | Bản lùi, giữ nguyên làm dự phòng |
| `docs/BaoCao.docx` | *(người dùng đã xoá/chuyển đi trong phiên 7)* | — |
| `docs/01-SRS.docx` | Dựng ở phiên 6, **chưa cập nhật v2.0** | Cần dựng lại nếu phải nộp |

> ⚠️ **Bản Word đã rẽ nhánh khỏi `BaoCao.md`.** Người dùng tự cắt bớt nhiều thứ trong Word: chương 4 rút còn *Kết luận* + *Hạn chế và hướng phát triển* (bỏ toàn bộ phần kết quả kiểm thử), mục 2.4 bỏ tiểu mục *Chỉ mục*, mục 3.6 bỏ *Đặc tả endpoint trọng tâm*, và **đổi toàn bộ style tiêu đề sang `BTL-H1/H2/H3`** của mẫu PTIT.
>
> ⇒ **TUYỆT ĐỐI KHÔNG chạy `assemble.py` ghi đè lên các file này.** Dựng lại từ `.md` sẽ mất hết phần đã cắt gọt. Muốn cập nhật thì **sửa đúng mục cần sửa ngay trong file Word** — cách làm ở §0.2m.

### 0.2m Cách sửa một mục trong file Word mà không đụng phần còn lại *(phiên 7)*

Đã làm thành công cho mục 2.4 của `BaoCao-moi - Copy.docx`. Quy trình 4 bước, script mẫu ở thư mục scratchpad (`fix24.py`, `verify.py`):

1. **Dò cấu trúc bằng cách đọc `word/document.xml`**, đừng lặp qua `doc.Paragraphs` bằng COM — file 1.500 đoạn thì COM mất vài phút, còn đọc XML thì tức thì. Giải nén bằng `unzip`, tìm `<w:pStyle w:val="BTL-H2">` để lấy danh sách tiêu đề.
2. **Thay ảnh ở mức zip**, không chèn ảnh mới qua COM: đọc file `.docx` bằng `zipfile`, ghi đè đúng `word/media/imageN.png`, giữ nguyên mọi entry khác. Cách này **bảo toàn caption cùng trường `SEQ Hình`** — chèn ảnh mới qua COM sẽ làm hỏng đánh số hình tự động. Sau đó chỉnh lại `InlineShape.Height` cho đúng tỉ lệ ảnh mới (nhớ `LockAspectRatio = 0` trước).
3. **Sửa nội dung bằng Word COM**: dò mốc theo *style + văn bản* chứ không theo chỉ số cứng; xoá `doc.Range(start, end)` rồi `Range.InsertFile(fragment.docx)`. Fragment dựng bằng pandoc với `--reference-doc=MauBaoCao.docx`.
   ⚠️ **Pandoc sinh style `Heading 2/3`, còn tài liệu dùng `BTL-H2/H3`** — hai tên khác nhau, phải **đổi style thủ công sau khi chèn**, nếu không tiêu đề mới không vào được mục lục và nhìn khác hẳn phần còn lại.
4. **Kiểm chứng bắt buộc**: bung text cả bản cũ lẫn bản mới ra `plain`, cắt bỏ đúng mục vừa sửa ở cả hai, rồi `difflib` phần còn lại. Kỳ vọng: **chỉ khác đúng mấy dòng mục lục của chính mục đó**. Nhớ chuẩn hoá trước khi so — pandoc tự đánh số tiêu đề (`16.`, `17.`…) nên thêm một tiểu mục là mọi số phía sau đều lệch, gây nhiễu diff.

### 0.2i Cách dựng hình từ SVG *(thiết lập ở phiên 6)*

Máy **không** có `cairosvg` / `svglib` / Inkscape, nhưng **có sẵn Chrome và Edge** — dùng chế độ headless để render SVG ra PNG độ phân giải cao:

```bash
# Bọc SVG trong một file HTML tối giản rồi chụp màn hình
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless=new --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=<W>,<H> \
  --screenshot="C:\duong\dan\TUYET_DOI\out.png" "duong/dan/render.html"
```

- ⚠️ Tham số `--screenshot` **bắt buộc là đường dẫn tuyệt đối kiểu Windows**; đưa đường dẫn tương đối thì Chrome báo `Failed to write file ... (0x3)`.
- ⚠️ *(phiên 7)* **File đầu vào cũng phải là URL `file:///` tuyệt đối**, khoảng trắng mã hóa thành `%20`. Đưa đường dẫn tương đối (`render.html`) thì Chrome coi đó là **tên miền**, đi tra DNS, và chụp về ảnh trang lỗi *"This site can't be reached"* — **không báo lỗi gì**, lệnh vẫn ghi file thành công. Mất một lượt vì đúng lỗi này. Luôn mở ảnh ra xem sau khi render.
- `--force-device-scale-factor=2` cho ảnh gấp đôi kích thước SVG → in ngang 15 cm trong Word đạt ~380 dpi, thừa sức nét.
- Cỡ cửa sổ phải khớp `width`/`height` của SVG, nếu không sẽ dư viền hoặc bị cắt.

**Hình đã dựng bằng cách này:**
- `docs/img/architecture.svg` → `architecture.png` (2240×1240) — Hình 2.1 kiến trúc tổng thể.
Sửa file `.svg` rồi render lại là ra bản mới; **đừng sửa trực tiếp file `.png`**.

> ⚠️ **ERD: người dùng chọn bản PlantUML, không dùng bản SVG tay.** Phiên 7 tôi có dựng `docs/img/erd.svg` → `erd.png` bằng cách trên, nhưng cuối phiên **người dùng đã xuất lại `erd.png` từ mã PlantUML ở `04-Database.md` §3.2** (lúc 16:12) cho đồng bộ phong cách với 6 sơ đồ tuần tự. ⇒ **`04-Database.md` §3.2 là nguồn có hiệu lực của ERD.** File `erd.svg` và `render-erd.html` giữ lại nhưng **không dùng nữa** — đừng render đè lên `erd.png`.
>
> ⚠️ **Hệ quả chưa xử lý:** bản Word `BaoCao-moi - Copy.docx` đang nhúng **bản SVG tay**, còn `docs/img/erd.png` là **bản PlantUML**. Hai ảnh khác nhau về hình thức (nội dung thì tương đương). Khi quay lại sửa Word thì thay ảnh trong đó bằng `erd.png` hiện tại — cách thay ở §0.2m bước 2.

Bốn điểm bắt buộc của hình kiến trúc (đã mất 4 lượt nhờ AI vẽ mới ra, đừng để hồi quy):
1. Cả 3 mũi tên MQTT đều nối vào khối **Mosquitto**, tuyệt đối không có đường nối thẳng ESP8266 ↔ Backend.
2. Cả 3 mũi tên nằm **phía trên** khối DHT11, không thẳng hàng với bất kỳ linh kiện nào — nếu không người đọc tưởng `device_respond` do quang trở phát ra.
3. `LM393` (không phải LM333).
4. Không có caption trong ảnh (Word tự đánh số), không có Redis, không có chân GPIO.

### 0.2j Báo cáo nay là bản TỰ CHỨA *(phiên 6)*

Trước đây `BaoCao.md` tự nhận là **"bản rút gọn"** và 4 lần đẩy người đọc sang các file `.md` — trong khi các file đó **không được nộp**. Đã sửa: báo cáo giờ đứng độc lập, không tham chiếu ra ngoài. Cụ thể:

| Trước | Sau |
|---|---|
| §1.5 chỉ liệt kê 10/16 yêu cầu phi chức năng, đánh số nhảy cóc, rồi "xem `01-SRS.md`" | Đủ **16 NFR**, liên tục NFR-01→16 |
| §2.4 kết bằng "12 ràng buộc, 7 chỉ mục: xem `04-Database.md`" | Thêm hẳn **§2.4.4 Ràng buộc toàn vẹn** (12 dòng) và **§2.4.5 Chỉ mục** (7 dòng) kèm lý do |
| §3.6 kết bằng "tham số truy vấn, mã lỗi: xem `05-API.md`" | Thêm **§3.6.3 Tham số truy vấn dùng chung** và **§3.6.4 Bảng mã lỗi toàn hệ thống** (7 mã) |
| §4.3 chỉ có 8/21 ca kiểm thử API | Đủ **21 ca** A-01→A-18 + A-07b/c/d, kèm dòng "Tỷ lệ đạt /21 ca" |
| Phụ lục A: *"Báo cáo này là bản rút gọn…"* | Viết lại: đặc tả cần thiết đã nằm trong chương 1–3; bảng tài liệu gốc thêm cột "tương ứng mục nào trong báo cáo" |
| §2.3 khung Hình 2.3 trỏ sang `CLAUDE.md` §5.1 | Trỏ vào bảng ngay phía trên trong chính báo cáo |

**Năm mâu thuẫn nội bộ đã sửa kèm:** §1.3 ghi "ba loại cảm biến" trong khi §2.2.1 và §3.2.7 nói hai (đúng: **hai cảm biến đo ba đại lượng**) · §2.1 liệt kê khối máy chủ thiếu Redis dù §1.6 và §2.3.1 nói Redis bắt buộc · §3.1 nói phân trang "không tách thành quan hệ riêng" nhưng tên UC-04 lại có chữ "phân trang" (đã tách rõ: phân trang mặc định thuộc luồng cơ sở, thao tác chuyển trang thuộc UC-04) · bảng §3.6.2 có 8 dòng nhưng T-17 nói 7 endpoint (đã nói rõ dòng 8 là WebSocket, không nằm trong Swagger) · UC-03 A2 nói "hiển thị trang trống" còn ca A-06 nói `404` (đã thêm câu nối: giao diện coi `404 PAGE_NOT_FOUND` là trạng thái rỗng).

> Khi thêm nội dung mới vào `BaoCao.md`, **giữ nguyên tính tự chứa** — đừng viết "xem `0X-….md`" nữa. Muốn nói chi tiết thì đưa thẳng nội dung vào báo cáo.

### 0.3 Việc còn treo — làm ở phiên sau

**🔴 ƯU TIÊN 1 — đồng bộ mô hình dữ liệu v2.0 (§0.2k). Chuỗi tài liệu đang không nhất quán, làm việc khác trước là lãng phí.**

- [x] ~~`01-SRS.md`~~ → **v0.5 xong**: §6 mô hình 5 thực thể · FR-17, FR-18 · §2.4 và §8.2 chốt lại chuyện đăng nhập · §3.2 sửa UC-02/03/04/05/07 (UC-07 A4 đổi hành vi) · §4.1 vẽ lại màn Data Sensor + Action History · §4.2/§4.3 đổi tên mã · §4.4 thêm endpoint · NFR-12/13/14 · §7 thêm T-08b/T-10b/T-11b/T-18
- [x] ~~`02-UseCase.md`~~ → **v2.0 xong**: thêm **BR-11**, **BR-12**, BR-02/BR-10 viết lại · UC-01 dựng thẻ từ danh mục + A3 · UC-02 lưu `user_id` + A3 · UC-03 đổi cột, bỏ cột Node · UC-04 dropdown "Cảm biến" + **E4** + gỡ lưu ý `null` · UC-05 thêm cột Người thao tác + A3 · UC-07 luồng chính 9 bước, **E3 đổi hành vi**, thêm E5 · ma trận truy vết mở tới FR-18. **Không phải xuất lại `usecase-diagram.png`**
- [x] ~~`05-API.md`~~ → **v2.0 xong**: 7 → **8 endpoint** (thêm `/api/sensors/devices`) · `/api/sensors/latest` trả **mảng**, bỏ `204` · `/api/sensors` viết lại trường + bộ lọc (`sensor` + `value__gte/lte`) · `/chart` **giữ nguyên hình dạng**, backend xoay bảng · `POST .../control` nhận `user_id` · `/api/actions` thêm `user` + lọc `?user=none` · `/api/devices` thêm `node_id` · §7.1 `AUTH_USER_MODEL` · §7.3 `TiebreakOrderingFilter` · §6.2 gom 3 số đo thành 1 sự kiện WS · 21 → **25 ca kiểm thử**
- [x] ~~`03-Sequence.md`~~ → **v2.0 xong**: SD-03 tra danh mục + `bulk_create` cùng mốc thời gian, E3 loại riêng số đo · SD-04 `DISTINCT ON` trả mảng · SD-01 thêm `user_id` · SD-06 `JOIN` + `ORDER BY` hai cột, gỡ cảnh báo `NULL` · đổi tên mã. **Cấu trúc lifeline không đổi — 6 ảnh SD chỉ cần xuất lại nếu muốn nhãn khớp tuyệt đối**
- [x] ~~Tính lại **bộ dữ liệu mẫu chuẩn §0.2f**~~ → xong: 20 chu kỳ = **59 dòng** (id 36076→36134), tổng **36.134**, thêm cột Người thao tác, dòng 79 để `—`
- [ ] **Chạy tìm–thay bảng đổi tên mã §0.2k trên TẤT CẢ file** — kể cả `wireframe/*.html` (chỗ này phải sửa HTML rồi chụp lại, không tìm–thay được trên ảnh)
- [x] ~~`docs/wireframe/*.html` + `wireframe.html`~~ → **xong**: Data Sensor đổi 6 cột (`ID · Mã cảm biến · Cảm biến · Giá trị · Đơn vị · Thời gian`), 3 dòng/chu kỳ, bộ lọc "Cảm biến ▾" + 2 ô giá trị **vô hiệu khi chưa chọn cảm biến** · Action History thêm cột **Người thao tác** (dòng 79 để `—`) + dropdown lọc + cột Thiết bị hiện cả mã lẫn tên · đổi tên mã ở cả 5 file · ghi chú thiết kế viết lại
- [ ] **Chụp lại ảnh 4 màn hình** từ các file HTML trên (đặt cửa sổ đúng cỡ trước khi chụp — §0.2e)
- [ ] ⚠️ **Xuất lại 3 ảnh sequence: SD-01, SD-02, SD-05** — nhãn đổi ở bản `03-Sequence.md` 2.0.1 (thêm `user_id`). *(SD-03, SD-04, SD-06 và `erd.png` người dùng đã xuất lại chiều 20/08, không cần làm lại.)*
- [x] ~~Xuất lại `docs/img/erd.png`~~ → **xong**: dựng từ `docs/img/erd.svg` bằng Chrome headless, 2760×1660, đủ 5 bảng + 3 quan hệ + khung ghi chú ràng buộc theo cặp (§0.2i)
- [x] ~~`docs/BaoCao.md`~~ → **xong**: §1.3 phạm vi · §1.4 thêm FR-17/FR-18 · §1.5 NFR-12/13/14 · **§2.4 viết lại toàn bộ** (5 bảng, 18 ràng buộc, 7 chỉ mục) · §3.2 sửa cả 5 use case · §3.3 thêm BR-11/BR-12 · §3.5 mô tả ảnh cần chèn · §3.6 bảng endpoint 8 dòng + tham số lọc mới · §4.2 21 ca · §4.3 25 ca · Phụ lục A
- [x] ~~**Cập nhật mục 2.4 trong bản Word**~~ → **xong**: sửa thẳng vào `docs/BaoCao-moi - Copy.docx` bằng phương pháp §0.2m. Đã thay ảnh ERD, viết lại 6 tiểu mục, cập nhật mục lục. Kiểm chứng: ngoài mục 2.4 chỉ có 4 dòng mục lục của chính nó thay đổi. *(Người dùng sau đó tự bỏ tiểu mục "Ràng buộc toàn vẹn" — đừng thêm lại.)*
- [x] ~~**Sắp xếp lại chương 3 trong Word**~~ → **xong**: bỏ hẳn mục 3.4 *Biểu đồ tuần tự* và 3.5 *Thiết kế giao diện*; 6 sequence + 4 ảnh Figma chuyển vào đúng use case; 3.6 API lùi thành 3.4. Hình đánh số lại 1→13 theo thứ tự mới. Thêm 3 ghi chú in nghiêng ở UC-01/02/04 để người dùng tự chụp bổ sung
- [x] ~~**Đồng bộ nội dung Word sang v2.0**~~ → **xong**: 26 ô bảng sửa chữ + 9 dòng chèn thêm, trải khắp chương 1 (§1.3, FR-10/14/16, thêm FR-17/18, NFR-12/13/14), chương 3 (UC-01→UC-07, BR-02, BR-10, thêm BR-11/12) và mục API (ô Xác thực, bảng endpoint 7→8 endpoint, bảng tham số lọc)
- [ ] **Bản Word còn hai việc**: ① thay ảnh ERD trong đó bằng `docs/img/erd.png` bản PlantUML (hiện đang là bản SVG tay) · ② người dùng tự chụp 3 ảnh trạng thái phụ theo ghi chú in nghiêng đã đặt sẵn

**Việc cũ:**

- [x] ~~Kiểm tra thông tin cá nhân tự suy đoán~~ — **đã xác nhận từ `docs/BTH1.docx`** (do người dùng tự dựng/chỉnh, coi là nguồn đúng): chức danh GV là **`TS.`** (không phải `ThS.` như đoán trước), mã học phần là **`INT14149`**. Đã sửa `tools/assemble.py` (§0.2k trở đi dùng giá trị mới). *(còn 1 chỗ chưa sửa: §4.7 của `05-API.md` vẫn ghi `ThS.` — cần đổi thành `TS.` khi động tới file đó lần sau)*. Lớp `D23CQAT01-B` chưa thấy nhắc tới trong `BTH1.docx`, vẫn chưa xác nhận được
- [x] ~~Xuất sơ đồ PlantUML ra PNG~~ — đã có 8 ảnh trong `docs/img/`
- [ ] **Đổi tên 6 ảnh sequence cho nhất quán** — tên hiện tại lộn xộn (`SD01_DieuKhienThietBi_NghiepVu.png`, `SD-02_Dieukhienbattatthietbi.png`, `SD-04.png`…), không khớp quy ước ở `03-Sequence.md` §1.5 (`sd-01-control-business.png` → `sd-06-history.png`). Nên thống nhất **trước khi** chèn vào Word
- [x] ~~**Dựng lại 2 bản Word**~~ — đã dựng lại ở phiên 6 sau khi sửa hết mâu thuẫn: `docs/BaoCao.docx` **31 trang / 43 bảng**, `docs/01-SRS.docx` **23 trang / 22 bảng**. Đã kiểm chứng lại bằng cách bung text cả hai file rồi so từng dòng với `.md` — khác biệt duy nhất còn lại là bìa, mục lục và caption ảnh (do `assemble.py` sinh ra)
- [ ] **12 chỗ trống trong `docs/BaoCao.md`** chờ chèn ảnh — mỗi chỗ là một khung bảng ghi rõ cần vẽ gì:
  ~~Hình 2.1 kiến trúc tổng thể~~ · 2.2 sơ đồ đấu nối · 2.3 hai tiến trình backend · 3.8→3.11 bốn màn hình Figma · 4.1 Swagger · 4.2→4.5 ảnh demo.
  ✅ **Hình 2.1 đã xong** (`docs/img/architecture.svg` → `.png`, xem §0.2i) — còn **11 khung**
- [ ] **Điền kết quả chương 4** của `BaoCao.md` sau khi chạy thử: cột "Kết quả thực tế" của 17 ca UAT + 8 ca API, bảng đo hiệu năng, mục 4.5 Đánh giá và 4.6 Kết luận
- [ ] **Dựng bản Word riêng** cho `02-UseCase.md`, `03-Sequence.md`, `04-Database.md`, `05-API.md` *(chỉ cần nếu GV yêu cầu nộp rời từng tài liệu — báo cáo tổng đã có)*
- [ ] 4 điểm cần đo lại khi có phần cứng ở tuần 2 — xem `04-Database.md` §14 (độ dài `request_id`, ngưỡng lux, tần suất ghi, trạng thái sau khi ESP reboot)
- [ ] ⚠️ **Phát hiện lúc lắp mạch (27/08/2026):** module quang trở LM393 đang có trong tay chỉ 3 chân **`VCC`, `GND`, `DO`** — **không có `AO`**. Toàn bộ thiết kế từ `04-Database.md` v2.0 trở đi (cột `room01_lux`, `min_value`/`max_value`, biểu đồ ánh sáng) giả định đọc được giá trị analog liên tục. **Quyết định tạm:** lắp `DO` vào chân `A0` để ráp/chạy thử phần cứng trước, sẽ mua module LM393 loại 4 chân (có `AO`) sau. Nếu cuối cùng không đổi được module, phải quay lại sửa `room01_lux` sang giá trị nhị phân (sáng/tối) ở cả `04-Database.md`, `05-API.md`, wireframe và báo cáo
- [ ] **Cân nhắc đồng bộ SRS §6 với schema thật** — sơ đồ ASCII trong `01-SRS.md` §6 hiện thiếu `device_type`, `is_active`, `error_message`. *Chưa sửa có chủ đích:* SRS là mô hình **mức khái niệm**, `04-Database.md` đã tuyên bố là bản có hiệu lực cho chi tiết vật lý. Chỉ sửa nếu muốn hai file khớp hoàn toàn
- [ ] **Vẽ lại sơ đồ ASCII thành ảnh** (kiến trúc hệ thống, wireframe, ERD) — hiện vẫn là khối code trong Word, nhìn không giống báo cáo chính quy
- [ ] Sau khi có ảnh: thêm caption `Hình n.` / `Bảng n.` → Word tự sinh **DANH MỤC HÌNH VẼ** và **DANH MỤC BẢNG BIỂU**
- [ ] Tách **TÀI LIỆU THAM KHẢO** thành mục riêng cuối bài (đang nằm ở mục 1.4)
- [ ] Đưa **DANH MỤC TỪ VIẾT TẮT** lên đầu theo mẫu (nội dung đã có ở mục 1.3)

### 0.4 Môi trường đã cài trên máy

```
Python 3.14 · Microsoft Word 16.0
pip: pypandoc-binary 1.17 (kèm sẵn Pandoc) · pywin32
Mosquitto 2.1.2 (cài 27/08/2026, sớm hơn kế hoạch — dùng ngay cho BTH2 §2.1)
```
PostgreSQL 18 (service `postgresql-x64-18`, DB `iot_room`) · Redis = container Docker `redis-dev`, dùng DB số 5 — §0.2o.
*(Node.js v24.14 + npm 11.11 **đã có sẵn** — kiểm ngày 14/09/2026, dùng cho `frontend/`.)*

> ⚠️ **Mosquitto cài trên Windows tự đăng ký thành Windows Service** (`Mosquitto Broker`, tên service `mosquitto`) và **tự chạy nền ngay sau khi cài**, chiếm sẵn cổng 1883. Gõ tay `mosquitto -v` để tự khởi động broker sẽ báo lỗi `Only one usage of each socket address…` vì đụng cổng với chính service đó — không phải lỗi cấu hình. Cứ dùng broker đang chạy sẵn (service), không cần tự bật.
>
> ⚠️ **Từ 14/09/2026 service nghe ở cổng `1884`** (§0.2n). Hệ quả ngược với ghi chú trên: gõ `mosquitto -v` giờ **không còn báo lỗi**, mà âm thầm dựng thêm một broker thứ hai ở 1883 **không đòi mật khẩu**; lệnh nào quên `-p 1884` sẽ lọt vào broker đó và "gửi thành công" mà mạch không nhận được gì.
>
> ⚠️ **Bẫy PowerShell khi gọi `mosquitto_pub -m '<json>'` — đã kiểm chứng bằng cách chạy thật, 2 lớp lỗi chồng nhau.**
> 1. PowerShell làm rớt mọi dấu `"` bên trong tham số truyền cho chương trình ngoài (native exe), kể cả khi bọc JSON bằng nháy đơn `'...'` hay thêm token `--%` để tắt phân tích cú pháp — broker nhận được `{a:b}` thay vì `{"a":"b"}`, JSON hỏng mà không có thông báo lỗi nào.
> 2. Né lỗi trên bằng cách ghi JSON ra file rồi dùng cờ `-f <file>` thay vì `-m` — nhưng nếu ghi file bằng `Out-File -Encoding utf8`, PowerShell tự chèn 3 byte BOM vô hình vào đầu file, bị gửi kèm vào message (hiện thành ký tự lạ `∩╗┐` trước dấu `{`), cũng làm JSON không hợp lệ.
> **Cách chạy đúng đã kiểm chứng:** `Out-File -FilePath payload.json -Encoding ascii -NoNewline` (không phải `utf8`) rồi `mosquitto_pub -f payload.json` (không phải `-m`). Payload mọi topic trong hệ thống này toàn ASCII nên `-Encoding ascii` không mất dữ liệu gì. Chi tiết + lệnh mẫu ở `docs/BTH2.md` §2.1.

> ⚠️ **Khi cài Django ở tuần 3 — kiểm tra phiên bản trước khi chạy `makemigrations`.**
> Tham số của `CheckConstraint` đổi tên giữa các bản: Django **≥ 5.1** dùng `condition=`, Django **≤ 5.0** dùng `check=`.
> Code `models.py` trong `04-Database.md` §8 viết theo **5.1**. Cài nhầm bản 5.0 thì báo lỗi `TypeError` ở cả 5 model.
>
> ⚠️ **Và trước lần `migrate` đầu tiên phải đặt `AUTH_USER_MODEL = "users.User"`** trong `settings.py` (§0.2k). Chạy `migrate` một lần rồi mới khai thì cách sửa duy nhất là `DROP DATABASE` làm lại.

---

### 0.6 Kho GitHub *(phiên 10 — 24/09/2026)*

<https://github.com/B23DCAT011/IOT> — nhánh `main`, lịch sử **21 commit chia theo từng phần**
(docs → tools → firmware → backend 5 commit → frontend 6 commit), không gộp một cục.

| Việc | Chi tiết |
|---|---|
| ⚠️ **Firmware nay cần `secrets.h`** | `WIFI_SSID/WIFI_PASS/MQTT_USER/MQTT_PASS` chuyển từ `.ino` sang `firmware/esp8266_room01/secrets.h`, file này **nằm trong `.gitignore`**. `.ino` chỉ còn `#include "secrets.h"`. Mất file đó thì **không biên dịch được** — chép `secrets.example.h` thành `secrets.h` rồi điền lại. Arduino IDE tự mở nó thành một tab cạnh sketch |
| Mật khẩu MQTT trong `docs/BTH2-huongdan-terminal-demo.md` | 21 chỗ đã thay bằng `<mat-khau>`. Chép lệnh từ tài liệu thì phải tự điền lại |
| Không commit | `backend/.env` · `.venv` · `node_modules` · `dist` · `build/` · `.claude/settings.local.json` · `secrets.h` · **12 ảnh `*.jpg` chụp bảng và 10 file payload `*.json` ở thư mục gốc** (bỏ ra ngày 24/09 cho trang đầu của kho gọn; vẫn còn trên máy, lệnh mẫu MQTT có đủ trong `docs/BTH2.md`) |
| Đã quét trước khi push | Dò từng giá trị bí mật thật trên **toàn bộ** commit: `SECRET_KEY`, `DB_PASSWORD`, `MQTT_PASSWORD`, `WIFI_PASS`, `MQTT_PASS` — sạch. Tên WiFi `Luu Duc Anh` và tài khoản `iotuser` vẫn còn trong tài liệu (SSID vốn phát công khai, còn `iotuser` chỉ là tên đăng nhập) |
| **Link trang Profile** | `LINK_GITHUB` = kho ở trên · `LINK_REPORT_PDF` = `.../blob/main/docs/BaoCao.pdf` (đã kiểm: HTTP 200, repo đang **public**) · `LINK_FIGMA` = `figma.com/design/2oR8lFM04tyK7kjpxGrILX/Untitled?node-id=0-1` (thêm 24/09; đã cắt đuôi `?p=f&t=…` vì đó là tham số phiên chia sẻ, hết hạn). ⚠️ **File Figma phải đặt quyền "Anyone with the link → can view"**, không thì thầy bấm vào bị chặn. Sửa link chỉ cần đổi `backend/.env` rồi khởi động lại daphne, **không đụng code**; nhớ sửa kèm `frontend/src/mocks/db.js` cho chế độ dữ liệu giả |
| `docs/BaoCao.pdf` | Xuất từ `BaoCao-moi .docx` bằng Word COM ở chế độ **chỉ đọc** (30 trang). Bản Word không bị đụng (`LastWriteTime` giữ nguyên 20/08). Chương 4 còn thiếu kết quả chạy thử ⇒ xuất lại đè lên file này khi xong, link không đổi |
| Lần sau thêm bí mật | Đừng gõ thẳng vào code. Backend: thêm biến vào `.env` + `.env.example`. Firmware: thêm vào `secrets.h` + `secrets.example.h` |

### 0.7 HTML cho Figma — `docs/figma-import/` *(phiên 10)*

Năm file `01-login · 02-dashboard · 03-data-sensor · 04-action-history · 05-profile` **trích
thẳng từ ứng dụng React đang chạy** (DOM + CSS thật, lấy qua Chrome DevTools Protocol), dùng cho
plugin **html.to.design**. Cách nhập ghi ở `docs/figma-import/README.md`.

> ⚠️ **`docs/wireframe/*.html` nay là bản lạc hậu** — vẽ tay từ phiên 5, còn 2 ô ngày, cột Thời
> gian để giờ trước, chưa có ô Dòng/trang, không có màn Login. Muốn ảnh khớp ứng dụng thì lấy
> từ `docs/figma-import/`.

Bốn chỗ phải xử lý khi trích (đều đã gặp thật, script trong scratchpad `figma.mjs`):
1. **Giá trị ô nhập nằm ở thuộc tính DOM, `outerHTML` chỉ chép attribute** ⇒ phải `setAttribute('value', el.value)` và gắn `selected` cho `<option>`, nếu không file tĩnh hiện ô rỗng và mọi select nhảy về lựa chọn đầu tiên (Dòng/trang hiện `8` trong khi bảng có 10 dòng).
2. **Tắt mọi vùng cuộn** (`overflow: visible`, bỏ `position: sticky`) và để `height: auto; min-height: 900px` — ghim cứng 900px thì Action History (cao ~960) bị dòng cuối đè lên thanh phân trang.
3. Xoá `data-vite-dev-id` — Vite nhét **đường dẫn tuyệt đối trên máy** vào từng thẻ `<style>`.
4. Xoá ô gợi ý tài khoản MSW ở màn Login bằng `[class*=mockHint]`; tìm theo chữ thì `__byText('div', …)` trả về thẻ bọc ngoài cùng và xoá nhầm cả khối đăng nhập.
5. **Dashboard phải dừng đồng hồ của dữ liệu giả trước khi chụp** (`for (let i=1;i<9999;i++) clearInterval(i)`): MSW đẩy chu kỳ mới mỗi 2 giây, chờ bố cục ổn định một nhịp là thẻ số lệch khỏi bộ mẫu §0.2f. Điều kiện chờ cũng phải là `.recharts-line`, không phải `svg path` — cái đó khớp nhầm icon ở sidebar nên trang bị chụp lúc còn "Đang tải…".
6. **Recharts `ResponsiveContainer` chỉ đo lại qua `ResizeObserver`** — `dispatchEvent(new Event('resize'))` vô tác dụng. Phải đổi kích thước thật một nhịp (`height: 899px` → `900px`), nếu không biểu đồ chỉ cao bằng nửa thẻ vì giữ nguyên kích thước đo lần đầu.

> ⚠️ **Heredoc `<<'EOF'` của Bash trên máy này vẫn nuốt dấu `\`** (đã dính 2 lần: đường dẫn Chrome và `'...
'` trong chuỗi JS). Viết script nhiều escape thì tạo file bằng Python, hoặc tránh escape (`String.fromCharCode(10)`).

### 0.5 Mở phiên mới thì bắt đầu từ đâu

1. Đọc file này (§0) — nắm trạng thái và các quyết định đã chốt.
2. **🔴 Việc gấp nhất hiện nay: đồng bộ mô hình dữ liệu v2.0** (§0.2k + §0.3 ưu tiên 1). Thứ tự: `01-SRS.md` → `02-UseCase.md` → `05-API.md` → `03-Sequence.md` → dữ liệu mẫu → bản vẽ → ảnh ERD → báo cáo. Đừng vẽ Figma trước khi chốt xong cột bảng mới, sẽ phải vẽ lại.
3. Sau đó mới quay lại lộ trình cũ: **Figma** (bước 1.6, §4) — wireframe 4 màn hình.
   Đầu vào đã sẵn sàng: sơ đồ ASCII 4 màn hình ở `01-SRS.md` §4.1 · tên cột bảng ở `02-UseCase.md` UC-03/UC-05 · **hình dạng dữ liệu thật ở `05-API.md` §4** (vẽ đúng những trường API trả về, không bịa thêm cột) · các trạng thái cần vẽ: công tắc đang khóa (BR-04), nhãn "Thiết bị ngoại tuyến" (BR-07), bảng rỗng, `PENDING`/`SUCCESS`/`FAILED`.
   **Đã có mockup `docs/wireframe.html`** — mở bằng trình duyệt, vẽ lại trong Figma theo đó; bảng màu và kích thước nằm ở cuối trang. **Sáu** trạng thái phụ đã dựng sẵn thành khung riêng ở `docs/wireframe/05-trang-thai.html`: ① công tắc khóa (BR-04) · ② thiết bị ngoại tuyến (BR-07) · ③ chưa có dữ liệu (UC-01 A1) · ④ bảng rỗng khi đang lọc (UC-04 A1) · ⑤ mất kết nối và lỗi tải, gồm cả dải "Timeout … FAILED" (UC-02 E1) · ⑥ **bảng đang áp bộ lọc mà có kết quả** (UC-04 luồng chính) — khung 6 thêm ở phiên 7 vì ba ghi chú "bổ sung ảnh" đặt trong bản Word cần đúng trạng thái này mà trước đó chưa có.

> ⚠️ **Muốn chụp toàn trang thì phải bỏ giới hạn chiều cao trước.** File dùng `height:100%` và cuộn bên trong (§0.2e), nên ảnh chụp headless chỉ thấy phần đầu. Cách làm: tạo bản tạm chèn thêm `<style>` ghi đè `.app{height:auto}` `.body{overflow:visible;height:auto}` rồi mới render. **Mọi con số trên bản vẽ lấy từ bộ dữ liệu mẫu chuẩn ở §0.2f — đừng bịa số mới.** Figma bản Starter nên **tuần 4 không nối được Dev Mode MCP**, sẽ sinh React từ ảnh chụp + đặc tả.
   Riêng màn hình **Data Sensor** nhớ vẽ đủ bộ lọc vừa chốt: dropdown chọn cột (nhiệt độ / độ ẩm / ánh sáng) + **2 ô nhập số** cho khoảng giá trị, đặt cạnh 2 ô chọn ngày. Dùng ô kiểu số để người dùng không gõ được chữ (UC-04 E1), và thêm chú thích nhỏ về việc bản ghi thiếu số đo bị loại khỏi kết quả.
3. Sau đó: đổi tên ảnh PNG cho nhất quán → dựng Word cho 4 tài liệu còn lại.

> **Tuần 1 đã xong toàn bộ 7 deliverable phân tích–thiết kế.** Việc còn lại của tuần 1 chỉ là Figma và khâu đóng gói (Word, ảnh).

---

## 1. Bối cảnh môn học

| Mục | Nội dung |
|---|---|
| Môn | IoT & Ứng dụng (PTIT) |
| Giảng viên | Nguyễn Quốc Uy — uynq@ptit.edu.vn — 0971479145 |
| Hình thức | Đồ án + báo cáo PDF + Figma + Postman/Swagger + UAT + live code |
| Nguồn yêu cầu | Ảnh chụp bảng `1.jpg` → `12.jpg`, ghi chú `in4.txt` |

### Vai trò GV yêu cầu sinh viên đóng (ảnh 1)
```
SA / BA  ──►  DB-Designer  ──►  Code, Test  ──►  UAT
              ├─ SRS
              ├─ Figma
              ├─ Flow / Sequence Diagram
              └─ API docs
```

### Cấu trúc báo cáo cuối kỳ (ảnh 5)
- **C1** — Tổng quan / Phần mở đầu
- **C2** — Thiết kế hệ thống (kiến trúc tổng thể HW + SW)
- **C3** — Thiết kế chi tiết: Use Case → Mô tả UC → Biểu đồ → Sequence → Figma → API
- **C4** — Kết quả thử nghiệm & Kết luận

---

## 2. Mô tả hệ thống (chốt)

Hệ thống IoT giám sát **nhiệt độ, độ ẩm, ánh sáng** của một căn phòng và **điều khiển bật/tắt thiết bị (đèn/quạt)** từ giao diện web.

### 2.1 Phần cứng (HW) — ảnh 2, 6, 7, 11

| Thành phần | Model | Chân | Ghi chú |
|---|---|---|---|
| Vi điều khiển | ESP8266 NodeMCU (hoặc ESP32) | — | 70–100k, có WiFi tích hợp |
| Cảm biến nhiệt độ + độ ẩm | DHT11 (hoặc DHT22) | VCC 3.3V, GND, Data → D4 | 25k |
| Cảm biến ánh sáng | Quang trở + module LM393 | VCC, GND, AO/DO → A0 | |
| Đèn 1 (LED) | LED + trở 220Ω | D5 | `pinMode(D5, OUTPUT)` |
| Đèn 2 (LED) | LED + trở 220Ω | D6 | HIGH = bật, LOW = tắt |
| Khác | Breadboard, dây nối | | |

> Mở rộng B2.2: nhiều thiết bị D1/D2/D3 điều khiển độc lập.

### 2.2 Phần mềm (SW) — ảnh 2, 7

```
┌─────────────┐                    ┌──────────────────────────────────┐
│   ESP8266   │                    │            LAPTOP                │
│  DHT11      │  WiFi              │  ┌──────────┐    ┌────────────┐  │
│  Quang trở  │ ◄────► MQTT ◄────► │  │  MQTT    │◄──►│  Backend   │  │
│  LED x2     │       1883         │  │ Mosquitto│    │  (API+WS)  │  │
└─────────────┘                    │  └──────────┘    └─────┬──────┘  │
                                   │                        │         │
                                   │  ┌──────────┐    ┌─────▼──────┐  │
                                   │  │ Frontend │◄──►│  Database  │  │
                                   │  │   Web    │HTTP│    SQL     │  │
                                   │  └──────────┘ WS └────────────┘  │
                                   └──────────────────────────────────┘
```

- **Broker:** Mosquitto cài local (`localhost:1883`). Dự phòng: cloud broker (HiveMQ / EMQX / CloudMQTT).
- **Giao thức:** MQTT (ESP ↔ Broker ↔ BE), HTTP REST + WebSocket (FE ↔ BE).

### 2.3 MQTT Topics (ảnh 8, 10) — CHỐT

| # | Topic | Hướng | Nội dung |
|---|---|---|---|
| 1 | `data_sensors` | ESP → Broker → BE (BE sub) | Số đo cảm biến định kỳ (2s/lần) |
| 2 | `device_control` | BE → Broker → ESP (ESP sub) | Lệnh bật/tắt thiết bị |
| 3 | `device_respond` | ESP → Broker → BE (BE sub) | Xác nhận thiết bị đã thực thi |

Lệnh test bằng CLI (GV ghi trên bảng):
```bash
mosquitto_sub -h localhost -p 1883 -t "data_sensors" -u <user> -P <pass>
mosquitto_pub -h localhost -p 1883 -t "data_sensors" -u <user> -P <pass> -m '{"temp":20,"hum":80}'
```

### 2.4 Luồng điều khiển thiết bị (ảnh 9) — Sequence chuẩn

```
User → FE : bấm nút toggle
FE   → BE : POST /api/devices/{id}/control   (HTTP)
BE   → DB : lưu action_history (status = PENDING)
BE   → MQTT : publish topic "device_control"
MQTT → HW : forward lệnh
HW   → HW : bật/tắt đèn (digitalWrite)
HW   → MQTT : publish topic "device_respond"
MQTT → BE : forward
BE   → DB : update action_history (status = SUCCESS)
BE   → FE : push qua WebSocket
FE   → User : hiển thị trạng thái mới
```

---

## 3. Use Case (B1 — ảnh 3, 4) — 6 UC

| ID | Tên | Mô tả ngắn |
|---|---|---|
| UC-01 | Xem Dashboard | 3 card số liệu (nhiệt độ / độ ẩm / ánh sáng) + biểu đồ realtime |
| UC-02 | Điều khiển thiết bị | Toggle bật/tắt đèn/quạt ngay trên Dashboard |
| UC-03 | Xem lịch sử Data Sensor | Bảng: id, nhiệt độ, độ ẩm, ánh sáng, thời gian |
| UC-04 | Tìm kiếm / Lọc / Sắp xếp / Phân trang | Áp dụng cho UC-03 và UC-05 |
| UC-05 | Xem Action History | Bảng: id, thiết bị, hành động, trạng thái, thời gian |
| UC-06 | Xem Profile | Thông tin SV + link GitHub, PDF báo cáo, Figma, Postman docs |

### Wireframe theo bảng (ảnh 3)
- **Dashboard:** sidebar trái · hàng 3 card `20°C` `80%` `100 lux` · biểu đồ đường (temp/hum theo thời gian) · panel bên phải với các toggle thiết bị (💡 đèn, 🌀 quạt).
- **Data Sensor:** sidebar · thanh tìm kiếm + dropdown lọc theo cột · bảng dữ liệu · phân trang góc dưới phải.
- **Action History:** sidebar · bảng (id, thiết bị, action, status, time) · tìm kiếm + phân trang.

---

## 4. Lộ trình (Roadmap)

### 🟩 Tuần 1 — Phân tích & Thiết kế (ĐANG LÀM)
| Bước | Deliverable | File | Trạng thái |
|---|---|---|---|
| 1.1 | **SRS** — đặc tả yêu cầu phần mềm | `docs/01-SRS.md` | ✅ **v0.4** |
| 1.2 | **Use Case Diagram** + đặc tả chi tiết từng UC | `docs/02-UseCase.md` | ✅ **v1.3** |
| 1.3 | **Sequence Diagram** (6 luồng) | `docs/03-Sequence.md` | ✅ **v1.2** |
| 1.4 | **Thiết kế CSDL** (ERD + DDL) | `docs/04-Database.md` | ✅ **v2.0** — 5 bảng (§0.2k) |
| 1.5 | **API Docs** (REST + WS + MQTT payload) | `docs/05-API.md` | ✅ **v2.1** — thêm đăng nhập bằng token (§0.2n) |
| 1.6 | **Figma** — wireframe 4 màn hình | `docs/wireframe.html` → Link Figma | 🟨 **mockup HTML xong, chờ vẽ lại trong Figma** |
| 1.7 | **Pipeline xuất Word** theo mẫu PTIT | `tools/` | ✅ **xong** (§5.4) |

> **Thứ tự đề xuất cho phiên sau:** Figma → đổi tên ảnh PNG → dựng Word.
> Chuỗi tài liệu 01→05 đã khép kín và nhất quán: schema chốt ở phiên 2, luồng thông điệp chốt ở phiên 3, hợp đồng giao tiếp chốt ở phiên 4. Figma chỉ việc vẽ đúng dữ liệu mà `05-API.md` §4 trả về.

### ⬜ Tuần 2 — Phần cứng (B2)
- Lắp mạch ESP8266 + DHT11 + quang trở + 2 LED trên breadboard
- Code Arduino: đọc cảm biến, kết nối WiFi, MQTT pub `data_sensors` / sub `device_control` / pub `device_respond`
- Test bằng `mosquitto_sub` / `mosquitto_pub` trên terminal
- B2.2: mở rộng nhiều thiết bị (D1, D2, D3) + nhiều terminal

### ✅ Tuần 3 — Backend (Django) + Database (PostgreSQL) — *xong 18/09/2026, xem §0.2o*
- Cài PostgreSQL + Redis + Mosquitto; khởi tạo project Django, cấu hình `.env`
- Viết models → `makemigrations` / `migrate`; seed 2 bản ghi bảng `devices`
- DRF: serializers, viewsets, filter/search/ordering/pagination cho UC-03/04/05
- Django Channels: `asgi.py`, consumer, routing; chạy bằng `daphne`
- Management command `mqtt_worker`: sub `data_sensors` + `device_respond`, ghi DB, `group_send` ra WebSocket
- API điều khiển: ghi `PENDING` → publish `device_control` → timeout 5s → `FAILED`
- Bật `drf-spectacular`, kiểm tra Swagger UI

### 🟨 Tuần 4 — Frontend (B3: UX/UI) — *khung 5 màn hình đã chạy với dữ liệu giả MSW (14/09/2026, §0.2n C)*
- Dựng 4 màn hình theo Figma, biểu đồ realtime, toggle, bảng + search + phân trang

### ⬜ Tuần 5 — Hoàn thiện (B4)
- Báo cáo PDF theo cấu trúc C1–C4
- Postman collection / Swagger UI
- UAT theo từng chức năng
- Chuẩn bị live code demo

---

## 5. Stack — ĐÃ CHỐT

| Lớp | Công nghệ | Ghi chú |
|---|---|---|
| Firmware | Arduino IDE (C++) — `DHT`, `ESP8266WiFi`, **`arduino-mqtt`** (lwmqtt) | ⚠️ **Không** dùng `PubSubClient` — xem §5.5 |
| Broker | Eclipse Mosquitto (local, Windows), port 1883 | GV nhắc trực tiếp trên bảng |
| **Backend** | **Django 5 + Django REST Framework** | ✅ chốt |
| **Realtime** | **Django Channels + Daphne (ASGI)** | WebSocket cho FE |
| **Channel layer** | **Redis** | Bắt buộc — xem §5.1 |
| **MQTT client** | **`paho-mqtt`** chạy trong management command riêng | Xem §5.1 |
| **Database** | **PostgreSQL 16** | ✅ chốt |
| ORM / migration | Django ORM + `makemigrations` / `migrate` | Sinh schema tự động |
| Frontend | React + Vite + Recharts + Axios | Biểu đồ realtime |
| API docs | **`drf-spectacular`** (Swagger UI / OpenAPI) + Postman Collection | B4 yêu cầu |
| Thiết kế UI | Figma | B1/B3 yêu cầu |

### 5.1 Điểm kiến trúc quan trọng của Django ⚠️

Django là framework **đồng bộ, request–response**. Nó không có sẵn vòng lặp nền để giữ kết nối MQTT. Vì vậy backend phải chạy **2 tiến trình song song**:

```
┌─────────────────────────────────────────────────────────────┐
│  Tiến trình 1:  daphne config.asgi:application              │
│  ├─ REST API (DRF)          ← FE gọi HTTP                   │
│  └─ WebSocket (Channels)    ← FE mở kết nối realtime        │
│                                    ▲                        │
│                                    │ group_send             │
│                              ┌─────┴─────┐                  │
│                              │   REDIS   │  channel layer   │
│                              └─────▲─────┘                  │
│                                    │ group_send             │
│  Tiến trình 2:  python manage.py mqtt_worker                │
│  ├─ paho-mqtt loop_forever()                                │
│  ├─ sub  data_sensors    → lưu DB → đẩy WS                  │
│  ├─ sub  device_respond  → update DB → đẩy WS               │
│  └─ pub  device_control  ← được gọi từ API view             │
└─────────────────────────────────────────────────────────────┘
```

**Vì sao bắt buộc có Redis:** MQTT worker và Daphne là **2 tiến trình khác nhau**. `InMemoryChannelLayer` chỉ hoạt động trong cùng một tiến trình → worker sẽ không đẩy được dữ liệu ra WebSocket. Redis là cầu nối giữa chúng.

**Publish lệnh từ API view:** view `POST /api/devices/{id}/control` nằm ở tiến trình 1, cần publish MQTT. Cách đơn giản và ổn định nhất: view tạo **một client paho ngắn hạn** (`connect → publish(qos=1) → disconnect`), không dùng chung client với worker. Chi phí ~vài ms, chấp nhận được ở quy mô đồ án và tránh hoàn toàn vấn đề chia sẻ socket giữa các tiến trình.

**Lệnh chạy hệ thống (3 terminal):**
```bash
# Terminal 1 — broker
mosquitto -c mosquitto.conf -v

# Terminal 2 — API + WebSocket
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Terminal 3 — MQTT worker
python manage.py mqtt_worker
```
> Redis chạy nền bằng Docker: `docker run -d -p 6379:6379 redis:7-alpine`

### 5.2 Cấu trúc thư mục backend Django

```
backend/
├── manage.py
├── .env                      # SECRET_KEY, DB, MQTT, REDIS
├── requirements.txt
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py               # định tuyến HTTP + WebSocket
└── apps/
    ├── sensors/              # model SensorData + API
    │   ├── models.py
    │   ├── serializers.py
    │   ├── views.py
    │   └── filters.py        # search / filter / sort
    ├── devices/              # model Device, ActionHistory + API điều khiển
    │   ├── models.py
    │   ├── serializers.py
    │   ├── views.py
    │   └── mqtt_publisher.py
    ├── realtime/
    │   ├── consumers.py      # WebSocket consumer
    │   └── routing.py
    └── mqtt/
        └── management/commands/
            └── mqtt_worker.py   # tiến trình 2
```

### 5.3 `requirements.txt` dự kiến
```
Django>=5.0
djangorestframework
django-filter
django-cors-headers
drf-spectacular
channels
channels-redis
daphne
psycopg[binary]
paho-mqtt
python-decouple
```

---

## 5.4 Xuất tài liệu ra Word theo mẫu PTIT

Mẫu chuẩn: `docs/MauBaoCao.docx`. Quy trình 2 bước:

```bash
python tools/build_body.py docs/01-SRS.md        # Markdown -> build/body.docx
python tools/assemble.py "SRS" docs/01-SRS.docx  # ghép bìa + mục lục + thân bài
```

| Script | Việc |
|---|---|
| `tools/build_body.py` | Bỏ phần đầu file `.md`, đổi `## N.` → `# CHƯƠNG N.`, nâng bậc các heading còn lại, gọi Pandoc với `--reference-doc` để thừa hưởng font/lề/style của mẫu |
| `tools/assemble.py` | Mở mẫu, giữ trang bìa, xoá phần sau, thay chữ trên bìa, chèn **trường MỤC LỤC thật của Word**, chèn thân bài, đánh số trang, cập nhật mục lục |

**Tham số của `assemble.py`:** `assemble.py "<tiêu đề trên bìa>" <file .docx đầu ra> ["<nhãn phía trên tiêu đề>"]`
Nhãn mặc định là `TÀI LIỆU`. Ví dụ dựng báo cáo tổng:
```bash
python tools/build_body.py docs/BaoCao.md
python tools/assemble.py "HỆ THỐNG GIÁM SÁT VÀ ĐIỀU KHIỂN MÔI TRƯỜNG PHÒNG DỰA TRÊN IOT" docs/BaoCao.docx "ĐỀ TÀI"
```

**Sửa thông tin trang bìa:** biến `COVER_FIXED` ở đầu `tools/assemble.py` (MSSV, họ tên, GV, học kỳ, mã học phần).

**Ảnh trong Markdown:** viết đường dẫn tương đối từ gốc dự án — `![Chú thích](docs/img/erd.png){ width=90% }`. Hàm `fix_image_paths()` trong `build_body.py` tự đổi sang đường dẫn tuyệt đối trước khi gọi Pandoc, vì Pandoc chạy với thư mục làm việc là `build/`.

**Bốn cái bẫy đã xử lý, đừng sửa lại:**
- `Find.Execute` phải truyền **tham số theo vị trí**. COM late-binding của pywin32 bỏ qua tham số đặt tên → thay chữ trên bìa im lặng không chạy.
- Đoạn tiêu đề "MỤC LỤC" phải ép về style Normal (`rng.Style = -1`) + `OutlineLevel = 10`, không thì chính nó tự lọt vào bảng mục lục.
- *(phiên 6)* **`sys.stdout` phải ép về UTF-8 ngay đầu file.** Console Windows mặc định là cp1252, nên chính lệnh `print` báo tiến độ (có chữ tiếng Việt) ném `UnicodeEncodeError` và giết script **giữa chừng khi Word đang mở tài liệu** — hỏng cả lần chạy sau.
- *(phiên 6)* ⚠️ **Mở file mẫu ở chế độ CHỈ ĐỌC** — `Documents.Open(TEMPLATE, False, True, False)`, tham số theo vị trí. Mở ghi thì Word tạo file khóa `~$auBaoCao.docx` cạnh file mẫu; nếu tiến trình Word chết bất thường (bị kill, treo), file khóa **ở lại**, và lần chạy sau Word bật hộp thoại *"file đang được mở"* — hộp thoại này **vô hình** vì `Visible=False`, nên script **treo vô thời hạn thay vì báo lỗi**. Phiên 6 mất 15 phút vì đúng lỗi này.
- *(phiên 6)* **Khi build treo, việc đầu tiên phải kiểm tra là file khóa:** `ls -a docs/ | grep '~\$'`. Có thì xoá, đóng hết tiến trình `WINWORD` **không có cửa sổ** (đó là instance tự động hoá, không phải Word của người dùng — phân biệt bằng `MainWindowTitle` rỗng), rồi chạy lại.
- *(phiên 6)* **Luôn bọc lệnh dựng trong `timeout`**, ví dụ `timeout 240 python tools/assemble.py …`. Không có nó thì lệnh treo chiếm trọn 7 phút timeout mặc định mà không rõ nguyên nhân.
- *(phiên 6)* **Dùng `DispatchEx` chứ không phải `Dispatch`.** `Dispatch` bám vào instance Word đang chạy; nếu instance đó còn kẹt từ lần crash trước thì `Documents.Open()` trả về đối tượng không phân giải được, báo lỗi khó hiểu `AttributeError: Open.Paragraphs`. `DispatchEx` luôn tạo tiến trình Word riêng.

**Phụ thuộc:** `pip install pypandoc-binary pywin32` + Microsoft Word đã cài.

---

## 5.5 ⚠️ Thư viện MQTT cho firmware: dùng `arduino-mqtt`, KHÔNG dùng `PubSubClient`

Chốt ở phiên 6. Đã **tra tài liệu chính thức của cả hai thư viện** để xác nhận, không nói từ trí nhớ:

| | `PubSubClient` (knolleary) | **`arduino-mqtt` (256dpi)** ✅ |
|---|---|---|
| **Publish** | **chỉ QoS 0** | QoS 0, 1, 2 |
| Subscribe | QoS 0, 1 | QoS 0, 1, 2 |
| Bộ đệm mặc định | 256 byte | **128 byte** |
| Cài trong Library Manager | tìm `PubSubClient` | tìm bằng từ khoá **`lwmqtt`** |

**Lý do đổi.** Thiết kế chốt `device_respond` dùng **QoS 1** (§2.3), mà `PubSubClient` **không publish được QoS 1** — hàm `publish()` của nó không có tham số QoS. Giữ `PubSubClient` thì phải chọn một trong hai điều tệ: hạ QoS của `device_respond` xuống 0 rồi sửa lại 4 tài liệu, hoặc để tài liệu ghi một đằng còn code chạy một nẻo. Đổi thư viện lúc firmware **chưa viết dòng nào** thì gần như miễn phí — đây là lý do quyết định.

**Hai điều bắt buộc nhớ khi code tuần 2:**

1. **Khai bộ đệm tường minh:** `MQTTClient client(256);` — mặc định chỉ 128 byte, mà payload `device_control` đã khoảng 110 byte. Sát nút tới mức chỉ cần đổi tên thiết bị dài thêm vài ký tự là tràn. Đây là điểm **kém hơn** `PubSubClient` (mặc định 256), dễ quên vì bản cũ không cần khai.
2. **Thêm `delay(10);` ngay sau `client.loop();`** — tài liệu của thư viện ghi rõ trên ESP8266 việc này khắc phục nhiều lỗi mất ổn định.

Cú pháp publish có QoS: `client.publish(topic, payload, retained, qos)` — tham số `retained` để `false` (§0.2d: không dùng retain ở cả 3 topic).

**Đánh đổi đã chấp nhận:** `PubSubClient` phổ biến hơn hẳn nên ví dụ và bài hướng dẫn trên mạng cũng nhiều hơn. Gặp sự cố sát deadline thì tìm lời giải cho `arduino-mqtt` sẽ vất vả hơn. Nếu tuần 2 thấy quá chật vật, phương án lùi là quay lại `PubSubClient` **và** hạ QoS của `device_respond` xuống 0 — nhưng phải sửa mục 2.3.2 của báo cáo cho khớp, đừng để lệch.

**Đã sửa theo quyết định này ở 5 chỗ:** `BaoCao.md` §1.6 · `CLAUDE.md` §5 (bảng stack) · `01-SRS.md` §4.3 · `04-Database.md` §14 điểm 1 · `05-API.md` §6.3.

---

## 6. Quy ước

- **Ngôn ngữ tài liệu:** Tiếng Việt (thuật ngữ kỹ thuật giữ nguyên tiếng Anh).
- **Đặt tên:** `snake_case` cho DB, MQTT topic và Python; `camelCase` cho JS; `PascalCase` cho Django model và React component.
- **API response:** giữ `snake_case` (mặc định của DRF) để FE và BE thống nhất, không đổi sang camelCase.
- **Mã UC:** `UC-XX` · **Yêu cầu chức năng:** `FR-XX` · **Phi chức năng:** `NFR-XX`.
- **Thư mục:**
  ```
  IOT/
  ├── CLAUDE.md              ← file này
  ├── in4.txt
  ├── *.jpg                  ← ảnh bảng gốc
  ├── docs/
  │   ├── MauBaoCao.docx     ← mẫu báo cáo PTIT (dùng làm reference-doc)
  │   ├── 01-SRS.md          ✅ v0.4
  │   ├── 01-SRS.docx        ← 23 trang, dựng lại phiên 6
  │   ├── 02-UseCase.md      ✅ v1.3
  │   ├── 03-Sequence.md     ✅ v1.2
  │   ├── 04-Database.md     ✅ v2.0 ← 5 bảng; 4 file kia CHƯA theo kịp (§0.2k)
  │   ├── 05-API.md          ✅ v1.3
  │   ├── BaoCao.md          ← BÁO CÁO TỔNG (bản rút gọn, 4 chương)
  │   ├── BaoCao.docx        ← BẢN NGƯỜI DÙNG CHỈNH TAY — KHÔNG ghi đè (§0.2h)
  │   ├── BaoCao-moi.docx    ← 48 trang, bản sinh mới nhất, TỰ CHỨA (§0.2j)
  │   ├── img/architecture.svg  ← nguồn vector Hình 2.1 (§0.2i)
  │   ├── wireframe.html     ← bản thuyết minh 4 màn hình (đã xuất bản artifact)
  │   ├── wireframe/         ← 5 file rời để nhập Figma (01→04 + 05-trang-thai)
  │   └── img/               ← 8 ảnh sơ đồ (tên chưa nhất quán, xem §0.3)
  ├── tools/
  │   ├── build_body.py      ← Markdown → thân bài
  │   └── assemble.py        ← ghép bìa + mục lục
  ├── build/                 ← file trung gian, không cần commit
  ├── firmware/              ← code Arduino (tuần 2)
  ├── backend/               ← Django — xem backend/README.md, backend/PLAN.md
  └── frontend/              ← React + Vite, chạy được với MSW (xem frontend/README.md)
  ```

---

## 7. Điểm còn cần chốt

- [x] Có cần đăng nhập / phân quyền không? → ~~Chốt phiên 7: có bảng người dùng, CHƯA có màn hình đăng nhập~~ → **Chốt lại phiên 8: CÓ màn hình đăng nhập**, token của DRF, bảo vệ toàn bộ 4 màn hình; `POST .../control` bỏ `user_id`, lấy người thao tác từ token (§0.2n, `05-API.md` v2.1). **Phân quyền theo vai trò vẫn chưa làm** — `role` chỉ mang tính mô tả
- [ ] Thiết bị điều khiển: 2 LED hay LED + quạt? (**mặc định: 2 LED, đặt tên logic là "Đèn" và "Quạt"**)
- [ ] Chu kỳ gửi dữ liệu cảm biến: **mặc định 2 giây**
- [ ] Broker: local Mosquitto hay cloud? (**mặc định: local, có cấu hình chuyển cloud**)
- [ ] Làm thêm mobile App (ảnh 2 có vẽ) hay chỉ Web? (**mặc định: chỉ Web**)
