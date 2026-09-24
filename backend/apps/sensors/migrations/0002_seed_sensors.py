"""Danh mục 3 cảm biến của phòng 1 — 04-Database.md §10.1, §10.2.

Ngưỡng min/max là BR-02. Hiệu chuẩn lại quang trở thì sửa trong trang admin rồi
khởi động lại mqtt_worker — không cần migration mới.
"""
from django.db import migrations

SEED = [
    {"code": "room01_temp", "name": "Nhiệt độ phòng", "metric_type": "TEMPERATURE",
     "unit": "°C", "hardware_model": "DHT11", "min_value": -10, "max_value": 60},
    {"code": "room01_humi", "name": "Độ ẩm phòng", "metric_type": "HUMIDITY",
     "unit": "%", "hardware_model": "DHT11", "min_value": 0, "max_value": 100},
    {"code": "room01_lux", "name": "Ánh sáng phòng", "metric_type": "LIGHT",
     "unit": "lux", "hardware_model": "LM393", "min_value": 0, "max_value": 2000},
]


def create_sensors(apps, schema_editor):
    SensorDevice = apps.get_model("sensors", "SensorDevice")
    for item in SEED:
        SensorDevice.objects.get_or_create(code=item["code"], defaults=item)


def remove_sensors(apps, schema_editor):
    SensorDevice = apps.get_model("sensors", "SensorDevice")
    SensorDevice.objects.filter(code__in=[i["code"] for i in SEED]).delete()


class Migration(migrations.Migration):
    dependencies = [("sensors", "0001_initial")]
    operations = [migrations.RunPython(create_sensors, remove_sensors)]
