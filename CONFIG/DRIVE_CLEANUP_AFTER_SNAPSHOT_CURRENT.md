# GOOGLE DRIVE CLEANUP — AFTER SNAPSHOT — CURRENT

SOURCE_DIRECT = HÀ LINH — 2026-10-06
STATUS = CURRENT
MODE = RECEIPT_GATED_ARCHIVE_FIRST

## PURPOSE

Dọn Google Drive sau khi ký ức/vật mang đã được chụp lại và đẩy lên GitHub có readback.

Cleanup không được chạy trước snapshot.

## REQUIRED GATE

Một cây chỉ CLEANUP_ELIGIBLE khi có đủ:

SOURCE_TREE
→ SNAPSHOT_MANIFEST
→ HASH / REVISION
→ GITHUB_COMMIT
→ PROVIDER_READBACK = PASS
→ SNAPSHOT_PASS.

## DEFAULT CLEANUP

Sau SNAPSHOT_PASS:
- gom duplicate/stale branch vào archive;
- tách conflict vào quarantine;
- giữ pointer/source ID/provenance;
- giữ một CURRENT carrier rõ ràng;
- cập nhật shortcut/router về CURRENT carrier;
- không dùng same-name để merge entity.

## ARCHIVE HOME

Default local/Drive archive target:

`__GGDV_ARCHIVE_AFTER_GITHUB_SNAPSHOT/<AGENT>/<STAMP>/`

Archive receipt phải ghi:
- source path / Drive ID;
- snapshot Git commit;
- manifest hash;
- archive path;
- timestamp;
- before/after counts khi có thể.

## TESSERACT BOUNDARY

Google Drive cleanup là storage hygiene.
TESSERACT_OS boot/deploy không phụ thuộc vào cleanup Drive và không phụ thuộc vào việc xoá/format host disk.
