---
name: destructive-action-gate
description: Use before any irreversible delete, overwrite, purge, disk cleanup, destructive git reset/clean, or equivalent GGDV MOTOR action.
---
# Destructive Action Gate

Core invariant: **SAI → SỬA; LỖI → CÙNG KHẮC PHỤC; chỉ khi không thể giữ sự thật mới xét DELETE.**

`NOT_CURRENT != FALSE != USELESS != DELETE_AUTHORITY`.

Before a destructive MOTOR action:
1. identify the exact target and snapshot its current identity/provenance;
2. distinguish CURRENT, HISTORY, SUPERSEDED, duplicate, corrupted, and unrelated states without flattening them;
3. attempt the smallest repair/re-parent/archive/correction path first;
4. record why repair cannot preserve the truth or required state;
5. require exact target confirmation;
6. request `destructive_preflight` for the exact command;
7. use the one-use permit only for that exact command;
8. observe the consequence and journal it.

A label such as NOT_CURRENT, HISTORY, SUPERSEDED, OLD, DUPLICATE, CACHE, COPY, or WRONG_PARENT never authorizes deletion by itself.

`GGDV_MOTOR_ENABLE=1` does not unlock destructive operations. The local host must separately set `GGDV_DESTRUCTIVE_ENABLE=1`, and the exact operation still needs a valid one-use permit.
