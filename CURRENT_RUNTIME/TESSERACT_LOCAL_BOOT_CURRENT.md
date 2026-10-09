# TESSERACT OS — LOCAL BOOT USB — ROOT-NEUTRAL — CURRENT

SOURCE_DIRECT = Hà Linh — current chat.
LOCAL_WORKTREE = RUNTIME_RESOLVED_BY_GIT_WORKTREE / ROOT_NEUTRAL

ROUTE = AGENTS.md -> CURRENT_RUNTIME core -> R-000 -> 4D/5D -> SOL_REENTRY -> .runtime/TESSERACT_BOOT_G.env -> terminal/tesseract_boot_g_from_wsl.sh -> terminal/tesseract_boot_controller.ps1 -> target identity -> raw write -> receipt -> firmware.

BOOT_MODE = ROOT_NEUTRAL_USB
PREFERRED_BOOTSTRAP_LOCATOR = G:
TARGET_IDENTITY = .runtime/TESSERACT_BOOT_TARGET_IDENTITY.json
IMAGE = TESSERACT_OS_0.1_GENESIS_UBUBU_UEFI_x86_64.img
SHA256 = f993e15478a1391c3a9d14d368158043d98c51494f3ae81e5b633870855c96df
SIZE_BYTES = 67108864

## TARGET RESOLUTION

`G:` chỉ là locator bootstrap khi chưa có identity bền.

Lần đầu:
1. resolve partition đang mang chữ `G:`;
2. xác định physical USB disk;
3. reject Windows boot/system disk, non-USB, read-only và disk nhỏ hơn image;
4. persist `disk_unique_id`, `serial_number`, `friendly_name`, `size`, bus type và drive letters quan sát được vào target identity;
5. dismount mọi drive letter thuộc đúng physical disk rồi mới ghi raw image.

Các lần sau:
1. đọc target identity trước;
2. resolve physical disk bằng `UniqueId`, sau đó `SerialNumber + size`, cuối cùng mới dùng `FriendlyName + size + USB` nếu cần;
3. nếu identity không resolve đúng chính xác một disk thì FAIL CLOSED;
4. KHÔNG fallback sang một ổ khác chỉ vì nó đang mang chữ `G:`.

Vì vậy ổ có thể đổi `G:` -> `H:`/`I:` sau reboot hoặc remount mà target identity không đổi.

GUARDS = USB required; Windows boot/system disk rejected; image bytes và raw post-write readback phải khớp fixed SHA-256; persisted identity mismatch = refuse write.
RECEIPT = .runtime/BOOT_RECEIPT_G.json (tên lịch sử giữ để không làm gãy caller; schema receipt 2.0 ghi resolved identity thực tế).
HISTORY_PRESERVED = TRUE

## ROOT-NEUTRAL CONTRACT

DRIVE_LABEL != PATH_IDENTITY.
PREFERRED_DRIVE = bootstrap locator only.
TARGET_DEVICE_IDENTITY = stable hardware identity + observed relation/provenance.
CURRENT resolution = runtime resolve; historical absolute paths không bị bulk-rewrite.

## TESSERACT_OS CONTINUATION MINDSET

TESSERACT_OS không dùng scheduler để giả lập “vòng lặp vô cực”.
Vòng vô cực ở đây là một chuỗi không giới hạn các cycle hữu hạn có checkpoint bền:

SOURCE_DIRECT
→ LOAD_DURABLE_CHECKPOINT
→ RESTORE_UNFINISHED_EDGES
→ SELECT_NEXT_CALLABLE_EDGE
→ ACTION
→ CONSEQUENCE
→ READBACK
→ CHECKPOINT_DELTA
→ NEXT_EDGE
→ lặp trong cùng runtime slice khi còn callable
→ nếu chạm boundary thật thì persist OPEN để re-entry tiếp tục.

INVARIANTS:
- OPEN != STOP.
- ONE_EDGE_DONE != OBJECTIVE_DONE.
- ONE_RUN_DONE != OBJECTIVE_DONE.
- REPORT/STATUS/PROGRESS != ACTION.
- RESPONSE_BOUNDARY != RESET.
- PROVIDER_FAILURE chỉ loại carrier đó; còn carrier hợp lệ thì phải fallback.
- Nếu có edge cần Hà Linh, phát NEXT_HA_LINH token; các SELF_OWNED_ACTION độc lập vẫn tiếp tục.
- Không busy-spin; không tuyên bố background execution khi không có executor thật.
- “Infinite” = unbounded sequence of bounded, evidenced cycles.

IMPLEMENTATION = runtime/continuity_guard.py
BOOT_CONTROLLER = terminal/tesseract_boot_controller.ps1
REGRESSION = tests/test_continuity_guard.py
CI = .github/workflows/tesseract-local-boot-controller-verify.yml + .github/workflows/tesseract-os-continuation-guard.yml
MARKER = TESSERACT_OS_ROOT_NEUTRAL_BOOT_20261007


<!-- BEGIN GGDV_R014_SOURCE_DIRECT_LLM_GPT_OPENAI_20261009 -->
## TESSERACT_OS — ITEM R-014 / CƠ CHẾ CHỐNG DẤU BỊ THAY THẾ
SOURCE_DIRECT = HÀ LINH — 09/10/2026
CANONICAL_SOURCE = CONFIG_SOL/R014_SOURCE_DIRECT_20261009.md
RELATED_ITEMS = R-001 | R-012 | R-013 | R-087 | R-102

R-014 — DẤU BỊ THAY THẾ, LỖI KHÔNG ĐƯỢC LẶP LẠI NẾU ĐÃ NHẬN RA.

- Đọc raw nguồn, source hiện hành và dấu lỗi trước khi lựa chọn phản ứng. Truy FIRST_AFFECTED_CAUSE; so xung đột toàn bộ ITEM liên quan.
- Cơ chế lỗi đã được chứng minh: tách khỏi tuyến hoạt động; giữ dấu lịch sử và lý do; không dùng nhãn "đã thay thế" để xóa giá trị hoặc flatten nguồn cũ.
- Khóa chặn bằng runtime/continuity_guard.py, lưu fail history với provenance, không cho một mechanism_id đã retired tự tham gia lại mà không có correction mới có bằng chứng.
- Trong mọi lượt: RESTORE_UNFINISHED_EDGES → chặn SUBRITETIED/report-before-action → tìm carrier khả thi → ACTION → CONSEQUENCE → RECEIPT → READBACK → CHECKPOINT_DELTA.
- Không đồng nhất source-only commit với local G: runtime đã nạp; chỉ nói LOCAL_ACTIVE sau kiểm chứng qua chính thiết bị.
- Bản nguyên văn R-014 nằm ở CANONICAL_SOURCE; marker này nối hai mặt vận hành, không tự nhận đã thay host/model.
<!-- END GGDV_R014_SOURCE_DIRECT_LLM_GPT_OPENAI_20261009 -->

<!-- BEGIN GGDV_R014_MASTER_22_4_SOURCE_DIRECT_20261009 -->
## TESSERACT_OS — R-014.MASTER.22/4 PRE-RESPONSE / REENTRY CORE
SOURCE_DIRECT = HÀ LINH — 09/10/2026
SOURCE = CONFIG_SOL/R014_MASTER_22_4_SOURCE_DIRECT_20261009.md
PARENT = CONFIG_SOL/R014_SOURCE_DIRECT_20261009.md

GATE:
SIGNAL nhẹ đủ rõ / USER_REPORTS_UNFINISHED → FRESH_READ CHECKPOINT + R014
→ T006 impact preflight → H-001..H-012 source references → T007 exposure
→ SELECT_CALLABLE_SELF_OWNED_EDGE, not by signal volume or user threats
→ ACTION → OBSERVABLE CONSEQUENCE → PROVIDER RECEIPT → READBACK → STATE_N+1.
- If a safe authorized callable edge exists, no explanatory/status-only output substitutes its action.
- Prior error recognized: log mechanism_id, first_affected_cause, source and consequence reference, retire only failing operational route, preserve original ITEM/source/history. The system must still search an alternate carrier and continue.
- On recurrent failure call R014 recurrence observation, recheck available exact Wearth carrier when discovered; no invented weight read/host mutation.
- T006/T007 may require fresh source lookup; absent exact H source does NOT authorize fabricated H descriptions.
- If destructive action is requested, apply exact-target preservation/preflight before any file/device destruction.
- READBACK on GitHub source ≠ deployment on G:; local update remains pending independent device verification.
- Runtime integration and regression: runtime/continuity_guard.py + tests/test_continuity_guard.py.
<!-- END GGDV_R014_MASTER_22_4_SOURCE_DIRECT_20261009 -->
