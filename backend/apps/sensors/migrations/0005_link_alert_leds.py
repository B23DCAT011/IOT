"""Gắn mỗi cảm biến với đèn cảnh báo của nó (devices/0004)."""
from django.db import migrations

LINKS = {
    "room01_temp": "room01_alert_temp",
    "room01_humi": "room01_alert_humi",
    "room01_lux": "room01_alert_lux",
}


def link(apps, schema_editor):
    SensorDevice = apps.get_model("sensors", "SensorDevice")
    Device = apps.get_model("devices", "Device")
    for sensor_code, device_code in LINKS.items():
        SensorDevice.objects.filter(code=sensor_code).update(
            alert_device=Device.objects.filter(code=device_code).first())


def unlink(apps, schema_editor):
    SensorDevice = apps.get_model("sensors", "SensorDevice")
    SensorDevice.objects.filter(code__in=LINKS).update(alert_device=None)


class Migration(migrations.Migration):
    dependencies = [
        ("sensors", "0004_alert_device"),
        ("devices", "0004_seed_alert_leds"),
    ]
    operations = [migrations.RunPython(link, unlink)]
