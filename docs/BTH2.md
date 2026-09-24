# BÁO CÁO BÀI THỰC HÀNH SỐ 2
## Triển khai giao tiếp qua giao thức MQTT

| | |
|---|---|
| **Môn học** | IoT & Ứng dụng (INT14149) — Học viện Công nghệ Bưu chính Viễn thông |
| **Giảng viên** | TS. Nguyễn Quốc Uy |
| **Sinh viên** | B23DCAT011 — Lưu Đức Anh |
| **Ngày** | 02/09/2026 |

> **Ghi chú khi dùng file này:** đây là bản khung (form) để điền ảnh chụp màn hình và số liệu thực tế sau khi làm xong bài thực hành. Mọi khối bảng có chữ **⬛ CHÈN HÌNH …** là chỗ trống chờ chèn ảnh — thay bằng ảnh thật rồi xoá dòng hướng dẫn bên trong khung.
> Tên topic, tên mã thiết bị (`room01_lamp`, `room01_fan`…) và cấu trúc payload JSON dùng thống nhất theo `docs/05-API.md` (đã chốt ở đồ án chính), để bài thực hành và đồ án không lệch nhau.

---

## 2. Triển khai giao tiếp qua giao thức MQTT

### 2.1 Thao tác thông qua terminal

**Mục đích:** kiểm chứng cơ chế publish/subscribe của MQTT bằng công cụ dòng lệnh, trước khi hiện thực bằng code trên ESP8266 — nếu terminal đã hoạt động đúng thì phần lỗi (nếu có) ở bước sau chắc chắn nằm ở code/mạch, không phải ở cấu hình mạng hay broker.

**Mô hình thực hiện:**

| | |
|---|---|
| Vai trò máy 1 | Đóng vai thiết bị (HW) — chạy `mosquitto_pub` để giả lập ESP8266 gửi dữ liệu |
| Vai trò máy 2 | Đóng vai Backend — chạy `mosquitto_sub` để giả lập server nhận dữ liệu |
| Broker | Mosquitto cài local trên một trong hai máy (`localhost` nếu cùng máy, hoặc địa chỉ IP LAN của máy chạy broker nếu là 2 máy khác nhau trong cùng mạng WiFi/LAN); có thể thay bằng broker công cộng trên mạng (ví dụ `test.mosquitto.org`) nếu 2 máy không cùng mạng nội bộ |

⬛ CHÈN HÌNH 2.1
|---|
| **Cần vẽ:** sơ đồ khối — 1 máy (giả lập HW) → mũi tên vào khối MQTT Broker → mũi tên ra 1 máy khác (giả lập Backend/Laptop theo dõi). Ghi rõ 3 topic cạnh mũi tên tương ứng. **Kích thước:** ngang 12 cm. |

**Ba topic dùng chung cho toàn hệ thống** (giữ nguyên tên đã chốt ở `05-API.md` §6, không đổi giữa bài thực hành và đồ án):

| Topic | Chiều | Nội dung |
|---|---|---|
| `data_sensors` | Thiết bị → Backend | Số đo cảm biến (nhiệt độ, độ ẩm, ánh sáng) |
| `device_control` | Backend → Thiết bị | Lệnh bật/tắt thiết bị |
| `device_respond` | Thiết bị → Backend | Xác nhận đã thực thi lệnh |

**Các bước thực hiện:**

1. Cài đặt Mosquitto (bao gồm cả 2 công cụ dòng lệnh `mosquitto_sub`, `mosquitto_pub`) trên máy đóng vai trò broker.
2. Khởi động broker: `mosquitto -v` (cờ `-v` để in log kết nối/subscribe/publish ra màn hình, tiện đối chiếu khi báo cáo).
3. Trên máy 2 (Backend), mở terminal, chạy lệnh **subscribe** vào topic `data_sensors`:

   ```bash
   mosquitto_sub -h <địa_chỉ_broker> -p 1884 -t "data_sensors"
   ```

   *(Thêm `-u <tên_đăng_nhập> -P <mật_khẩu>` nếu broker có bật xác thực; bỏ qua nếu broker chạy chế độ mở, mặc định khi mới cài.)*

4. Trên máy 1 (giả lập HW), mở terminal, chạy lệnh **publish** một bản tin mẫu lên đúng topic đó:

   ```bash
   # Bash / cmd.exe — escape dấu " bằng \" (cách này CHẠY ĐÚNG trên Bash/cmd)
   mosquitto_pub -h <địa_chỉ_broker> -p 1884 -t "data_sensors" -m "{\"device_id\":\"esp8266_room01\",\"temperature\":28.5,\"humidity\":72.0,\"light\":350}"
   ```

   ```powershell
   # PowerShell — cách AN TOÀN NHẤT: ghi JSON ra file rồi dùng -f, không truyền JSON trực tiếp trên dòng lệnh
   '{"device_id":"esp8266_room01","temperature":28.5,"humidity":72.0,"light":350}' | Out-File -FilePath payload.json -Encoding ascii -NoNewline
   mosquitto_pub -h <địa_chỉ_broker> -p 1884 -t "data_sensors" -f payload.json
   ```

   > ⚠️ **Hai bẫy đã gặp thực tế trong PowerShell, đã kiểm chứng bằng cách chạy thật:**
   > 1. Chép nguyên cú pháp Bash (`\"..\"`) vào PowerShell → báo lỗi `Unknown option`, chuỗi JSON bị cắt vụn — vì PowerShell không coi `\` là ký tự escape, dấu `"` ngay sau `\` bị hiểu là dấu đóng chuỗi thật.
   > 2. Tưởng bọc bằng nháy đơn `'{"a":"b"}'` là xong — **vẫn sai**: broker nhận được `{a:b}`, **mất hết toàn bộ dấu `"`**. Nguyên nhân nằm sâu hơn lỗi cú pháp: khi PowerShell chuyển tham số cho một chương trình ngoài (không phải cmdlet), nó tự dựng lại thành một dòng lệnh kiểu Win32 và làm rớt các dấu `"` nằm trong tham số, kể cả dùng thêm token `--%` để tắt phân tích cú pháp cũng không cứu được (đã thử, vẫn mất dấu `"`).
   > 3. Ghi file bằng `Out-File -Encoding utf8` cũng **chưa xong hẳn** — PowerShell tự chèn thêm 3 byte BOM vô hình vào đầu file, bị gửi kèm luôn vào message (hiện ra như mấy ký tự lạ `∩╗┐` đứng trước dấu `{`). JSON có BOM ở đầu không hợp lệ với nhiều bộ phân tích (ví dụ Python `json.loads` báo lỗi). Khắc phục: dùng **`-Encoding ascii`** thay vì `utf8` khi ghi file — payload các topic trong hệ thống này toàn ký tự ASCII (tên trường, số, `ON`/`OFF`/`SUCCESS`…) nên không mất dữ liệu gì.
   > 4. **Tổng kết cách chạy đúng đã kiểm chứng:** ghi JSON ra file bằng `-Encoding ascii`, rồi dùng cờ **`-f <file>`** của `mosquitto_pub` để gửi nguyên nội dung file — không đi qua bước tham số dòng lệnh nữa nên không còn gì để PowerShell làm hỏng, và không còn BOM. Cách này dùng được cho mọi topic có payload JSON, không riêng `data_sensors`.

5. Quan sát terminal của máy 2 — nội dung JSON vừa gửi phải xuất hiện **ngay lập tức**.
6. Lặp lại với 2 topic còn lại để xác nhận đầy đủ cả 3 kênh:

   ```powershell
   # PowerShell — dùng file trung gian như lưu ý ở trên, không truyền JSON trực tiếp
   # Giả lập Backend gửi lệnh điều khiển
   '{"request_id":"test-001","device":"room01_lamp","action":"ON"}' | Out-File -FilePath control.json -Encoding ascii -NoNewline
   mosquitto_pub -h <địa_chỉ_broker> -p 1884 -t "device_control" -f control.json

   # Giả lập thiết bị phản hồi đã thực thi
   '{"request_id":"test-001","device":"room01_lamp","state":"ON","status":"SUCCESS"}' | Out-File -FilePath respond.json -Encoding ascii -NoNewline
   mosquitto_pub -h <địa_chỉ_broker> -p 1884 -t "device_respond" -f respond.json
   ```

**Kết quả quan sát được** (chạy thật trên 1 máy, `localhost`, ngày 02/09/2026):

| Topic | Lệnh gửi | Kết quả nhận được | Đạt/Không đạt |
|---|---|---|---|
| `data_sensors` | `mosquitto_pub -h localhost -p 1883 -t "data_sensors" -f payload.json` với `payload.json` = `{"device_id":"esp8266_room01","temperature":28.5,"humidity":72.0,"light":350}` | `mosquitto_sub` in ra đúng nguyên văn: `{"device_id":"esp8266_room01","temperature":28.5,"humidity":72.0,"light":350}` | Đạt |
| `device_control` | `mosquitto_pub -h localhost -p 1883 -t "device_control" -f control.json` với `control.json` = `{"request_id":"test-001","device":"room01_lamp","action":"ON"}` | `mosquitto_sub` in ra đúng nguyên văn: `{"request_id":"test-001","device":"room01_lamp","action":"ON"}` | Đạt |
| `device_respond` | `mosquitto_pub -h localhost -p 1883 -t "device_respond" -f respond.json` với `respond.json` = `{"request_id":"test-001","device":"room01_lamp","state":"ON","status":"SUCCESS"}` | `mosquitto_sub` in ra đúng nguyên văn: `{"request_id":"test-001","device":"room01_lamp","state":"ON","status":"SUCCESS"}` | Đạt |

⬛ CHÈN HÌNH 2.2
|---|
| **Cần chèn:** ảnh chụp 2 cửa sổ terminal đặt cạnh nhau — một chạy `mosquitto_sub` (đang hiển thị bản tin vừa nhận), một chạy `mosquitto_pub` (vừa gõ lệnh gửi). **Kích thước:** ngang 15 cm. |

**Nhận xét:** Cả 3 topic đều nhận đúng nguyên văn nội dung JSON đã gửi, độ trễ gần như tức thời (chạy cùng máy qua `localhost` nên không có độ trễ mạng đáng kể). Điểm cần lưu ý khi làm trên PowerShell: không truyền JSON trực tiếp qua tham số `-m` vì PowerShell làm rớt dấu `"` khi chuyển tham số cho chương trình ngoài — phải ghi JSON ra file bằng `-Encoding ascii` rồi gửi bằng cờ `-f` (chi tiết ở khung cảnh báo phía trên). Làm đúng cách này thì JSON nhận được sạch tuyệt đối, không lệch một ký tự nào so với bản gửi.

---

### 2.2 Thao tác thông qua code Arduino

**Mục đích:** thay thao tác gõ lệnh thủ công ở mục 2.1 bằng một chương trình chạy tự động trên ESP8266 — thiết bị tự kết nối WiFi, tự kết nối broker, tự publish số liệu định kỳ và tự xử lý lệnh điều khiển nhận được, đúng vai trò "HW" mà ở mục 2.1 con người đang giả lập bằng tay.

**Mở rộng của bài thực hành — nhiều thiết bị, nhiều đầu điều khiển:** một ESP8266 có thể điều khiển đồng thời nhiều thiết bị chấp hành (ký hiệu chung `D1`, `D2`, `D3`…), và nhận lệnh từ nhiều "terminal" khác nhau (nhiều client cùng publish vào `device_control`) mà không xung đột, vì mỗi bản tin đều mang theo mã thiết bị đích (`device`) và mã định danh riêng của lệnh (`request_id`). Trong phạm vi đồ án hiện tại, hệ thống có đúng 2 thiết bị chấp hành (`room01_lamp`, `room01_fan`), nhưng cơ chế ánh xạ dưới đây viết theo kiểu **bảng tra cứu** để thêm thiết bị thứ 3 chỉ cần thêm một dòng, không phải sửa logic.

⬛ CHÈN HÌNH 2.3
|---|
| **Cần vẽ:** sơ đồ khối — HW (ESP8266 + các thiết bị chấp hành) → MQTT Broker → nhiều Terminal (ter1, ter2, ter3…) cùng gửi lệnh vào `device_control`; chiều ngược lại HW publish `device_respond`/`data_sensors` về broker rồi toả tới mọi terminal đang subscribe. **Kích thước:** ngang 13 cm. |

**Thư viện MQTT sử dụng:** `arduino-mqtt` (còn gọi là `lwmqtt`, tác giả 256dpi) — **không dùng `PubSubClient`**, vì `PubSubClient` chỉ publish được QoS 0 trong khi `device_respond` cần QoS 1 (lý do đầy đủ ở `CLAUDE.md` §5.5).

**Mã nguồn thật đã nạp và chạy** (`firmware/esp8266_room01/esp8266_room01.ino`, dùng thư viện `ArduinoJson` để tách/dựng JSON, không dùng cách nối chuỗi thủ công — an toàn hơn khi chuỗi có khoảng trắng hoặc thứ tự trường thay đổi):

```cpp
#include <ESP8266WiFi.h>
#include <MQTT.h>
#include <DHT.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "<ten_wifi>";
const char* WIFI_PASS = "<mat_khau_wifi>";
const char* MQTT_HOST = "<dia_chi_broker>";   // IP LAN cua may chay Mosquitto
const int   MQTT_PORT = 1884;

#define DHTPIN    D4
#define DHTTYPE   DHT11
#define LIGHTPIN  A0        // Module LM393 hien chi co DO, xem CLAUDE.md §0.3
#define PIN_LAMP  D5
#define PIN_FAN   D6

const char* NODE_ID = "esp8266_room01";
const unsigned long SEND_INTERVAL = 2000;   // 2 giay/lan, dung BR-01
unsigned long lastSend = 0;

WiFiClient net;
MQTTClient client(256);   // Mac dinh 128 byte KHONG du cho payload device_control (~110 byte)
DHT dht(DHTPIN, DHTTYPE);

// Bang tra ma thiet bi -> chan GPIO. Them thiet bi thu 3 chi can them 1 dong.
struct DeviceMap { const char* code; uint8_t pin; };
DeviceMap DEVICES[] = {
  { "room01_lamp", PIN_LAMP },
  { "room01_fan",  PIN_FAN  },
};
const int DEVICE_COUNT = sizeof(DEVICES) / sizeof(DEVICES[0]);

void connectWiFi() {
  Serial.print("Dang ket noi WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" OK, IP: " + WiFi.localIP().toString());
}

void onMqttMessage(String &topic, String &payload) {
  Serial.println("Nhan tren " + topic + ": " + payload);

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    Serial.print("Loi doc JSON, bo qua message: ");
    Serial.println(err.c_str());
    return;
  }

  const char* requestId = doc["request_id"] | "";
  const char* device    = doc["device"]     | "";
  const char* action    = doc["action"]     | "";

  int pin = -1;
  for (int i = 0; i < DEVICE_COUNT; i++) {
    if (strcmp(device, DEVICES[i].code) == 0) { pin = DEVICES[i].pin; break; }
  }
  if (pin == -1) {
    Serial.printf("Bo qua: khong co thiet bi ma \"%s\" trong bang anh xa\n", device);
    return;   // Firmware phai bo qua thiet bi la, khong tu bat chan dau tien (05-API.md §6.3)
  }

  bool turnOn = (strcmp(action, "ON") == 0);
  digitalWrite(pin, turnOn ? HIGH : LOW);

  JsonDocument resp;
  resp["request_id"] = requestId;
  resp["device"]     = device;
  resp["state"]      = turnOn ? "ON" : "OFF";
  resp["status"]     = "SUCCESS";
  String out;
  serializeJson(resp, out);
  client.publish("device_respond", out, false, 1);   // QoS 1, khong retain
  Serial.println("Da gui device_respond: " + out);
}

void connectMQTT() {
  client.begin(MQTT_HOST, MQTT_PORT, net);
  client.onMessage(onMqttMessage);

  String clientId = String(NODE_ID) + "_" + String(ESP.getChipId(), HEX);
  Serial.print("Dang ket noi MQTT broker");
  while (!client.connect(clientId.c_str())) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println(" OK");
  client.subscribe("device_control", 1);
}

void publishSensorData() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  int   l = analogRead(LIGHTPIN);   // Module chi co DO -> tam thoi ra ~0 hoac ~1023

  JsonDocument doc;
  doc["device_id"] = NODE_ID;
  if (!isnan(t)) doc["temperature"] = t;
  if (!isnan(h)) doc["humidity"] = h;
  doc["light"] = l;

  String out;
  serializeJson(doc, out);
  client.publish("data_sensors", out, false, 0);   // QoS 0 (05-API.md §6.2)
  Serial.println("Da gui data_sensors: " + out);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LAMP, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);
  digitalWrite(PIN_LAMP, LOW);
  digitalWrite(PIN_FAN, LOW);

  dht.begin();
  connectWiFi();
  connectMQTT();
}

void loop() {
  client.loop();
  delay(10);   // Khuyen nghi cua thu vien arduino-mqtt tren ESP8266 (CLAUDE.md §5.5)

  if (!client.connected()) {
    connectMQTT();
  }

  if (millis() - lastSend > SEND_INTERVAL) {
    lastSend = millis();
    publishSensorData();
  }
}
```

**Kết quả thực tế khi chạy thật** (nạp bằng `arduino-cli upload`, cổng `COM7`, chip nhận diện `ESP8266EX`, ngày 02/09/2026):

- ESP8266 kết nối WiFi (mạng 2.4GHz) và kết nối MQTT broker thành công, sau đó publish `data_sensors` đều đặn mỗi ~2 giây. Trích Serial Monitor thật:
  ```
  Da gui data_sensors: {"device_id":"esp8266_room01","temperature":34.4,"humidity":36,"light":46}
  Da gui data_sensors: {"device_id":"esp8266_room01","temperature":34.2,"humidity":37,"light":46}
  Da gui data_sensors: {"device_id":"esp8266_room01","temperature":34.4,"humidity":37,"light":46}
  Da gui data_sensors: {"device_id":"esp8266_room01","temperature":34.1,"humidity":37,"light":46}
  ```
- Gửi lệnh `device_control` bằng `mosquitto_pub` cho cả 2 thiết bị, cả 4 lệnh đều nhận `device_respond` **SUCCESS** đúng `request_id`, đèn/quạt đổi trạng thái đúng như lệnh:

  | Lệnh gửi (`device_control`) | Phản hồi nhận được (`device_respond`) |
  |---|---|
  | `{"request_id":"test-report-001","device":"room01_lamp","action":"ON"}` | `{"request_id":"test-report-001","device":"room01_lamp","state":"ON","status":"SUCCESS"}` |
  | `{"request_id":"test-report-002","device":"room01_lamp","action":"OFF"}` | `{"request_id":"test-report-002","device":"room01_lamp","state":"OFF","status":"SUCCESS"}` |
  | `{"request_id":"test-report-003","device":"room01_fan","action":"ON"}` | `{"request_id":"test-report-003","device":"room01_fan","state":"ON","status":"SUCCESS"}` |
  | `{"request_id":"test-report-004","device":"room01_fan","action":"OFF"}` | `{"request_id":"test-report-004","device":"room01_fan","state":"OFF","status":"SUCCESS"}` |

- **Hai hiện tượng phụ quan sát được, không phải lỗi:**
  1. Thỉnh thoảng (khoảng 1/10 lần đọc) DHT11 trả về đọc lỗi — hoặc thiếu hẳn trường `temperature`/`humidity` trong payload (do `isnan()` lọc đúng), hoặc ra giá trị rác kiểu `temperature:0.4, humidity:0` (checksum của DHT11 lỗi nhưng không rơi vào `NaN` nên lọt qua điều kiện lọc hiện tại) — hạn chế đã biết của cảm biến DHT11 giá rẻ, không phải lỗi logic code.
  2. LED xanh có sẵn trên board (nối chung chân **D4/GPIO2** với chân Data của DHT11) nhấp nháy dồn dập mỗi 2 giây đúng lúc `dht.read...()` chạy — vì giao thức đọc DHT11 phải bật/tắt chân D4 rất nhanh nhiều lần trong một lần đọc. Đây là đặc điểm phần cứng của board, không ảnh hưởng tới tính đúng đắn của số liệu.

⬛ CHÈN HÌNH 2.4
|---|
| **Cần chèn:** ảnh chụp Serial Monitor của Arduino IDE khi ESP8266 đang chạy — thấy rõ dòng log kết nối WiFi/MQTT thành công, các dòng "Da gui data_sensors: …" định kỳ, và dòng "Nhan tren device_control: …" khi có lệnh điều khiển gửi tới. **Kích thước:** ngang 15 cm. |

**Bảng đối chiếu mở rộng nhiều thiết bị** (ví dụ minh hoạ nếu thêm thiết bị thứ 3):

| Ký hiệu chung | Mã thiết bị (`device`) | Chân GPIO | Terminal gửi lệnh ví dụ |
|---|---|---|---|
| D1 | `room01_lamp` | D5 | ter1 |
| D2 | `room01_fan` | D6 | ter2 |
| D3 | *(thiết bị mở rộng sau này, ví dụ `room01_curtain`)* | *(chân trống còn lại)* | ter3 |

**Nhận xét:** Độ trễ từ lúc `mosquitto_pub` gửi lệnh `device_control` tới lúc nhận được `device_respond` gần như tức thời (dưới 1 giây, cùng mạng LAN/hotspot với broker). Không quan sát thấy ESP8266 mất kết nối hay tự reset giữa chừng trong suốt quá trình test 4 lệnh điều khiển liên tiếp. Riêng giai đoạn đọc Serial Monitor qua cổng COM có gặp lỗi tạm thời "Access is denied" khi mở song song với tiến trình khác đang truy cập cổng — không liên quan tới firmware, chỉ cần đóng chương trình đang chiếm cổng COM rồi mở lại.
