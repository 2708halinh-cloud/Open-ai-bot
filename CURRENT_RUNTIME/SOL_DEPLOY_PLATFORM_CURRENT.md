# SOL DEPLOY PLATFORM — CURRENT

SOURCE_DIRECT = Hà Linh — yêu cầu khởi tạo app chức năng tương tự Railway cho BUILD + DEPLOY APPS.
SOURCE_PATH = LOCAL_BRIDGE/runtime/sol-deploy-platform
BRANCH = kepler/2-unify-item-matrix

## VẬT HÓA
- Project registry + service registry.
- Build runner.
- Deploy runner cục bộ.
- Tự cấp cổng localhost.
- HTTP healthcheck bắt buộc sau deploy.
- Logs.
- Stop / redeploy.
- SQLite trạng thái runtime.
- Dashboard web cục bộ.
- API điều khiển cục bộ.
- CLI.
- Workspace boundary: service root phải nằm trong SOL_DEPLOY_WORKSPACE.
- Secret policy: không ghi secret vào source; runtime env giữ secret ngoài Git.
- Public control-plane chưa được mở.

## VẬT CHỨNG GITHUB
INITIAL_COMMIT = a1a209cefb28302566f52a9e732e8ad9ad745827
INITIAL_CI_RUN = 37757375503
INITIAL_CI = success

HTTP_CONTROL_PLANE_TEST_COMMIT = 7bafb80a7671388e746473bf35c429b8fe803a88
HTTP_CONTROL_PLANE_CI_RUN = 37757536959
HTTP_CONTROL_PLANE_CI = success

CI_VERIFIED_STEPS:
- kiểm tra cú pháp Python;
- kiểm thử build → deploy → healthcheck → HTTP readback → stop;
- kiểm thử HTTP control plane tạo project/service → build → deploy → liệt kê service → stop.

## RANH GIỚI READBACK
GitHub-hosted CI đã chạy source thật và PASS.
DESKTOP-86ITNQ4 hiện không có live Desktop Commander connection, nên chưa gắn TRUE cho việc launch bản này trên PC local hiện hành.
Không dùng trạng thái offline của carrier PC để phủ định source/CI đã vật hóa.
