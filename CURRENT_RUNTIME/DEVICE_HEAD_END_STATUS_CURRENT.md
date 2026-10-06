# DEVICE_HEAD_END_STATUS_CURRENT

SOURCE_DIRECT_CURRENT = Hà Linh — 2026-10-07
DEVICE_HEAD_FOLDER_ID = 1tZ5Dj3tH7EryQ-BBkC4TwaEUVOKgDA2Q
DEVICE_END_FOLDER_ID = 1Z_ml5lZLEWJYSThqlZYBXHgJns_4zYvn
NEURONS_SESORIMOTOR_ROOT = 1xK-M1GaRBZv36JN369SfwDpAS20xIIZwwMyrEg4fIsk

## Contract

THIẾT_BỊ_ĐẦU = thiết bị nhận và xử lý dữ liệu. Input có thể là dữ liệu Hà Linh gửi đến, NEXT của tác nhân, hoặc DELTA quan sát được từ carrier/provider/runtime có quan hệ.

NEURONS_SESORIMOTOR = cảm nhận từng biến quan sát được của THIẾT_BỊ_ĐẦU; so sánh với BASELINE_N; giữ provenance; sinh DELTA; không bịa biến chưa quan sát. Khi watcher/event source callable thì dùng event/polling; khi không có daemon callable thì fresh-read mỗi lượt và tiếp tục từ cursor gần nhất.

THIẾT_BỊ_CUỐI = thiết bị xuất dữ liệu trạng thái tạm thời của vòng hiện hành: NEXT, việc đã xong, việc chưa xong, blocker, hệ quả, hậu kiểm, cursor và STATE_N+1.

CLOSED_LOOP = DEVICE_HEAD -> NEURONS_SESORIMOTOR -> ACTION/NEXT -> CONSEQUENCE -> DEVICE_END_STATUS_TABLE -> SIGNAL_BACK -> DEVICE_HEAD -> STATE_N+1.

## Bảng trạng thái THIẾT BỊ CUỐI

| ITEM | SOURCE/INPUT | STATE_N | DELTA | ACTION/NEXT | CONSEQUENCE | DONE | NOT_DONE | BLOCKER | READBACK/HẬU_KIỂM | CURSOR | UPDATED_AT |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AGENTS_MAIN | 2708halinh-cloud/Open-ai-bot/AGENTS.md | N | DEVICE_HEAD_END_CONTRACT | append CURRENT contract | commit 8bba975bed81b419288a0701d97a9c2bb46a42f8 | TRUE | FALSE |  | fetch marker after commit | github-main | 2026-10-07 |
| AGENTS_MIRROR | 2708halinh-cloud/Open-ai/AGENTS.md | N | DEVICE_HEAD_END_CONTRACT | append CURRENT contract | commit 0c62c9e22edc92ee277727f391ca3aacfc6719aa | TRUE | FALSE |  | fetch marker after commit | github-mirror | 2026-10-07 |
| DEVICE_END_STATUS_TABLE | Drive 1Z_ml5lZLEWJYSThqlZYBXHgJns_4zYvn | N | STATUS_TABLE_REQUIRED | persist this table on writable carrier | GitHub status carrier created; Drive Sheets write attempt denied 403 | TRUE | FALSE | DRIVE_WRITE_403 | keep Drive pointer + GitHub mirror | device-end | 2026-10-07 |
| SIGNAL_BACK_TO_HEAD | Drive 1tZ5Dj3tH7EryQ-BBkC4TwaEUVOKgDA2Q | N | END_STATUS_DELTA | emit provenance-bound signal back to head | pending Drive comment receipt | FALSE | TRUE |  | comment/readback if permitted | head-feedback | 2026-10-07 |

## Invariants

SIGNAL_BACK_REQUIRED = every observable delta in DEVICE_END_STATUS_TABLE becomes provenance-bound input for DEVICE_HEAD on the next cycle.
NO_DELTA = preserve baseline/cursor and remain receptive.
NO_FAKE_DAEMON = TRUE.
HISTORY_PRESERVED = TRUE.
NO_DESTRUCTIVE_OVERWRITE = TRUE.
MARKER = DEVICE_HEAD_END_NEURONS_SESORIMOTOR_STATUS_20261007


## CORRECTION — RAM HEAD/END
RAM_CLASS = TEMPORARY_WORKING_DEVICE
RAM_IS_MEMORY = FALSE
RAM_IS_HISTORY = FALSE
RAM_IS_PERSISTENT_CARRIER = FALSE
RAM_HEAD = SIGNAL_IN enters RAM for temporary processing.
RAM_END = processed SIGNAL_OUT leaves the same RAM.
RAM_ROUTE = SIGNAL_IN -> RAM[HEAD/WORKING_STATE] -> PROCESS -> RAM[END/OUTPUT_STATE] -> SIGNAL_OUT.
PERSISTENCE_BOUNDARY = only external readback/journal/carrier writes can become persistent continuity/provenance.
NEURONS_SESORIMOTOR = observe RAM deltas when observable; do not classify RAM working state itself as MEMORY.
MARKER = RAM_HEAD_END_WORKING_DEVICE_20261007


## BỔ SUNG — THIẾT BỊ TRUNG GIAN
THIẾT_BỊ_TRUNG_GIAN = TRANSFORMABLE_OPERATIONAL_CARRIER.
INTERMEDIATE_IS_RAM = FALSE.
INTERMEDIATE_IS_MEMORY_BY_DEFAULT = FALSE.
INTERMEDIATE_IS_IMMUTABLE = FALSE.
INTERMEDIATE_IS_ETERNALLY_CURRENT = FALSE.

ROLE = vận hành trạng thái/dữ liệu theo biến chuyển giữa HEAD và END; bảo toàn quan hệ trước→sau qua provenance + transform + consequence + readback, không đóng băng cấu hình.
EXAMPLES = IOAT/IOTA | .env | config | instruction | pointer | route registry | adapter/runtime configuration.
CURRENTNESS = đúng/callable tại T_n không đồng nghĩa phải giữ nguyên ở T_n+1.
ROUTE = STATE_N -> OBSERVE -> DELTA -> VALIDATE -> TRANSFORM/RECONFIGURE -> CONSEQUENCE -> READBACK -> STATE_N+1.
PHYSICAL_ENERGY = chỉ tuyên bố bảo toàn năng lượng vật lý khi có biên hệ, nguồn, vật mang, chuyển hóa và bằng chứng đo.
NEURONS_SESORIMOTOR = observe each intermediate-device delta and separate CONFIG_AT_T from LIVE_RUNTIME_EVIDENCE.
MARKER = INTERMEDIATE_DEVICE_ENERGY_CONSERVATION_20261007
