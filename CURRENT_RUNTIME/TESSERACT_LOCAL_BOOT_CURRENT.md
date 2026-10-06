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
