/*
  ESP8266 — Giám sát & điều khiển phòng qua MQTT
  Node: esp8266_room01

  Chân đấu dây (theo firmware/HuongDanLapRap.md):
    DHT11        -> D4
    LM393 (DO)   -> A0   (module chỉ có DO, chưa có AO — xem CLAUDE.md §0.3)
    LED "Đèn"    -> D5   (mã nghiệp vụ: room01_lamp)
    LED "Quạt"   -> D6   (mã nghiệp vụ: room01_fan)

  Thư viện cần cài qua Library Manager (Sketch > Include Library > Manage Libraries):
    - "DHT sensor library" by Adafruit          (kèm theo "Adafruit Unified Sensor")
    - "MQTT" by Joel Gaehwiler                  (tìm bằng từ khoá "lwmqtt" nếu không thấy ngay)
    - "ArduinoJson" by Benoit Blanchon           (bản 7.x)

  Board: đảm bảo đã cài gói "esp8266" trong Boards Manager, chọn đúng board
  NodeMCU 1.0 (ESP-12E Module) trước khi Upload.
*/

#include <ESP8266WiFi.h>
#include <MQTT.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ------------------ CẤU HÌNH — THÔNG TIN ------------------
// Tài khoản WiFi và MQTT nằm ở secrets.h — file đó KHÔNG commit lên GitHub.
// Chưa có thì chép secrets.example.h thành secrets.h rồi điền giá trị thật.
// Arduino IDE tự mở secrets.h thành một tab cạnh file này.
#include "secrets.h"
const char* MQTT_HOST = "172.20.10.5";   // IP LAN của máy chạy Mosquitto — xem lại bằng ipconfig nếu đổi
const int   MQTT_PORT = 1884;
// -----------------------------------------------------------------------------

#define DHTPIN    D4
#define DHTTYPE   DHT11
#define LIGHTPIN  A0
#define PIN_LAMP  D5
#define PIN_FAN   D6

const char* NODE_ID = "esp8266_room01";
// In ra ngay đầu Serial Monitor để biết chắc mạch đang chạy bản nào — đổi mỗi lần sửa firmware.
const char* FW_VERSION = "2026-09-24 lenh-gop";
const unsigned long SEND_INTERVAL = 2000;   // 2 giây/lần
unsigned long lastSend = 0;

WiFiClient net;
MQTTClient client(256);   // Mặc định 128 byte KHÔNG đủ cho payload device_control (~110 byte)
DHT dht(DHTPIN, DHTTYPE);

// Bảng tra mã thiết bị -> chân GPIO. Thêm thiết bị thứ 3 chỉ cần thêm 1 dòng.
struct DeviceMap { const char* code; uint8_t pin; };
DeviceMap DEVICES[] = {
  { "room01_lamp", PIN_LAMP },
  { "room01_fan",  PIN_FAN  },
};
const int DEVICE_COUNT = sizeof(DEVICES) / sizeof(DEVICES[0]);

// ⚠️ Hàng đợi phản hồi — KHÔNG gọi client.publish() bên trong onMqttMessage().
// Thư viện arduino-mqtt dùng CHUNG một bộ đệm 256 byte cho cả nhận lẫn gửi, nên publish
// ngay trong callback là ghi đè lên chính message đang được xử lý. Một gói thì thường
// thoát, hai gói liên tiếp (lệnh gộp) thì hỏng máy trạng thái: broker ngắt kết nối, ESP
// nối lại và bắn ra một loạt gói REPORT của connectMQTT() — đúng hiện tượng ngày 24/09.
// Vì vậy callback chỉ xếp hàng, loop() mới gửi thật.
struct PendingResponse {
  char        requestId[48];
  const char* device;   // trỏ vào DEVICES[].code — chuỗi tĩnh, sống lâu hơn JsonDocument tạm
  const char* state;
  const char* status;
};
PendingResponse RESP_QUEUE[4];
int respCount = 0;

// Chỉ báo trạng thái ở lần vào broker đầu tiên sau khi khởi động — xem publishStateReport().
bool firstConnect = true;

// Mã gộp: một lệnh áp dụng cho MỌI thiết bị trong bảng trên (tắt/bật hết một lượt).
// Không có dòng nào mang mã này trong bảng devices_device của CSDL — xem ghi chú ở
// onMqttMessage() về cách firmware trả lời để giao diện vẫn đúng khi backend chưa sửa.
const char* ALL_DEVICES_CODE = "all";

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
  DeserializationError err = deserializeJson(doc,  -fpayload);
  if (err) {
    Serial.print("Loi doc JSON, bo qua message: ");
    Serial.println(err.c_str());
    return;
  }

  const char* requestId = doc["request_id"] | "";
  const char* device    = doc["device"]     | "";
  const char* action    = doc["action"]     | "";

  // Lệnh gộp: đặt toàn bộ thiết bị về cùng một trạng thái, trả lời MỖI THIẾT BỊ MỘT GÓI
  // SUCCESS/FAILED mang đúng mã thật của nó (không gói nào mang chữ "all", vì mã đó không
  // có trong bảng devices_device). Cả mấy gói dùng chung `request_id` của lệnh gốc.
  // ⚠️ Backend hiện tra `request_id` ra bản ghi action_history rồi mới cập nhật; lệnh gộp
  // không đi qua API nên không khớp được bản ghi nào ⇒ backend bỏ qua, CSDL và giao diện
  // web CHƯA đổi theo. Phải thêm endpoint điều khiển gộp ở backend thì mới đủ.
  if (strcmp(device, ALL_DEVICES_CODE) == 0) {
    bool turnOnAll = (strcmp(action, "ON") == 0);
    Serial.printf("Lenh gop \"%s\": dat %d thiet bi ve %s\n",
                  device, DEVICE_COUNT, turnOnAll ? "ON" : "OFF");
    for (int i = 0; i < DEVICE_COUNT; i++) {
      digitalWrite(DEVICES[i].pin, turnOnAll ? HIGH : LOW);
      queueCommandResult(requestId, DEVICES[i].code, turnOnAll ? "ON" : "OFF", "SUCCESS");
    }
    return;
  }

  int index = -1;
  for (int i = 0; i < DEVICE_COUNT; i++) {
    if (strcmp(device, DEVICES[i].code) == 0) { index = i; break; }
  }
  if (index == -1) {
    Serial.printf("Bo qua: khong co thiet bi ma \"%s\" trong bang anh xa\n", device);
    return;   // Firmware phải bỏ qua thiết bị lạ, không tự bật chân đầu tiên (05-API.md §6.3)
  }

  bool turnOn = (strcmp(action, "ON") == 0);
  digitalWrite(DEVICES[index].pin, turnOn ? HIGH : LOW);
  queueCommandResult(requestId, DEVICES[index].code, turnOn ? "ON" : "OFF", "SUCCESS");
}

// Xếp một phản hồi vào hàng đợi. Gọi từ callback; việc gửi để loop() làm.
void queueCommandResult(const char* requestId, const char* device,
                        const char* state, const char* status) {
  const int QUEUE_SIZE = sizeof(RESP_QUEUE) / sizeof(RESP_QUEUE[0]);
  if (respCount >= QUEUE_SIZE) {
    Serial.println("Hang doi phan hoi day, bo qua mot goi device_respond");
    return;
  }
  PendingResponse &item = RESP_QUEUE[respCount++];
  strncpy(item.requestId, requestId, sizeof(item.requestId) - 1);
  item.requestId[sizeof(item.requestId) - 1] = '\0';   // requestId trỏ vào JsonDocument tạm ⇒ phải chép
  item.device = device;
  item.state  = state;
  item.status = status;
}

// Gửi hết hàng đợi. Chỉ gọi từ loop(), sau khi client.loop() đã xử lý xong message.
// Giữa hai gói phải nhường lượt cho client.loop(): publish QoS 1 chờ broker trả PUBACK,
// bắn liên tiếp mà không cho thư viện đọc PUBACK của gói trước thì gói sau hết giờ chờ
// (mặc định 1 giây) và lwmqtt coi như mất kết nối — mạch nối lại, sinh ra loạt gói REPORT.
void flushCommandResults() {
  for (int i = 0; i < respCount; i++) {
    if (!client.connected()) {
      Serial.println("Mat ket noi giua chung, bo cac phan hoi con lai trong hang doi");
      break;
    }
    publishCommandResult(RESP_QUEUE[i].requestId, RESP_QUEUE[i].device,
                         RESP_QUEUE[i].state, RESP_QUEUE[i].status);
    client.loop();
    delay(10);
  }
  respCount = 0;
}

// Một gói device_respond xác nhận lệnh đã thực thi (SD-02). Dùng cho cả lệnh một thiết bị
// lẫn từng thiết bị trong lệnh gộp, nên mọi gói có cùng hình dạng — backend chỉ cần một
// nhánh xử lý. `status` là "SUCCESS" hoặc "FAILED" (05-API.md §6.3).
void publishCommandResult(const char* requestId, const char* device,
                          const char* state, const char* status) {
  JsonDocument resp;
  resp["request_id"] = requestId;
  resp["device"]     = device;
  resp["state"]      = state;
  resp["status"]     = status;
  String out;
  serializeJson(resp, out);
  client.publish("device_respond", out, false, 1);   // QoS 1, khong retain
  Serial.println("Da gui device_respond: " + out);
}

// Gửi một lệnh device_control lên broker y như backend vẫn làm.
// Chính ESP này đang subscribe device_control nên sẽ tự nhận lại và thực thi,
// nhờ vậy lệnh gõ từ Serial Monitor đi đúng luồng MQTT, không đi tắt.
void publishControl(const char* device, const char* action) {
  if (!client.connected()) {
    Serial.println("Chua ket noi broker, bo qua lenh vua go");
    return;
  }
  JsonDocument cmd;
  cmd["request_id"] = "serial-" + String(millis());
  cmd["device"]     = device;
  cmd["action"]     = action;
  String out;
  serializeJson(cmd, out);
  client.publish("device_control", out, false, 1);
  Serial.println("Da gui device_control: " + out);
}

// Đọc lệnh gõ trong ô Message của Serial Monitor.
// Đặt ô line ending của Serial Monitor là "New Line" thì gõ xong Enter là chạy ngay.
void handleSerialCommand() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();
  line.toLowerCase();
  if (line.length() == 0) return;

  if      (line == "lamp on"  || line == "den on")   publishControl("room01_lamp", "ON");
  else if (line == "lamp off" || line == "den off")  publishControl("room01_lamp", "OFF");
  else if (line == "fan on"   || line == "quat on")  publishControl("room01_fan",  "ON");
  else if (line == "fan off"  || line == "quat off") publishControl("room01_fan",  "OFF");
  else if (line == "all on"   || line == "bat het")  publishControl(ALL_DEVICES_CODE, "ON");
  else if (line == "all off"  || line == "tat het")  publishControl(ALL_DEVICES_CODE, "OFF");
  else {
    Serial.println("Khong hieu lenh: \"" + line + "\"");
    Serial.println("Cac lenh dung duoc: lamp on | lamp off | fan on | fan off | all on | all off");
  }
}

void connectMQTT() {
  client.begin(MQTT_HOST, MQTT_PORT, net);
  client.onMessage(onMqttMessage);

  String clientId = String(NODE_ID) + "_" + String(ESP.getChipId(), HEX);
  Serial.print("Dang ket noi MQTT broker voi tai khoan \"" + String(MQTT_USER) + "\" (client ID: " + clientId + ")");
  while (!client.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println(" OK");
  client.subscribe("device_control", 1);
  if (firstConnect) {
    firstConnect = false;
    publishStateReport();
  }
}

// Báo trạng thái THẬT của từng thiết bị, CHỈ ở lần vào broker đầu tiên sau khi khởi động.
// Mất điện rồi cắm lại, setup() đặt mọi chân về LOW nên đèn đang tắt — nhưng CSDL và
// giao diện vẫn nhớ "ON" từ trước. Gói này giúp backend sửa lại cho đúng phần cứng.
// Đi chung topic device_respond, phân biệt bằng status "REPORT" và KHÔNG có request_id.
// ⚠️ Trước đây gửi ở MỌI lần nối lại broker, nên mỗi lần rớt sóng là cửa sổ device_respond
// lại có một cụm REPORT xen vào giữa các gói SUCCESS. Mất điện thì mạch khởi động lại
// (firstConnect = true) nên tình huống cần đồng bộ vẫn được phủ.
void publishStateReport() {
  for (int i = 0; i < DEVICE_COUNT; i++) {
    JsonDocument doc;
    doc["device"] = DEVICES[i].code;
    doc["state"]  = digitalRead(DEVICES[i].pin) == HIGH ? "ON" : "OFF";
    doc["status"] = "REPORT";
    String out;
    serializeJson(doc, out);
    client.publish("device_respond", out, false, 1);
    Serial.println("Da bao trang thai: " + out);
    client.loop();
    delay(10);
  }
}

void publishSensorData() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  int   l = analogRead(LIGHTPIN);   // Module chỉ có DO -> tạm thời ra ~0 hoặc ~1023

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
  Serial.println();
  Serial.println("=== " + String(NODE_ID) + " — firmware " + FW_VERSION + " ===");
  pinMode(PIN_LAMP, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);
  digitalWrite(PIN_LAMP, LOW);
  digitalWrite(PIN_FAN, LOW);

  dht.begin();
  // Lần đọc DHT11 đầu tiên sau khi cấp điện ra số rác (đo được 0.9 °C / 0 % ngày 18/09/2026)
  // chứ không ra NaN, nên isnan() không lọc được. Chờ cảm biến ổn định, đọc nháp một lần rồi bỏ.
  delay(2000);
  dht.read();
  // Thư viện DHT trả lại kết quả CŨ nếu hai lần đọc cách nhau < 2 giây. Đặt mốc ở đây để
  // lần gửi data_sensors đầu tiên chắc chắn đọc lại cảm biến, không dùng lại số rác vừa bỏ.
  lastSend = millis();
  connectWiFi();
  connectMQTT();

  Serial.println("San sang. Go lenh vao o Message cua Serial Monitor:");
  Serial.println("  lamp on | lamp off | fan on | fan off | all on | all off");
}

void loop() {
  client.loop();
  delay(10);   // Khuyến nghị của thư viện arduino-mqtt trên ESP8266 (CLAUDE.md §5.5)

  if (!client.connected()) {
    connectMQTT();
  }

  flushCommandResults();   // Gửi phản hồi của message vừa nhận — phải ở NGOÀI callback
  handleSerialCommand();

  if (millis() - lastSend > SEND_INTERVAL) {
    lastSend = millis();
    publishSensorData();
  }
}
