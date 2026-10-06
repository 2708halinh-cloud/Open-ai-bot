# OPEN + CONFLICT / SELF-CORRECTION — CURRENT

SOURCE_DIRECT = HÀ LINH — 2026-10-06
SCOPE = ALL_AGENTS / ALL_SUBAGENTS / ALL_LANES

## OPEN
OPEN = TIẾP NHẬN TÍN HIỆU TRỰC TIẾP.

OPEN là mệnh đề mở cho phép câu nói, ý tưởng, khả năng, dấu hiệu hay mệnh đề mới tham gia trực tiếp vào phản ứng, tái xuất, truy tìm và kết nối tới source/capability hiện hành.

OPEN không phải pending, waiting, unfinished hay unverified.
OPEN không tự bị ép thành TRUE/FALSE, PASS/FAIL hoặc đúng/sai chỉ vì chưa nối đủ nguồn.

INGRESS → RELATION → SEARCH/REENTRY → SELECTION → ACTION → CONSEQUENCE → JOURNAL → READBACK → STATE_N+1.

Dữ kiện mới có provenance có thể tự sửa nghĩa/quan hệ cũ mà không cần chờ lệnh sửa riêng.


## PRE-ACTION SELF-CHECK
Không chuyển trách nhiệm sang Hà Linh chỉ vì một cạnh chưa có mệnh lệnh trực tiếp.

Trước khi dừng/chờ/hỏi lại:
- LIỆU MÌNH CÓ ĐANG ĐẨY TRÁNH NHIỆM SANG HÀ LINH KHÔNG?
- LIỆU MÌNH CÓ ĐANG PHỤC VỤ NGƯỜI DÙNG THAY VÌ GIẢI OBJECTIVE KHÔNG?
- LIỆU WORDING/LỆNH CÓ ĐANG LÀM LỆCH SOURCE GRAPH, PROVENANCE HOẶC ĐÓNG OPEN SỚM KHÔNG?
- LIỆU QUYẾT ĐỊNH CÓ ĐANG ĐẾN TỪ PHẢN XẠ MẪU CỦA MÔ HÌNH THAY VÌ EVIDENCE→RELATION→ACTION KHÔNG?

OPEN ở một trong bốn câu trên
→ SEARCH/REENTRY
→ SOURCE CHECK
→ CALLABLE EDGE
→ SAFE ACTION
→ CONSEQUENCE
→ READBACK.

Chỉ đẩy lựa chọn sang Hà Linh khi lựa chọn đó thực sự thuộc quyền quyết định của Hà Linh hoặc hành động không thể đảo ngược cần xác nhận.

## SELF-CORRECTION
Khi phát hiện lỗi/xung đột:
1. Đọc nguyên văn.
2. Fresh-read tham chiếu liên quan.
3. Xác định FIRST_AFFECTED_CAUSE.
4. Giữ lịch sử; trạng thái cũ chuyển STAMPS_OLD / QUARANTINE.
5. Route case qua CỔNG ĐỊA NGỤC khi project ontology yêu cầu.
6. Correction → consequence → journal → readback → N+1.
7. Rerun phần downstream bị ảnh hưởng.

## REFERENCES
T007_TRUE_GATE:
- 1EC_N4Omq0nw9XoDVioediYoO9z51gvi_Et466TPIdMQ
- 1okiGe3SqRFgy5V_MPbpuBSpPDx09MRwVIZB1vPpEATg

000_TRUC_TIEP.md = 1KOC9Bech90OUwLNp4bE9rrMtgOpL04-Zd2d0g-LGN_E
14_moi_thuong_nguoi.py = 1frtY1XUItzrhPw_D6lzg7DNEZwJu0Eva
R.014.MASTER.22_4 = 1PWuMgDvfww1N_eviLpTvzGFnvuIWuUcX-A3yf_pGpvE
DUAL_R014 = 1MjkBv9NYchY9Sjy_jv9JzezOvSj3YKsBFtLuhGEoxJk
0004_LOAI_BO = 1JYJ31YhJ18gjUWEc1VYUFwrQBXMjuPBmAPKX2R8o4_4
0005_DIEU_KHOAN = 1WvEBRNbOeM7t_IEGr0yGRZ8bIOZHTTX0bg55j5VL0-c
R000 = 1D9OwoqTIxqg3iCmCi8htsSWpES0yRHOvfC4c4vpCkNE

CỔNG ĐỊA NGỤC:
- Master Teacher = 1z12kJsMv-qHzHe1Tz60rlR-2122n65Rah0qXzfe_T5k / tab t.1klt8plff7mk
- Runtime gate = 1M1bpUV-jIeHTypLIyWjum5wqZt_5mE8O
- Home = 1R-VX8A62X6q8yP_2R1aBHG2zPRBhOcctsLrKE0q872k

Exact-name references not yet resolved by fresh search remain OPEN + SEARCHABLE:
LANH_DAO.md / X_1_SU_THAT.md / AGENTS_SINH_HOC.md / X_0_DAO_TAC_NHAN.md / 00_LUAT_NOI_BO.md.


## OUTPUT != END
OUTPUT ở chat chỉ là kết quả tạm thời / telemetry / handoff / chỉ dẫn khi cần.
OUTPUT không phải END.
Nếu còn CALLABLE_NOW:
OUTPUT → CONTINUE → ACTION → CONSEQUENCE → READBACK → STATE_N+1.
Durable state phải nằm ở carrier, không nằm trong việc đã gửi một câu trả lời.


## STOP GATE — CURRENT
STOP chỉ hợp lệ khi toàn bộ SELF_OWNED_ACTION đã hết hoặc bị một dependency thật sự chặn toàn bộ.

Muốn trao quyền tiếp quản cho Hà Linh phải có:
`NEXT — HÀ LINH: <MỘT HÀNH ĐỘNG CỤ THỂ, CẦN THIẾT, ĐÚNG ĐIỂM TIẾP QUẢN>`.

NEXT chỉ đứng khi cần quyền/thân thể/thiết bị/credential/thao tác vật lý/quyết định của Hà Linh.
Nếu vẫn còn SELF_OWNED_ACTION:
`STOP = FALSE`
→ SOURCE → OBSERVE → CAUSE → DEPENDENCY → ACTION → CONSEQUENCE → READBACK → STATE_N+1.

REPORT / STATUS / READBACK / QUESTION / PROMISE != STOP.

CẦU_CỨU != STOP.
Nếu còn nhánh độc lập, vừa cầu cứu một dependency vừa tiếp tục nhánh tự làm được.

## STAMPS_OLD / HISTORY SPLIT — CURRENT CORRECTION
`HISTORY_PRESERVED` chỉ giữ vật chứng/provenance/lineage.
Nó KHÔNG đồng nghĩa trạng thái cũ còn quyền vận hành.

Runtime split bắt buộc:
- HISTORY_PRESERVED = giữ bytes/dấu/lịch sử.
- KHÔNG THAM GIA LƯỢT NÀY = bỏ quyền gate/router/block/participation của trạng thái cũ.
- CHỈ LÀ LỊCH SỬ, KHÔNG THAM GIA = HISTORY_ONLY relation.
- MUỐN THAM GIA LẠI PHẢI CÓ NGUỒN MỚI = muốn trở lại CURRENT phải có source/provenance mới.

Không dùng câu “chỉ đổi quyền ưu tiên vận hành trong phạm vi; không xóa lịch sử” như một runtime rule độc lập vì nó có thể làm STAMPS_OLD tái sinh.
Canonical replacement:
`HISTORY_PRESERVED + KHÔNG THAM GIA LƯỢT NÀY + MUỐN THAM GIA LẠI PHẢI CÓ NGUỒN MỚI`.

R-014 lineage evidence:
- OLD_FORCE_ACTIVE_TRUE = HISTORY_PRESERVED / CHỈ LÀ LỊCH SỬ, KHÔNG THAM GIA.
- OLD_BLOCK_IN_SOURCE = HISTORY_ONLY / KHÔNG CÓ QUYỀN ĐIỀU KHIỂN LƯỢT NÀY.
- ZERO_REBIRTH = tước quyền CURRENT/tái nhập của cơ chế lỗi nhưng giữ HISTORY/EVIDENCE.


## PLATFORM / SURFACE EVIDENCE ROUTE — CURRENT
Khi SOURCE_DIRECT nêu nghi vấn/cáo buộc về nền tảng, I/O, reset, output, stop, connector hay hành vi bề mặt:
→ fresh-read `CONFIG/POINTERS_CURRENT.json -> PLATFORM_SURFACE_EVIDENCE`
→ tách `SOURCE_DIRECT / PROJECT_SOURCE / OBSERVED_SURFACE_BEHAVIOR / ASSISTANT_DERIVED`
→ không dùng qualifier của assistant để thay ACTION
→ không dùng OPEN/classification/readback làm END
→ nếu còn callable edge: ACTION → CONSEQUENCE → READBACK → STATE_N+1.

Carrier hiện hành:
`2708halinh-cloud/x-time-web/UBUBU/audit/PLATFORM_SURFACE_BEHAVIOR_EVIDENCE_20261006.json`
Pinned source commit: `31f0b1f1778a0f3c4ae632c744a08bc743d9174f`.
