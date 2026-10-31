"""Ba đèn LED cảnh báo vượt ngưỡng — chân GPIO khớp PIN_ALERT_* trong firmware esp8266_room01.ino.

Không dùng D3/D4/D8: các chân đó quyết định chế độ khởi động của ESP8266 (D4 còn nối DHT11).
"""
from django.db import migrations

SEED = [
    {"code": "room01_alert_temp", "name": "Đèn cảnh báo nhiệt độ", "device_type": "ALERT", "gpio_pin": "D1"},
    {"code": "room01_alert_humi", "name": "Đèn cảnh báo độ ẩm", "device_type": "ALERT", "gpio_pin": "D2"},
    {"code": "room01_alert_lux", "name": "Đèn cảnh báo ánh sáng", "device_type": "ALERT", "gpio_pin": "D7"},
]


def create_alert_leds(apps, schema_editor):
    Device = apps.get_model("devices", "Device")
    for item in SEED:
        Device.objects.get_or_create(code=item["code"], defaults=item)


def remove_alert_leds(apps, schema_editor):
    Device = apps.get_model("devices", "Device")
    Device.objects.filter(code__in=[i["code"] for i in SEED]).delete()


class Migration(migrations.Migration):
    dependencies = [("devices", "0003_alert_device_type")]
    operations = [migrations.RunPython(create_alert_leds, remove_alert_leds)]
