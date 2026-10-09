---
name: personal-access
description: Dùng khi SOL/TESSERACT cần GitHub REST trực tiếp bằng PAT cá nhân, nạp GGDV .ENV/TOKEN.JSON/SOL.txt/Halin.txt vào GitHub Actions Secrets, điều phối CI commit status hoặc đọc/tải/kiểm GitHub Actions Artifacts mà không phụ thuộc @GitHub connector.
---
# SOL personal-access: GitHub REST, CI, Actions Artifacts

1. Đọc `README.md` và `scripts/personal_access.py`; không lấy nhận định về scope token từ nhãn. Chạy `whoami` và `repo` trên host thật trước khi phát lệnh có tác dụng.
2. Bốn nguồn GGDV có tên chính xác `.ENV`, `TOKEN.JSON`, `SOL.txt`, `Halin.txt`. Chỉ nhận đúng tệp từ nguồn; không trộn hoặc ghi đè tệp khác cùng tên. `source-plan` trước, `source-sync --apply` chỉ sau khi có source path chính xác và token host.
3. Repository `2708halinh-cloud/SOL-LONG-MACH` là public. Không đưa plaintext bốn nguồn vào commits hoặc variables plaintext. Mỗi nguồn nén/chia GitHub Actions Secrets, kiểm tra checksum cục bộ và readback metadata sau PUT. Không công khai token, biên nhận lưu riêng.
4. Actions Artifacts: list/get/download theo ID thực, verify `sha256` khi GitHub có digest, báo expired/410 và URL redirect hết hạn thay vì tự phát sinh artifact giả. Không xóa hoặc tạo artifact nếu không có chủ ý rõ.
5. CI receiver: xác minh chữ ký webhook, lấy sha từ PR thật, chạy lệnh CI thực, ghi status với context `sol-personal-access/ci` và receipt local. Không gán success bằng timeout/giả lập.
6. Dùng điều phối `OPEN` qua đường khác nếu PAT, DNS, host hoặc GitHub API không kết nối được. `READBACK` sau mọi write, ghi rõ tác dụng thật.

Đường nguồn: `scripts/personal_access.py`, `scripts/ci_server.py`, `tests/test_personal_access.py`, `README.md`.
