# Hướng dẫn demo MQTT qua terminal — BTH2 mục 2.1 (có mật khẩu)

> Cập nhật: 14/09/2026
> Chạy trên: PowerShell (Windows), broker Mosquitto local, `localhost:1884`
> Tài khoản đang dùng: **user `iotuser`** / **mật khẩu `<mat-khau>`**
> *(nếu đã đổi mật khẩu thì sửa lại mọi lệnh `-P` bên dưới cho khớp)*
> Muốn **đổi port** (ví dụ 1883 → 1884) hoặc **đổi tài khoản/mật khẩu**: xem **Phần 3** và **Phần 4** cuối file.
> ✅ **Broker đã chuyển sang port `1884` từ 14/09/2026** và mọi lệnh trong file đã theo port mới. Tiến độ từng bước xem bảng đầu **Phần 3**.

Mục đích: mở nhiều cửa sổ PowerShell cùng lúc, dán từng khối lệnh vào đúng cửa sổ tương ứng, là demo được đủ 3 topic + xác thực.

---

## Bước 0 — Khởi động broker *(chỉ làm nếu đang TẮT, cần quyền Admin)*

Mở PowerShell **"Run as Administrator"**, chạy:

```powershell
Start-Service mosquitto
Get-Service mosquitto
```

Phải thấy `Status = Running` rồi mới làm tiếp các bước dưới. Nếu đã `Running` sẵn thì bỏ qua bước này.

---

## Bước 1 — Mở 3 cửa sổ subscribe (mỗi cửa sổ 1 topic, để chạy nền)

Mở 3 cửa sổ PowerShell **thường** (không cần Admin), mỗi cửa sổ dán đúng 1 dòng dưới đây, để nó chạy liên tục suốt buổi demo.

**Cửa sổ 1 — theo dõi topic `data_sensors`:**
```powershell
mosquitto_sub -h localhost -p 1884 -t "data_sensors" -u iotuser -P <mat-khau>
```

**Cửa sổ 2 — theo dõi topic `device_control`:**
```powershell
mosquitto_sub -h localhost -p 1884 -t "device_control" -u iotuser -P <mat-khau>
```

**Cửa sổ 3 — theo dõi topic `device_respond`:**
```powershell
mosquitto_sub -h localhost -p 1884 -t "device_respond" -u iotuser -P <mat-khau>
```

### Cách gọn hơn khi demo — chỉ cần 1 cửa sổ

Ba cửa sổ ở trên hợp lý khi cần chỉ rõ từng topic đi riêng đường. Nếu muốn nhanh, dùng
một trong hai lệnh dưới đây, cả hai đều in kèm **giờ nhận** nhờ cờ `-F`.

**Chỉ nghe phản hồi của mạch** (`device_respond`) — dùng khi demo bật/tắt đèn quạt ở mục 2.5:

```powershell
mosquitto_sub -h localhost -p 1884 -t "device_respond" -F "%I | %t | %p" -u iotuser -P <mat-khau>
```

**Nghe cả 3 topic trong cùng một cửa sổ** — ký tự `#` nghĩa là mọi topic:

```powershell
mosquitto_sub -h localhost -p 1884 -t "#" -F "%I | %t | %p" -u iotuser -P <mat-khau>
```

Mỗi dòng in ra có dạng *giờ | tên topic | nội dung*, ví dụ:

```
2026-09-09T21:41:17+0700 | device_respond | {"request_id":"test-001","device":"room01_lamp","state":"ON","status":"SUCCESS"}
```

Có tên topic ngay trên mỗi dòng nên vẫn phân biệt được lệnh đi và phản hồi về, mà không
phải nhìn qua lại giữa nhiều cửa sổ. Nhược điểm là `data_sensors` đổ về 2 giây một dòng
sẽ đẩy phản hồi trôi lên nhanh, nên khi cần soi kỹ phản hồi thì dùng lệnh thứ nhất.

Dừng cửa sổ nghe bằng `Ctrl + C`.

---

## Bước 2 — Cửa sổ 4: gửi (publish) lần lượt cả 3 topic

Mở thêm 1 cửa sổ PowerShell nữa (Cửa sổ 4). Trước tiên `cd` vào thư mục dự án:

```powershell
cd "C:\Users\Admin\Desktop\Tai lieu ki 7\IOT"
```

### 2.1 — Giả lập HW gửi số liệu cảm biến (`data_sensors`)

```powershell
'{"device_id":"esp8266_room01","temperature":28.5,"humidity":72.0,"light":350}' | Out-File -FilePath payload.json -Encoding ascii -NoNewline
mosquitto_pub -h localhost -p 1884 -t "data_sensors" -f payload.json -u iotuser -P <mat-khau>
```

→ Xem **Cửa sổ 1**: phải hiện đúng JSON vừa gửi.

### 2.2 — Giả lập Backend gửi lệnh điều khiển (`device_control`)

```powershell
'{"request_id":"test-001","device":"room01_lamp","action":"ON"}' | Out-File -FilePath control.json -Encoding ascii -NoNewline
mosquitto_pub -h localhost -p 1884 -t "device_control" -f control.json -u iotuser -P <mat-khau>
```

→ Xem **Cửa sổ 2**.

### 2.3 — Giả lập thiết bị phản hồi đã thực thi (`device_respond`)

```powershell
'{"request_id":"test-001","device":"room01_lamp","state":"ON","status":"SUCCESS"}' | Out-File -FilePath respond.json -Encoding ascii -NoNewline
mosquitto_pub -h localhost -p 1884 -t "device_respond" -f respond.json -u iotuser -P <mat-khau>
```

→ Xem **Cửa sổ 3**.

### 2.4 *(Tuỳ chọn)* — Cửa sổ 5: thêm 1 nơi điều khiển thứ 2 (`ter2`)

Minh hoạ "nhiều đầu điều khiển không xung đột":

```powershell
'{"request_id":"test-002","device":"room01_fan","action":"ON"}' | Out-File -FilePath control2.json -Encoding ascii -NoNewline
mosquitto_pub -h localhost -p 1884 -t "device_control" -f control2.json -u iotuser -P <mat-khau>
```

→ Xem **Cửa sổ 2**: thấy cả 2 lệnh (`room01_lamp` và `room01_fan`) đều tới mà không đụng nhau, nhờ có trường `device` + `request_id` riêng của từng lệnh.

### 2.5 — Bật/tắt **thật** đèn và quạt trên mạch *(đã chạy được ngày 09/09/2026)*

Khác với 2.2–2.4 ở trên vốn chỉ là giả lập giữa các cửa sổ terminal, bốn lệnh dưới đây
điều khiển trực tiếp 2 LED cắm trên breadboard.

Điều kiện: mạch đang cắm điện, đã nạp `firmware/esp8266_room01/esp8266_room01.ino`,
và **Cửa sổ 1 đang thấy `data_sensors` chạy đều 2 giây một lần** — đó là dấu hiệu mạch
đã vào được WiFi và đăng nhập broker thành công.

**Bật đèn** — `room01_lamp`, LED ở chân D5:

```powershell
'{"request_id":"lamp-on","device":"room01_lamp","action":"ON"}' | Out-File -FilePath lamp-on.json -Encoding ascii -NoNewline
mosquitto_pub -h localhost -p 1884 -t "device_control" -q 1 -f lamp-on.json -u iotuser -P <mat-khau>
```

**Tắt đèn:**

```powershell
'{"request_id":"lamp-off","device":"room01_lamp","action":"OFF"}' | Out-File -FilePath lamp-off.json -Encoding ascii -NoNewline
mosquitto_pub -h localhost -p 1884 -t "device_control" -q 1 -f lamp-off.json -u iotuser -P <mat-khau>
```

**Bật quạt** — `room01_fan`, LED ở chân D6:

```powershell
'{"request_id":"fan-on","device":"room01_fan","action":"ON"}' | Out-File -FilePath fan-on.json -Encoding ascii -NoNewline
mosquitto_pub -h localhost -p 1884 -t "device_control" -q 1 -f fan-on.json -u iotuser -P <mat-khau>
```

**Tắt quạt:**

```powershell
'{"request_id":"fan-off","device":"room01_fan","action":"OFF"}' | Out-File -FilePath fan-off.json -Encoding ascii -NoNewline
mosquitto_pub -h localhost -p 1884 -t "device_control" -q 1 -f fan-off.json -u iotuser -P <mat-khau>
```

Mỗi lệnh phải cho **hai** kết quả quan sát được, nói ra khi demo cho thầy:

1. LED tương ứng sáng lên hoặc tắt đi ngay lập tức trên breadboard.
2. **Cửa sổ 3** hiện dòng phản hồi do chính mạch tự gửi lại, ví dụ với lệnh bật đèn:

```
{"request_id":"lamp-on","device":"room01_lamp","state":"ON","status":"SUCCESS"}
```

Trường `request_id` trong phản hồi trùng đúng với `request_id` của lệnh vừa gửi. Đây là
cách backend biết phản hồi này ứng với bản ghi `action_history` nào (BR-06).

> ⚠️ **Nếu LED sáng nhưng Cửa sổ 3 không có gì:** kiểm tra `-q 1`. Firmware gửi
> `device_respond` ở QoS 1, còn cửa sổ subscribe mở ở QoS 0 vẫn nhận được, nên trường hợp
> này gần như chắc chắn là mạch đã mất kết nối broker ngay sau khi bật LED.
>
> ⚠️ **Nếu không có gì xảy ra cả:** xem lại Cửa sổ 1 còn chạy `data_sensors` không.
> Mạch mất WiFi thì nó im lặng hoàn toàn, không báo lỗi ra terminal.

---

## Bước 3 — Chứng minh xác thực có hiệu lực *(phòng khi thầy hỏi)*

Thử gửi **không kèm** `-u/-P` để xem bị từ chối:

```powershell
mosquitto_pub -h localhost -p 1884 -t "data_sensors" -m "test"
```

Kết quả mong đợi: báo lỗi kiểu `Connection Refused: not authorised.` và message **không** tới được Cửa sổ 1 — chứng minh broker đang thực sự yêu cầu đăng nhập, không phải chỉ ghi trên giấy.

---

## Phần 2 — Lệnh quản lý user / mật khẩu *(phòng khi bị hỏi vào việc này)*

Công cụ dùng: `"C:\Program Files\mosquitto\mosquitto_passwd.exe"`
File lưu mật khẩu (đã băm, không lưu dạng chữ thường): `"C:\Program Files\mosquitto\passwd"`

> ⚠️ **Lưu ý chung:** mọi lệnh sửa file trong `C:\Program Files\mosquitto\` (đổi mật khẩu, thêm/xoá user, sửa conf) đều cần PowerShell **"Run as Administrator"**. Sau khi sửa xong **phải** `Restart-Service mosquitto` thì thay đổi mới có hiệu lực.

**Xem danh sách user hiện có** *(không có lệnh liệt kê riêng, đọc trực tiếp cột đầu tiên của file)*:

```powershell
Get-Content "C:\Program Files\mosquitto\passwd" | ForEach-Object { ($_ -split ':')[0] }
```

**Đổi mật khẩu user đã có** (ví dụ đổi mật khẩu của `iotuser`) — *cần Admin*:

```powershell
& "C:\Program Files\mosquitto\mosquitto_passwd.exe" -b "C:\Program Files\mosquitto\passwd" iotuser MatKhauMoi456
Restart-Service mosquitto
```

**Thêm user mới** (ví dụ: `giangvien` / `MatKhauGV789`) — *cần Admin*:

```powershell
& "C:\Program Files\mosquitto\mosquitto_passwd.exe" -b "C:\Program Files\mosquitto\passwd" giangvien MatKhauGV789
Restart-Service mosquitto
```

> ⚠️ **Tuyệt đối không dùng cờ `-c` khi thêm user thứ 2 trở đi!** Cờ `-c` nghĩa là "tạo file mới", dùng lại sẽ **xoá sạch** toàn bộ user cũ đang có trong file (mất luôn `iotuser`).

**Xoá 1 user** (ví dụ xoá `giangvien`) — *cần Admin*:

```powershell
& "C:\Program Files\mosquitto\mosquitto_passwd.exe" -D "C:\Program Files\mosquitto\passwd" giangvien
Restart-Service mosquitto
```

**Tắt hẳn xác thực, quay lại chế độ mở (anonymous)** nếu cần — *cần Admin*:

Mở `C:\Program Files\mosquitto\mosquitto.conf`, sửa dòng `allow_anonymous false` thành `allow_anonymous true` và xoá/comment dòng `password_file ...`, rồi:

```powershell
Restart-Service mosquitto
```

---

## Phần 3 — Đổi port MQTT (ví dụ 1883 → 1884)

Đổi port gồm **4 chỗ**. Sót chỗ nào thì chỗ đó mất kết nối, và thường **không có thông báo lỗi rõ ràng**:

| # | Chỗ phải sửa | Nếu quên |
|---|---|---|
| 1 | File cấu hình broker `mosquitto.conf` | Broker vẫn nghe ở 1883 |
| 2 | Tường lửa Windows (mở cổng mới) | Lệnh trên chính laptop vẫn chạy, nhưng **mạch ESP8266 không vào được broker**. Dễ tưởng là lỗi code |
| 3 | Firmware `esp8266_room01.ino` dòng `MQTT_PORT`, rồi nạp lại | Mạch lặp mãi ở bước kết nối MQTT |
| 4 | Mọi lệnh `-p 1883` trong file này và `docs/BTH2.md` *(sau này thêm `.env` của backend)* | `mosquitto_sub`/`pub` báo không kết nối được |

**Tiến độ lần đổi 1883 → 1884 (14/09/2026):**

| Việc | Trạng thái |
|---|---|
| Sửa `mosquitto.conf` + khởi động lại broker | ✅ Đã kiểm tra: `netstat` thấy `0.0.0.0:1884 LISTENING`, không còn 1883 |
| Xác thực trên port mới | ✅ Có `-u/-P` gửi được; không có thì bị từ chối `not authorised` |
| Luật tường lửa `Mosquitto MQTT 1884` | ✅ Đã tạo |
| Xoá luật cũ `Mosquitto MQTT 1883` | ⬜ Chưa xoá (không ảnh hưởng gì, chỉ để cho gọn) |
| Sửa lệnh trong file này + `docs/BTH2.md` | ✅ |
| Sửa `MQTT_PORT = 1884` trong firmware | ✅ |
| Sửa `MQTT_HOST` theo IP hiện tại + nạp lại mạch | ⬜ **Chưa làm** — xem Bước 4 |

> Mọi lệnh ở Bước 1 → Bước 3 dưới đây chạy trong PowerShell **"Run as Administrator"**.

### Bước 1 — Sao lưu rồi sửa `mosquitto.conf`

> **Sửa tay bằng Notepad là đủ.** Lệnh `Copy-Item` tạo file `.bak` chỉ để có bản sao lưu phòng khi sửa hỏng, **không bắt buộc**. Điều bắt buộc duy nhất: Notepad phải được **mở từ cửa sổ Admin** (lệnh `notepad ...` bên dưới). Mở Notepad bình thường thì lúc lưu, Windows không cho ghi vào `C:\Program Files` và hiện hộp thoại *Save As* — bấm lưu ra chỗ khác thì broker không đọc được.

```powershell
Copy-Item "C:\Program Files\mosquitto\mosquitto.conf" "C:\Program Files\mosquitto\mosquitto.conf.bak"
notepad "C:\Program Files\mosquitto\mosquitto.conf"
```

Trong Notepad bấm `Ctrl + End` để xuống **cuối file**. Ba dòng cấu hình đang có hiệu lực nằm ở cuối (khoảng dòng 1126):

```
listener 1883 0.0.0.0
allow_anonymous false
password_file C:\Program Files\mosquitto\passwd
```

Chỉ sửa dòng đầu thành:

```
listener 1884 0.0.0.0
```

Lưu (`Ctrl + S`) rồi đóng Notepad.

> ⚠️ **Chỉ sửa đúng dòng ở cuối file.** Phần giữa file có các dòng `# listener 1883` và `# listener 1884` (khoảng dòng 321, 325). Đó là **chú thích mẫu** (có dấu `#` đầu dòng), không có tác dụng gì. Sửa nhầm vào đó thì broker vẫn chạy 1883.
>
> ⚠️ **Giữ nguyên `0.0.0.0`.** Bỏ nó đi hoặc đổi thành `localhost` thì broker chỉ nhận kết nối từ chính laptop, còn mạch ESP8266 (kết nối qua WiFi) sẽ bị chặn.

Kiểm tra lại đã sửa đúng chưa:

```powershell
Select-String -Path "C:\Program Files\mosquitto\mosquitto.conf" -Pattern '^listener'
```

Kết quả phải là **đúng 1 dòng** `listener 1884 0.0.0.0`, không có dấu `#` phía trước.

**Tùy chọn — chạy song song cả hai port trong lúc chuyển đổi.** Nếu muốn mạch ESP cũ (còn nạp firmware port 1883) vẫn chạy trong lúc chưa kịp nạp lại, thì **thêm** một dòng thay vì sửa:

```
listener 1883 0.0.0.0
listener 1884 0.0.0.0
allow_anonymous false
password_file C:\Program Files\mosquitto\passwd
```

Nạp firmware mới xong thì quay lại xoá dòng `listener 1883`. Sau khi khởi động lại, **nhớ chạy lại kiểm tra ở Bước 5 cho cả hai port** để chắc cả hai đều đang đòi mật khẩu.

### Bước 2 — Mở cổng 1884 trên tường lửa Windows

Máy đang có sẵn luật `Mosquitto MQTT 1883`, loại mạng **Private**, chỉ cho phép cổng 1883. Cổng mới cần một luật riêng:

```powershell
New-NetFirewallRule -DisplayName "Mosquitto MQTT 1884" -Direction Inbound -Protocol TCP -LocalPort 1884 -Action Allow -Profile Private
```

Không dùng 1883 nữa (sau khi đã bỏ hẳn, không chạy song song) thì xoá luật cũ cho gọn:

```powershell
Remove-NetFirewallRule -DisplayName "Mosquitto MQTT 1883"
```

> Vì sao chỉ bị ở mạch ESP mà lệnh trên laptop vẫn chạy: `mosquitto_sub -h localhost` kết nối nội bộ trong máy nên **không đi qua tường lửa**. Chỉ kết nối từ thiết bị khác (ESP8266 qua WiFi) mới bị chặn. Vì vậy quên bước này thì terminal thử vẫn thấy ổn, tới lúc cắm mạch mới lộ ra.

**Mạng Private hay Public?** Luật ở trên chỉ áp dụng cho mạng loại **Private**. Xem mạng đang dùng thuộc loại nào:

```powershell
Get-NetConnectionProfile
```

Nếu dòng `NetworkCategory` là **`Public`** (ví dụ mạng trường `PTIT_WIFI 6` đang là Public), cổng 1884 **vẫn thông**, vì máy có sẵn 2 luật tên `mosquitto` loại Public cho phép chương trình `mosquitto.exe` dùng **mọi cổng** (TCP và UDP). Hai luật này do Windows tạo lúc Mosquitto chạy lần đầu.

> ⚠️ **Đừng xoá hai luật tên `mosquitto`**, vì chúng đang giữ cho broker hoạt động được trên mạng Public. Chỉ xoá luật `Mosquitto MQTT 1883`.
>
> Kiểm tra lại cả 4 luật: `Get-NetFirewallRule -DisplayName "mosquitto*" | Select-Object DisplayName, Enabled, Profile`

### Bước 3 — Khởi động lại broker và kiểm tra

```powershell
Restart-Service mosquitto
Get-Service mosquitto
netstat -ano | Select-String ':188[34]\s'
```

Kỳ vọng: `Status = Running`, và `netstat` hiện `0.0.0.0:1884 ... LISTENING` (không còn dòng 1883, trừ khi đang chạy song song).

> ⚠️ **Broker chỉ đọc `mosquitto.conf` một lần, lúc khởi động.** Thứ tự bắt buộc là **sửa → lưu → `Restart-Service`**. Khởi động lại trước khi lưu thì broker vẫn đọc bản cũ, và phải khởi động lại thêm lần nữa.

**Nếu `netstat` vẫn hiện `1883`** (đã gặp thật ngày 14/09/2026): file cấu hình chưa được lưu, hoặc broker được khởi động lại trước khi lưu. Kiểm tra nội dung file:

```powershell
Select-String -Path "C:\Program Files\mosquitto\mosquitto.conf" -Pattern '^listener'
```

- Vẫn là `listener 1883`: file chưa lưu được. Quay lại Bước 1, nhớ mở Notepad từ cửa sổ Admin.
- Đã là `listener 1884`: chỉ cần chạy lại `Restart-Service mosquitto`.

**Nếu service không lên được (`Stopped`)**, thường là do gõ sai file cấu hình. Chạy tay broker để xem nó báo lỗi gì:

```powershell
Stop-Service mosquitto
& "C:\Program Files\mosquitto\mosquitto.exe" -c "C:\Program Files\mosquitto\mosquitto.conf" -v
```

Đọc lỗi xong thì bấm `Ctrl + C`, sửa lại file (hoặc khôi phục bản sao lưu bằng lệnh dưới), rồi `Start-Service mosquitto`.

```powershell
Copy-Item "C:\Program Files\mosquitto\mosquitto.conf.bak" "C:\Program Files\mosquitto\mosquitto.conf" -Force
```

### Bước 4 — Sửa firmware và nạp lại mạch

Mở `firmware/esp8266_room01/esp8266_room01.ino`, sửa **dòng 29**:

```cpp
const int   MQTT_PORT = 1884;
```

Nạp lại vào NodeMCU. Mở Serial Monitor (115200), phải thấy qua được dòng `Dang ket noi MQTT broker ...`. Nếu mạch cứ in dấu chấm mãi ở dòng đó, xem lại Bước 2 (tường lửa).

### Bước 5 — Sửa các lệnh terminal và thử lại

Đổi toàn bộ `-p 1883` thành `-p 1884` trong file này và `docs/BTH2.md` (trong VS Code: `Ctrl + H`, thay tất cả). Xem còn sót chỗ nào bằng lệnh sau, chạy ở thư mục dự án:

```powershell
Select-String -Path docs\*.md, firmware\esp8266_room01\*.ino -Pattern '1883'
```

Thử nghe trên port mới (có mật khẩu phải nhận được, không có mật khẩu phải bị từ chối):

```powershell
mosquitto_sub -h localhost -p 1884 -t "#" -F "%I | %t | %p" -u iotuser -P <mat-khau>
mosquitto_pub -h localhost -p 1884 -t "data_sensors" -m "test"
```

Lệnh thứ hai (không có mật khẩu) phải báo đúng như sau. Đây là thông báo thật đã chạy ngày 14/09/2026:

```
Connection error: Connection Refused: not authorised
Error: The connection was refused
```

> ⚠️ **Lệnh thiếu `-p` sẽ tự dùng 1883**, vì 1883 là cổng mặc định của mọi công cụ MQTT. Sau khi đổi port, lệnh nào quên `-p 1884` đều báo không kết nối được. Đây là lỗi thường gặp nhất khi demo.

---

## Phần 4 — Đổi tài khoản / mật khẩu MQTT

Lệnh đổi mật khẩu, thêm và xoá user đã có ở **Phần 2**. Phần này là **quy trình đầy đủ** để đổi mà không làm đứt kết nối, vì tài khoản không chỉ nằm trong broker mà còn nằm trong firmware.

Tài khoản đang được dùng ở **3 chỗ**:

| # | Chỗ | Nội dung hiện tại |
|---|---|---|
| 1 | File mật khẩu của broker `C:\Program Files\mosquitto\passwd` | `iotuser` (mật khẩu đã băm) |
| 2 | Firmware `esp8266_room01.ino` dòng 30–31 | `MQTT_USER = "iotuser"`, `MQTT_PASS = "<mat-khau>"` |
| 3 | Mọi lệnh `-u ... -P ...` trong file này | `-u iotuser -P <mat-khau>` |

### Cách A — Chỉ đổi mật khẩu, giữ tên `iotuser`

1. *(Admin)* Đổi mật khẩu trong broker:
   ```powershell
   & "C:\Program Files\mosquitto\mosquitto_passwd.exe" -b "C:\Program Files\mosquitto\passwd" iotuser MatKhauMoi456
   Restart-Service mosquitto
   ```
2. Sửa firmware dòng 31 thành `const char* MQTT_PASS = "MatKhauMoi456";` rồi nạp lại mạch.
3. Đổi mọi `-P <mat-khau>` trong file này thành `-P MatKhauMoi456` (`Ctrl + H`).
4. Đóng hết các cửa sổ `mosquitto_sub` cũ và mở lại bằng mật khẩu mới. `Restart-Service` đã ngắt mọi kết nối cũ.

> Từ lúc làm bước 1 tới lúc nạp xong bước 2, mạch **không vào được broker**. Không làm việc này ngay trước giờ demo.

### Cách B — Đổi sang tài khoản mới, không bị gián đoạn

Tạo tài khoản mới **song song**, chuyển dần từng chỗ sang, cuối cùng mới xoá tài khoản cũ. Ví dụ tài khoản mới `esp_room01` / `MatKhauMoi456`:

1. *(Admin)* Thêm tài khoản mới. **Không** dùng cờ `-c`, dùng là mất `iotuser` (xem Phần 2):
   ```powershell
   & "C:\Program Files\mosquitto\mosquitto_passwd.exe" -b "C:\Program Files\mosquitto\passwd" esp_room01 MatKhauMoi456
   Restart-Service mosquitto
   ```
   Lúc này **cả hai** tài khoản đều đăng nhập được, mạch đang chạy với `iotuser` vẫn kết nối lại bình thường.
2. Sửa firmware dòng 30–31:
   ```cpp
   const char* MQTT_USER = "esp_room01";
   const char* MQTT_PASS = "MatKhauMoi456";
   ```
   Nạp lại, xem Serial Monitor in `Dang ket noi MQTT broker voi tai khoan "esp_room01"` và qua được bước đó.
3. Đổi mọi `-u iotuser -P <mat-khau>` trong file này thành tài khoản mới.
4. Mọi chỗ đều chạy ổn rồi mới *(Admin)* xoá tài khoản cũ:
   ```powershell
   & "C:\Program Files\mosquitto\mosquitto_passwd.exe" -D "C:\Program Files\mosquitto\passwd" iotuser
   Restart-Service mosquitto
   ```

### Kiểm tra sau khi đổi

```powershell
# Tài khoản MỚI: phải kết nối được và nhận dữ liệu
mosquitto_sub -h localhost -p 1884 -t "#" -u esp_room01 -P MatKhauMoi456

# Tài khoản/mật khẩu CŨ: phải bị từ chối "not authorised"
mosquitto_sub -h localhost -p 1884 -t "#" -u iotuser -P <mat-khau>
```

### Lưu ý khi chọn mật khẩu và tên đăng nhập

- **Chỉ dùng chữ cái và chữ số.** Ký tự đặc biệt gây lỗi ở cả hai phía:
  - PowerShell: `$` bị hiểu là biến, dấu `` ` `` là ký tự thoát. Mật khẩu `Abc$123` sẽ bị gửi đi thành `Abc`. Nếu buộc phải dùng thì bọc nháy đơn: `-P 'Abc$123'`.
  - Firmware (C++): dấu `"` và `\` trong chuỗi phải viết thành `\"` và `\\`.
- Tên đăng nhập **không được chứa dấu `:`**, vì file `passwd` dùng `:` để ngăn cách tên và mật khẩu.
- ⚠️ Mật khẩu đang nằm dạng **chữ thường** trong file `.ino` và file hướng dẫn này. Khi đưa code lên GitHub (link nằm ở trang Profile), đổi mật khẩu thật thành chữ giả như `YOUR_MQTT_PASSWORD` trước khi push.

---

## Ghi chú

- Broker Mosquitto chạy dưới dạng Windows Service tên `mosquitto`, tự khởi động cùng máy (`StartType = Automatic`) trừ khi bị tắt tay.
- **Không** dùng `mosquitto -v` để tự khởi động broker riêng. Broker thật là service `mosquitto`, hiện nghe ở **1884**.
  ⚠️ **Hồi còn dùng 1883, lệnh này báo lỗi trùng cổng nên không gây hại. Từ khi đổi sang 1884 thì nó chạy được mà không báo lỗi gì** (cổng 1883 đã trống), và dựng lên một broker **thứ hai**: nghe ở 1883, **không đòi mật khẩu**. Lệnh nào quên `-p 1884` sẽ lọt vào broker giả này và "gửi thành công", nhưng mạch và backend không bao giờ nhận được. Vẫn giữ nguyên quy tắc: không tự chạy `mosquitto -v`.
- Nếu quên `-u/-P`: lệnh sẽ không kết nối được tới broker, báo `Connection Refused: not authorised`.
- Tài khoản `iotuser` / `<mat-khau>` là tài khoản demo tạo ngày 03/09/2026. Nếu đổi mật khẩu thì phải sửa lại **tất cả** lệnh `-P` ở Bước 1, 2, 3 bên trên cho khớp, không thì các cửa sổ subscribe cũ sẽ mất kết nối (phải đóng mở lại với mật khẩu mới).
- Các file `payload.json`, `control.json`, `respond.json`, `control2.json`, `lamp-on.json`, `lamp-off.json`, `fan-on.json`, `fan-off.json` được tạo trong thư mục dự án (chỗ `cd` ở Bước 2). Có thể xoá sau khi demo xong, không ảnh hưởng gì tới broker.
