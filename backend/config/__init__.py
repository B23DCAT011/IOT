import sys

# Console Windows mặc định cp1252 khi xuất ra pipe/file → log tiếng Việt vỡ thành "Đ�"
# (cùng bẫy với tools/assemble.py — CLAUDE.md §5.4). Gói `config` được cả manage.py lẫn
# daphne import đầu tiên nên đặt ở đây là phủ hết mọi tiến trình.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
