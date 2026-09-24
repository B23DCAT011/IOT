"""Hai thiết bị chấp hành — 04-Database.md §10.2. Chân GPIO khớp firmware esp8266_room01.ino.

Trạng thái ban đầu OFF vì pinMode(OUTPUT) trên ESP8266 đặt chân về LOW sau khi khởi động.
"""
from django.db import migrations

SEED = [
    {"code": "room01_lamp", "name": "Đèn phòng", "device_type": "LIGHT", "gpio_pin": "D5"},
    {"code": "room01_fan", "name": "Quạt trần", "device_type": "FAN", "gpio_pin": "D6"},
]


def create_devices(apps, schema_editor):
    Device = apps.get_model("devices", "Device")
    for item in SEED:
        Device.objects.get_or_create(code=item["code"], defaults=item)


def remove_devices(apps, schema_editor):
    Device = apps.get_model("devices", "Device")
    Device.objects.filter(code__in=[i["code"] for i in SEED]).delete()


class Migration(migrations.Migration):
    dependencies = [("devices", "0001_initial")]
    operations = [migrations.RunPython(create_devices, remove_devices)]
