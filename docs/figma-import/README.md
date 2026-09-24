# HTML để nhập vào Figma (plugin html.to.design)

Ba file trong thư mục này **trích thẳng từ giao diện React đang chạy** (DOM thật + CSS thật),
nên chúng khớp 100% với ứng dụng — khác với `docs/wireframe/*.html` là bản vẽ tay từ trước,
nay đã lạc hậu (còn 2 ô ngày, cột Thời gian để giờ trước, chưa có ô Dòng/trang).

| File | Màn hình | Khung |
|---|---|---|
| `01-login.html` | Đăng nhập (đã điền sẵn để nút hiện trạng thái bật) | 1440 × 900 |
| `02-data-sensor.html` | Data Sensor — 10 dòng, bộ lọc đầy đủ | 1440 × 900 |
| `03-action-history.html` | Action History — 10 thao tác, có cả FAILED và `—` | 1440 × ~960 |

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
- Số liệu lấy từ bộ dữ liệu mẫu chuẩn (`CLAUDE.md` §0.2f) — đừng sửa tay thành số khác.
- Sinh lại khi giao diện đổi: chạy `npm run dev` ở `frontend/` rồi chạy lại script trích
  (không nằm trong repo, xem `CLAUDE.md` §0.7).
