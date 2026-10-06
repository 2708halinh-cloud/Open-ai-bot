# TESSERACT OS — LOCAL BOOT G: — CURRENT

SOURCE_DIRECT = Hà Linh — current chat.
LOCAL_WORKTREE = /home/halin/kepler/worktrees/Open-ai-bot-2-unify-item-matrix-34d45d00

ROUTE = AGENTS.md -> CURRENT_RUNTIME core -> R-000 -> 4D/5D -> SOL_REENTRY -> .runtime/TESSERACT_BOOT_G.env -> terminal/tesseract_boot_g_from_wsl.sh -> receipt -> firmware.

TARGET = G:
IMAGE = TESSERACT_OS_0.1_GENESIS_UBUBU_UEFI_x86_64.img
SHA256 = f993e15478a1391c3a9d14d368158043d98c51494f3ae81e5b633870855c96df
SIZE_BYTES = 67108864

GUARDS = target G only; backing device must be USB; Windows boot/system disk rejected; image bytes and post-write readback must match the fixed SHA-256.
RECEIPT = .runtime/BOOT_RECEIPT_G.json
HISTORY_PRESERVED = TRUE


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
REGRESSION = tests/test_continuity_guard.py
CI = .github/workflows/tesseract-os-continuation-guard.yml
MARKER = TESSERACT_OS_CONTINUATION_GUARD_20261007
