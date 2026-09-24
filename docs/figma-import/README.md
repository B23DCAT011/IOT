# HTML để nhập vào Figma (plugin html.to.design)

Năm file trong thư mục này **trích thẳng từ giao diện React đang chạy** (DOM thật + CSS thật),
nên chúng khớp 100% với ứng dụng — khác với `docs/wireframe/*.html` là bản vẽ tay từ trước,
nay đã lạc hậu (còn 2 ô ngày, cột Thời gian để giờ trước, chưa có ô Dòng/trang).

| File | Màn hình | Khung |
|---|---|---|
| `01-login.html` | Đăng nhập — đã điền sẵn để nút hiện trạng thái bật | 1440 × 900 |
| `02-dashboard.html` | Dashboard — 3 thẻ số, biểu đồ 20 mẫu, panel 2 thiết bị | 1440 × 900 |
| `03-data-sensor.html` | Data Sensor — 10 dòng, đủ 7 ô lọc | 1440 × 900 |
| `04-action-history.html` | Action History — 10 thao tác, có `FAILED` và người thao tác `—` | 1440 × ~960 |
| `05-profile.html` | Profile — thông tin sinh viên + 4 liên kết bàn giao | 1440 × 900 |

Mọi con số lấy từ bộ dữ liệu mẫu chuẩn (`CLAUDE.md` §0.2f): Dashboard là chu kỳ `17:30:02`
(28.5 °C · 72.0 % · 350 lux, biến thiên −0.1 / −14.4 / +262), đường độ ẩm **đứt một đoạn** ở
`17:29:54` đúng như UC-07 A2; Action History có lệnh 88 `FAILED` và lệnh 79 không rõ người bấm.

## Cách nhập

1. Trong Figma mở plugin **html.to.design** → thẻ **Import from code / Paste HTML**.
   (Nhập bằng URL không dùng được vì file nằm trên máy, không có địa chỉ web.)
2. Mở file `.html` bằng Notepad, chọn tất cả, dán vào ô của plugin.
3. Đặt **viewport width = 1440**, rồi Import.

## Lưu ý

- CSS nhúng thẳng trong từng file, **không có file dùng chung** — tách ra là mất sạch style
  (đã dính một lần, xem `CLAUDE.md` §0.1 mục 13).
- Font khai là `Segoe UI` và `Consolas`; máy Windows có sẵn nên Figma không phải thay font.
- Mọi vùng cuộn đã bị tắt và nội dung trải hết, để plugin không cắt mất phần dưới bảng.
- Sinh lại khi giao diện đổi: chạy `npm run dev` ở `frontend/` rồi chạy lại script trích
  (không nằm trong repo, cách làm và 6 cái bẫy ghi ở `CLAUDE.md` §0.7).
