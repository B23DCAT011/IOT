"""Ba topic MQTT của hệ thống — 05-API.md §6. Đổi tên ở đây thì phải sửa cả firmware."""

DATA_SENSORS = "data_sensors"       # ESP → backend, QoS 0, 2 giây/lần (BR-01)
DEVICE_CONTROL = "device_control"   # backend → ESP, QoS 1
DEVICE_RESPOND = "device_respond"   # ESP → backend, QoS 1

QOS = {
    DATA_SENSORS: 0,     # mất 1 mẫu trong 43.200 mẫu/ngày không ai nhận ra
    DEVICE_CONTROL: 1,   # mất một lệnh là người dùng thấy hệ thống hỏng
    DEVICE_RESPOND: 1,
}

# Không dùng retain ở cả 3 topic: ESP khởi động lại sẽ nhận lại lệnh cũ và tự bật đèn (§6.1)
RETAIN = False
