# SOL PERSONAL-ACCESS — GitHub REST riêng, CI và Actions Artifacts

**Phiên bản:** 0.1.0 • **Nguồn đích:** `2708halinh-cloud/SOL-LONG-MACH` (repository public), **branch** `sol-personal-access-ci-artifacts-20261010`.

Đây là mã chạy trực tiếp trên máy Windows/Ubuntu có quyền truy cập internet. Nó **không sử dụng connector `@GitHub`** để thực hiện lệnh. Đây không phải đặc quyền cấp thêm: token/tài khoản quyết định các quyền API thực tế. Không đưa PAT hoặc nội dung tệp nguồn vào plugin, GitHub commit, lời nhắn, URL hay CI log.

## Khởi động từ PC

```powershell
$env:SOL_GITHUB_TOKEN_FILE = 'D:\SENSOR_LOGS\Chìa Khóa Thiên Đàng\github.env.txt'
python scripts/personal_access.py whoami
python scripts/personal_access.py repo
python scripts/personal_access.py artifacts
```

File token chỉ đọc trên chính máy người dùng; nếu biến này không đúng vị trí, cung cấp `SOL_GITHUB_TOKEN` trực tiếp vào biến môi trường OS do mình quản lý. Phần mềm không chép nguồn credentials vào GitHub.

## Bốn vật mang yêu cầu

**Trạng thái nguồn đã đối chiếu trong phiên 10/10/2026:**
- `SOL.txt`: 428523 bytes, có nguồn trong phiên.
- `Halin.txt`: 3195341 bytes, có nguồn trong phiên.
- `.ENV`, `TOKEN.JSON`: chưa đọc được đúng hai file gốc trong phiên. Không tự dựng giá trị.

Các tên biến GitHub Actions Secrets (không phải Repository Variables plaintext):
- `GGDV_DOT_ENV_META`, `GGDV_DOT_ENV_PART_000...`
- `GGDV_TOKEN_JSON_META`, `GGDV_TOKEN_JSON_PART_000...`
- `GGDV_SOL_TXT_META`, `GGDV_SOL_TXT_PART_000...`
- `GGDV_HALIN_TXT_META`, `GGDV_HALIN_TXT_PART_000...`

Để kiểm tra nguồn:

```powershell
python scripts/personal_access.py source-plan --source-dir 'D:\SENSOR_LOGS\Chìa Khóa Thiên Đàng' 
```

Để ghi GitHub Secrets sau khi đã đặt token có quyền `Secrets:write` thực sự và cài `PyNaCl`:

```powershell
python -m pip install pynacl
python scripts/personal_access.py source-sync --source-dir 'D:\SENSOR_LOGS\Chìa Khóa Thiên Đàng' --apply
python scripts/personal_access.py secrets-list
```

`source-plan` mặc định không gọi mạng. `source-sync` không có `--apply` chỉ xuất kế hoạch. Mỗi tệp được gzip + base64, chia thành các phần dưới 48KiB. SHA-256 được kiểm tra **trước khi ghi** và đưa vào manifest bí mật. Có thể kiểm tra tên secret và updated_at sau khi API nhận, nhưng API không cho đọc ngược plaintext bí mật: trạng thái đòi hỏi CI readback ở host riêng nếu cần chứng minh byte đích.

GitHub giới hạn 100 repository secrets, 48KiB mỗi secret. Với hai tệp 428523 bytes và 3195341 bytes, kế hoạch dự kiến nằm dưới ngưỡng; công cụ kiểm toán đếm chính xác và từ chối ghi khi vượt giới hạn.

## GitHub Actions Artifacts thực

```powershell
python scripts/personal_access.py artifacts
python scripts/personal_access.py artifacts --run-id 37545405120 --repo 2708halinh-cloud/x-time-web
python scripts/personal_access.py artifact 123456
python scripts/personal_access.py download-artifact 123456 --output .\readback\artifact.zip
```

Lệnh `artifacts` đọc `GET /repos/{owner}/{repo}/actions/artifacts`, hoặc `.../runs/{run_id}/artifacts`. Lệnh tải ZIP dùng endpoint `/artifacts/{id}/zip`, theo redirect một phút mà **không chuyển Authorization tới object-store**; so SHA-256 khi GitHub cung cấp `digest`. `410 Gone` hoặc hết hạn không được đánh dấu thành công. Không có lệnh xóa artifact mặc định.

## CI máy người dùng

`ci_server.py` lắng nghe POST `/event_handler`, kiểm chữ ký `X-Hub-Signature-256`, nhận các sự kiện PR `opened` / `reopened` / `synchronize`. Khi nhận đúng sự kiện từ repo đã khai báo, nó đặt commit status `pending`, thực sự chạy argv CI trên working directory do người quản trị chỉ định, ghi biên nhận local, rồi đặt `success` / `failure` / `error` đúng kết quả. Không có `sleep → success` giả.

```powershell
$env:SOL_CI_REPO='2708halinh-cloud/SOL-LONG-MACH'
$env:SOL_CI_WEBHOOK_SECRET='<chuỗi riêng giữ trên host>'
$env:SOL_CI_COMMAND_JSON='["python","-m","unittest","discover","-s","tests"]'
$env:SOL_CI_CWD='D:\your\checked-out\repo'
python scripts/ci_server.py
```

Listener mặc định `127.0.0.1:8777`: muốn nhận GitHub webhooks, cần cấu hình URL có thể truy cập tới host riêng (tunnel, reverse proxy, webhook relay) và dùng secret chữ ký. **Chưa đăng ký webhook** trên repository và chưa cài host, không khẳng định CI đã hoạt động.

## Tiếp diễn

- `PLUGIN_SOURCE`: thực hiện cục bộ và độc lập với plugin @GitHub.
- `REPO_BRANCH`: ghi tài liệu/mã lên branch mới, không thay `main`.
- `SECRETS_REMOTE`: chưa ghi giá trị vì connector GitHub hiện có không hỗ trợ endpoint Secret write, container không có mạng truy cập GitHub trực tiếp.
- `SOL_HOST`: chưa có biên nhận API phát sinh tại DESKTOP-86ITNQ4.
- `CI_SERVER`: thử nghiệm chạy local, chưa triển khai webhook ngoài mạng.

**Hướng dẫn quyền:** PAT chỉ dùng ở host do SOL quản lý; `admin` trên repository từ connector không đồng nghĩa PAT đã có mọi permission trong danh sách của user. `GET /user` và `GET /repos/...` là phép thử đầu tiên.
