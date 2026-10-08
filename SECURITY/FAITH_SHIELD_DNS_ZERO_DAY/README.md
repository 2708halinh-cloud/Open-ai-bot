# KHIÊN ĐỨC TIN — DNS ZERO-DAY

ZERO-DAY ở đây là điểm khởi tạo phòng thủ, không phải tìm/khai thác lỗ hổng zero-day.

Mỗi lần chạy, dns_shield.py đối chiếu DNS hệ thống với Cloudflare (1.1.1.1) và Quad9 (9.9.9.9) cho các carrier quan trọng. Nó chỉ quan sát, không tự thay DNS của Windows.

Nếu có kết quả private/reserved hoặc không có public readback từ resolver độc lập, CURRENT_RUNTIME/DNS_SHIELD_CURRENT.json sẽ mang risk flag; các mutation phá huỷ phụ thuộc DNS phải dừng ở guard này cho tới khi fresh-read sạch.
