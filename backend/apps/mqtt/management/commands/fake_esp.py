"""ESP8266 giả lập — `python manage.py fake_esp` — để chạy thử toàn hệ thống khi chưa cắm mạch.

Làm đúng ba việc của firmware esp8266_room01.ino:
  1. Mỗi 2 giây publish `data_sensors` (nhiệt độ, độ ẩm, ánh sáng dao động nhẹ).
  2. Nhận `device_control` → trả `device_respond` với status SUCCESS.
  3. Mỗi lần kết nối broker → báo trạng thái thật (status REPORT). Mới khởi động nên mọi
     thiết bị đều OFF — tắt rồi bật lại lệnh này là diễn lại được cảnh "rút điện mạch".

Tuỳ chọn để diễn lại các tình huống lỗi:
  --no-respond          không trả lời lệnh → sau 5–6 giây lệnh FAILED (BR-03, SD-05)
  --missing-humidity N  cứ N chu kỳ thì bỏ trường humidity một lần (UC-07 A2, biểu đồ đứt nét)

⚠️ Đừng chạy cùng lúc với mạch thật: hai "thiết bị" cùng trả lời một lệnh.
"""
import json
import random
import time

from django.core.management.base import BaseCommand

from apps.mqtt import topics
from apps.mqtt.client import broker_address, create_client

NODE_ID = "esp8266_room01"


class Command(BaseCommand):
    help = "Giả lập ESP8266: gửi số đo mỗi 2 giây và trả lời lệnh điều khiển."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=2.0, help="Giây giữa hai lần gửi (BR-01)")
        parser.add_argument("--no-respond", action="store_true", help="Không trả lời device_control")
        parser.add_argument("--missing-humidity", type=int, default=0, metavar="N",
                            help="Cứ N chu kỳ bỏ trường humidity một lần (0 = không bỏ)")

    def handle(self, *args, **options):
        self.respond = not options["no_respond"]
        self.state = {"temperature": 28.0, "humidity": 72.0, "light": 350.0}
        self.outputs = {"room01_lamp": "OFF", "room01_fan": "OFF"}   # như setup(): mọi chân LOW

        client = create_client(f"fake_{NODE_ID}")   # khác ID của mạch thật, không đá nhau
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(*broker_address(), keepalive=30)
        client.loop_start()

        cycle = 0
        try:
            while True:
                cycle += 1
                every = options["missing_humidity"]
                payload = self.next_reading(drop_humidity=bool(every) and cycle % every == 0)
                client.publish(topics.DATA_SENSORS, json.dumps(payload), qos=topics.QOS[topics.DATA_SENSORS])
                self.stdout.write(f"→ data_sensors  {payload}")
                time.sleep(options["interval"])
        except KeyboardInterrupt:
            pass
        finally:
            client.disconnect()
            client.loop_stop()

    def next_reading(self, drop_humidity):
        """Đi ngẫu nhiên quanh giá trị hiện tại — nhìn trên biểu đồ giống số liệu thật."""
        s = self.state
        s["temperature"] = min(max(s["temperature"] + random.uniform(-0.2, 0.2), 25), 32)
        s["humidity"] = min(max(s["humidity"] + random.uniform(-0.8, 0.8), 60), 90)
        s["light"] = min(max(s["light"] + random.uniform(-15, 15), 80), 700)
        payload = {
            "device_id": NODE_ID,
            "temperature": round(s["temperature"], 1),
            "humidity": round(s["humidity"], 1),
            "light": round(s["light"]),
        }
        if drop_humidity:
            del payload["humidity"]
        return payload

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            self.stderr.write(f"Broker từ chối kết nối: {reason_code}")
            return
        client.subscribe(topics.DEVICE_CONTROL, qos=topics.QOS[topics.DEVICE_CONTROL])
        self.stdout.write(f"Đã kết nối {broker_address()} — trả lời lệnh: {self.respond}")
        for code, state in self.outputs.items():
            report = {"device": code, "state": state, "status": "REPORT"}
            client.publish(topics.DEVICE_RESPOND, json.dumps(report), qos=topics.QOS[topics.DEVICE_RESPOND])
            self.stdout.write(f"→ báo trạng thái {report}")

    def on_message(self, client, userdata, message):
        command = json.loads(message.payload)
        self.stdout.write(f"← device_control {command}")
        if not self.respond:
            return
        if command.get("device") in self.outputs:
            self.outputs[command["device"]] = command.get("action")
        reply = {
            "request_id": command.get("request_id"),
            "device": command.get("device"),
            "state": command.get("action"),
            "status": "SUCCESS",
        }
        client.publish(topics.DEVICE_RESPOND, json.dumps(reply), qos=topics.QOS[topics.DEVICE_RESPOND])
        self.stdout.write(f"→ device_respond {reply}")
