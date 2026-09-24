# Hướng dẫn lắp ráp phần cứng — Hệ thống giám sát & điều khiển phòng

> Áp dụng đúng theo linh kiện và sơ đồ chân đã chốt ở `CLAUDE.md` §2.1.
> Đọc hết checklist §4 **trước khi** cắm dây cấp nguồn (USB) lần đầu.

---

## 0. Danh sách linh kiện cần có

| # | Linh kiện | Số lượng | Ghi chú |
|---|---|---|---|
| 1 | ESP8266 NodeMCU | 1 | Board chính |
| 2 | Cảm biến nhiệt độ + độ ẩm DHT11 | 1 | Loại module 3 chân (đã có sẵn điện trở kéo lên) |
| 3 | Module quang trở + LM393 | 1 | ⚠️ Loại thực tế trong tay chỉ có **3 chân (VCC, GND, DO)** — không có `AO`. Xem lưu ý ở §2 |
| 4 | LED | 2 | 1 làm "Đèn phòng" (`room01_lamp`), 1 làm "Quạt trần" (`room01_fan`) |
| 5 | Điện trở 220Ω | 2 | Nối tiếp mỗi LED, vạch màu đỏ–đỏ–nâu |
| 6 | Breadboard | 1 | |
| 7 | Dây nối (đực–đực, đực–cái) | ~10–12 sợi | |

---

## 1. Sơ đồ chân tổng hợp

| Thiết bị | Chân trên module | Nối vào NodeMCU | GPIO thật | Ghi chú |
|---|---|---|---|---|
| DHT11 | VCC | 3V3 | — | **Không** nối vào `Vin`/5V |
| DHT11 | GND | GND | — | |
| DHT11 | Data (out/S) | **D4** | GPIO2 | ⚠️ xem lưu ý §2 |
| LM393 (quang trở) | VCC | 3V3 | — | **Không** nối vào `Vin`/5V |
| LM393 | GND | GND | — | |
| LM393 | DO (digital out) | **A0** | ADC0 | ⚠️ Module trong tay không có `AO`, tạm nối `DO` vào A0 để chạy được phần cứng — chỉ đọc được 2 mức (gần 0 / gần 1023), không phải giá trị lux liên tục. Xem `CLAUDE.md` §0.3 |
| LED "Đèn phòng" | Anode (chân dài) → qua trở 220Ω | **D5** | GPIO14 | `digitalWrite(D5, HIGH)` = bật |
| LED "Đèn phòng" | Cathode (chân ngắn) | GND | — | |
| LED "Quạt trần" | Anode (chân dài) → qua trở 220Ω | **D6** | GPIO12 | `digitalWrite(D6, HIGH)` = bật |
| LED "Quạt trần" | Cathode (chân ngắn) | GND | — | |

> Sơ đồ chân đầy đủ của board (D0–D8 ứng với GPIO số mấy, chân nào cấp 3.3V):
> đây là link về **sơ đồ chân (pinout) tổng thể của ESP8266 NodeMCU**
> https://randomnerdtutorials.com/esp8266-pinout-reference-gpios/

---

## 2. ⚠️ Lưu ý riêng cho từng chân — đọc trước khi đấu

- **D4 (GPIO2) là chân "strapping pin" lúc khởi động** — board yêu cầu chân này ở mức HIGH trong lúc boot, và trên nhiều bo NodeMCU nó còn nối sẵn với LED xanh onboard (LED này sáng ở mức LOW). DHT11 loại module 3 chân đã có điện trở kéo lên sẵn nên đường Data mặc định nằm ở mức HIGH → **tương thích tốt**, không cần đổi chân. Nếu sau này đổi sang DHT11 loại 4 chân trần (không có điện trở kéo lên tích hợp) thì phải tự thêm điện trở 10kΩ giữa VCC và Data.
- **D5 (GPIO14) và D6 (GPIO12) là hai chân "an toàn"**, không có ràng buộc lúc boot, dùng làm ngõ ra điều khiển LED/relay là hợp lý.
- **A0 chỉ có một kênh ADC duy nhất trên ESP8266**, dải điện áp vào 0–3.3V (bo NodeMCU đã có sẵn cầu phân áp nội bộ) — module LM393 cấp nguồn 3.3V thì ngõ ra nằm đúng trong dải này, không cần thêm gì.
- ⚠️ **Module LM393 đang dùng chỉ có `DO`, không có `AO`.** Nối tạm `DO` vào A0 vẫn đọc được (chỉ ra giá trị gần 0 hoặc gần 1023, không có mức trung gian) — đủ để test mạch/code chạy thông, chưa đủ để lấy giá trị lux thật. Phương án lâu dài: đổi sang module LM393 loại 4 chân (có `AO`), hoặc dùng quang trở rời + điện trở 10kΩ tự làm cầu phân áp vào A0. Xem `CLAUDE.md` §0.3.
- **Cả DHT11 và LM393 đều cấp nguồn 3.3V (chân `3V3`), không dùng chân `Vin`/5V** — cấp 5V vào module ngoại vi 3.3V có thể làm hỏng cảm biến hoặc đọc sai giá trị analog trên A0.

Chi tiết cách đấu dây DHT11 (kèm hình): đây là link về **cách đấu dây cảm biến nhiệt độ + độ ẩm DHT11 vào ESP8266**
https://lastminuteengineers.com/esp8266-dht11-dht22-web-server-tutorial/

Chi tiết cách đấu module quang trở LM393 (kèm hình): đây là link về **cách đấu module cảm biến ánh sáng (quang trở + LM393) vào ESP8266**
https://newbiely.com/tutorials/esp8266/esp8266-light-sensor

---

## 3. Các bước lắp ráp trên breadboard

1. **Cắm NodeMCU lên breadboard**, hai bên chân board mỗi bên nằm trên một nửa breadboard (để hai hàng lỗ đối diện nhau không bị board che).
2. **Nối nguồn ra hai đường rail của breadboard:**
   - NodeMCU `3V3` → rail dương (+).
   - NodeMCU `GND` → rail âm (−).
3. **Cắm DHT11:**
   - Chân `VCC` → rail dương (+).
   - Chân `GND` → rail âm (−).
   - Chân `Data`/`OUT`/`S` → dây nối thẳng vào **D4** trên NodeMCU.
4. **Cắm module LM393 (quang trở):**
   - Chân `VCC` → rail dương (+).
   - Chân `GND` → rail âm (−).
   - Chân `DO` → dây nối thẳng vào **A0** trên NodeMCU (module này không có `AO`, xem lưu ý §2).
5. **Cắm LED "Đèn phòng" (`room01_lamp`):**
   - Cắm LED lên breadboard, chân dài (anode) và chân ngắn (cathode) ở hai hàng lỗ khác nhau.
   - Nối một điện trở 220Ω từ chân dài (anode) sang một dây dẫn tới **D5**.
   - Nối chân ngắn (cathode) thẳng vào rail âm (−) / GND.
6. **Cắm LED "Quạt trần" (`room01_fan`):** lặp lại y hệt bước 5, nhưng dây tín hiệu nối vào **D6** thay vì D5.
7. **Soi lại toàn bộ dây một lượt theo bảng ở §1** trước khi làm checklist §4.

---

## 4. ⚠️ Checklist bắt buộc — kiểm tra trước khi cắm USB cấp nguồn

- [ ] Không có hai chân nào của cùng một linh kiện vô tình cắm chung một hàng lỗ breadboard (gây chập).
- [ ] `VCC` của DHT11 và LM393 đều nối vào `3V3`, **không** nối nhầm vào `Vin`.
- [ ] Dây Data của DHT11 cắm đúng **D4** — dễ nhầm với D5/D6 vì tên đều dạng "D-số".
- [ ] Mỗi LED đều có điện trở 220Ω nối tiếp — **không** cắm LED thẳng vào chân GPIO mà thiếu trở (dòng quá dòng cho phép của chân, có thể hỏng GPIO).
- [ ] Cực LED đúng chiều: chân dài (anode) về phía GPIO qua trở, chân ngắn (cathode) về GND. Cắm ngược thì LED chỉ không sáng chứ không hỏng gì (vì có trở hạn dòng), nhưng nên sửa lại cho đúng thiết kế.
- [ ] Rail dương và rail âm của breadboard không bị nối tắt với nhau bằng dây thừa.
- [ ] Đã rút mọi que đo/dây thử nghiệm không cần thiết ra khỏi breadboard.

Cắm USB xong mà đèn nguồn trên NodeMCU **không** sáng → rút ra ngay, kiểm tra lại rail dương/âm có bị chập không, đừng để cắm lâu.

---

## 5. Kiểm tra từng phần trước khi ghép chung (khuyến nghị làm theo đúng thứ tự)

Việc cài Arduino IDE + board ESP8266 làm trước tiên: đây là link về **cách cài board ESP8266 vào Arduino IDE**
https://randomnerdtutorials.com/how-to-install-esp8266-board-arduino-ide/

1. **Test 2 LED riêng** — nạp sketch `Blink` đơn giản trên D5 rồi D6 (đổi `LED_BUILTIN` thành `D5`/`D6`), xác nhận đúng đèn nào chớp đúng chân đó.
2. **Test DHT11** — cài thư viện Adafruit rồi mở ví dụ đọc nhiệt độ/độ ẩm có sẵn, xem Serial Monitor có ra số hợp lý (nhiệt độ phòng ~25–32 °C) không.
   Thư viện dùng: đây là link về **thư viện Adafruit đọc cảm biến DHT11 cho Arduino IDE**
   https://github.com/adafruit/DHT-sensor-library
3. **Test quang trở** — nạp sketch chỉ có `Serial.println(analogRead(A0));` trong `loop()`, lấy tay che rồi bỏ tay ra khỏi cảm biến. Vì module chỉ có `DO`, số đọc được sẽ **nhảy giữa 2 mức** (gần 0 / gần 1023) chứ không tăng giảm dần — đúng như dự kiến, không phải lỗi. Ghi lại mức nào ứng với tối/sáng để dùng tạm.
4. Cả 3 test đều ổn thì mới ghép chạy đồng thời trên cùng một sketch.

---

## 6. Bước tiếp theo (ngoài phạm vi lắp ráp cơ khí, để làm khi viết code tuần 2)

Việc đấu dây đến đây là xong. Hai việc kế tiếp theo roadmap (`CLAUDE.md` §4 — Tuần 2) là **cài thư viện MQTT** và **cài + chạy thử broker Mosquitto**, chưa cần làm ngay nhưng để sẵn link ở đây cho lúc cần:

- đây là link về **thư viện MQTT đã chốt dùng cho firmware** (`arduino-mqtt`/lwmqtt — KHÔNG dùng `PubSubClient`, lý do ở `CLAUDE.md` §5.5)
  https://github.com/256dpi/arduino-mqtt
- đây là link về **cách cài đặt MQTT broker Mosquitto trên Windows**
  https://www.cedalo.com/blog/how-to-install-mosquitto-mqtt-broker-on-windows

---

## 7. Toàn bộ link tham khảo (gom lại để tra nhanh)

| Link | Nội dung |
|---|---|
| https://randomnerdtutorials.com/esp8266-pinout-reference-gpios/ | Sơ đồ chân (pinout) tổng thể ESP8266 NodeMCU |
| https://lastminuteengineers.com/esp8266-dht11-dht22-web-server-tutorial/ | Cách đấu dây DHT11 vào ESP8266 |
| https://newbiely.com/tutorials/esp8266/esp8266-light-sensor | Cách đấu module quang trở LM393 vào ESP8266 |
| https://randomnerdtutorials.com/how-to-install-esp8266-board-arduino-ide/ | Cách cài board ESP8266 vào Arduino IDE |
| https://github.com/adafruit/DHT-sensor-library | Thư viện Adafruit đọc cảm biến DHT11 |
| https://github.com/256dpi/arduino-mqtt | Thư viện MQTT `arduino-mqtt` (đã chốt dùng, xem §5.5) |
| https://www.cedalo.com/blog/how-to-install-mosquitto-mqtt-broker-on-windows | Cài đặt MQTT broker Mosquitto trên Windows |

> Các link đã tra cứu ngày 27/08/2026, chưa mở từng trang để xác nhận nội dung chi tiết —
> nếu mở lên thấy link chết hoặc lệch nội dung, báo lại để thay link khác.
> File `firmware/link-tham-khao-lap-rap.txt` là bản danh sách link thô dựng trước bản này,
> giữ lại làm bản dự phòng — bản `.md` này là bản đầy đủ, dùng để tra cứu chính.
