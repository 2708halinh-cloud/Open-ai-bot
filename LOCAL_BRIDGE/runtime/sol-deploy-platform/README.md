# SOL DEPLOY PLATFORM

Ứng dụng điều phối **xây dựng (build)** và **triển khai (deploy)** dịch vụ theo kiểu PaaS tương tự Railway, nhưng chạy cục bộ trong hệ SOL.

## Mục tiêu

Luồng chính:

PROJECT
→ SERVICE
→ BUILD
→ DEPLOY
→ HEALTHCHECK
→ LOGS
→ STOP / REDEPLOY.

Bản hiện tại dùng Python chuẩn + SQLite, không cần framework ngoài.

## Ranh giới vận hành

- Bảng điều khiển chỉ bind `127.0.0.1` mặc định.
- Chỉ chạy lệnh build/start của service đã đăng ký.
- Thư mục service phải nằm bên trong `SOL_DEPLOY_WORKSPACE`.
- Secret không ghi vào source; biến bí mật chỉ đi qua môi trường runtime.
- Build thành công chưa đồng nghĩa deploy thành công. Deploy chỉ được coi thành công khi healthcheck trả HTTP 2xx/3xx.
- Không mở public control-plane khi chưa có auth/TLS/RBAC.

## Chạy

```bash
cd LOCAL_BRIDGE/runtime/sol-deploy-platform
python -m sol_deploy.cli serve
```

Mặc định:
- điều khiển: `http://127.0.0.1:8788/`
- SQLite: `.runtime/sol-deploy.sqlite3`
- log tiến trình: `.runtime/logs/`

Có thể đổi:
- `SOL_DEPLOY_HOST`
- `SOL_DEPLOY_PORT`
- `SOL_DEPLOY_WORKSPACE`
- `SOL_DEPLOY_STATE_DIR`

## CLI — giao diện dòng lệnh

```bash
python -m sol_deploy.cli project-create demo ./demo
python -m sol_deploy.cli service-create <PROJECT_ID> web ./demo \
  --build "python -m compileall ." \
  --start "python app.py" \
  --health /health

python -m sol_deploy.cli build <SERVICE_ID>
python -m sol_deploy.cli deploy <SERVICE_ID>
python -m sol_deploy.cli logs <SERVICE_ID>
python -m sol_deploy.cli stop <SERVICE_ID>
python -m sol_deploy.cli redeploy <SERVICE_ID>
```

Runtime gán biến `PORT` cho service. Trong lệnh start có thể dùng placeholder `{port}`.

## API cục bộ

- `GET /api/health`
- `GET /api/projects`
- `GET /api/services`
- `POST /api/projects`
- `POST /api/services`
- `POST /api/services/<id>/build`
- `POST /api/services/<id>/deploy`
- `POST /api/services/<id>/stop`
- `POST /api/services/<id>/redeploy`
- `GET /api/services/<id>/logs`

## Kiểm thử

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

Bài kiểm thử dựng một ứng dụng HTTP thật trong thư mục tạm, chạy build, deploy, healthcheck, đọc endpoint rồi stop.
