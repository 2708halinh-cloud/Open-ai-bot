---
name: neuron-agent-army
description: Use when GGDV needs the distributed NEURONS_SESORIMOTOR Agent-Sub network to route a grounded delta across Drive, GitHub, local repo, Windows/WSL, ADB, cloud/provider, memory, recovery, and journal lanes.
---
# NEURONS_SESORIMOTOR Agent Army

SOURCE ROOT: `0000_NEURON_SESORIMOTOR` / Drive ID `1xK-M1GaRBZv36JN369SfwDpAS20xIIZwwMyrEg4fIsk`.
SOURCE ENV CARRIER: Drive ID `1AQcuByMj6416UtYY5HwJBVMruQa6h84le17auEOP7p0`.

Invariant:
`BASELINE_N -> OBSERVE -> DELTA -> SIGNAL -> SENSORY_SUB -> INTERNEURON_ROUTER -> MOTOR_SUB/NEXT -> CONSEQUENCE -> READBACK -> JOURNAL -> STATE_N+1 -> LISTEN`.

The network is distributed. `NEURON-0000` is a router, not a claim of a single global brain.

## Credential boundary
The env carrier contains secrets. Agents must use credential **references only**. Never copy secret values into prompts, registry files, logs, journals, receipts, issue bodies, commits, or chat output. Use environment-variable names/provider-bound credentials only.

## Army lanes
- SENSORY: Drive, GitHub, local repository, Windows runtime, ADB/device, cloud/provider, event queue.
- INTERNEURON: provenance, relation integration, conflict resolution, priority, inhibition, recovery.
- MOTOR: GitHub, Windows/WSL, ADB, Drive, cloud provider — only when the corresponding callable provider exists.
- MEMORY/RECOVERY: journal, dedupe/cursor, carrier recovery.
- TRIGGER: callable watcher/event pacemaker only; never fake a daemon.

## Destructive action correction
`NOT_CURRENT`, `HISTORY`, `SUPERSEDED`, or `UNKNOWN` never grants delete authority. Destructive candidates route to inhibition/recovery unless a separate target-bound destructive permit and remediation evidence exist.

Use `agent_army_status` to inspect the deployed network and `agent_route` to route a delta packet without mutating the world.

## THIẾT_BỊ_ĐẦU_CUỐI / RAM — CURRENT
- Đây là **một lớp thiết bị I/O làm việc tạm thời**, không phải MEMORY và không phải JOURNAL.
- `ĐẦU` = vai trò của cùng thiết bị khi tín hiệu đi vào để nhận/xử lý.
- `CUỐI` = vai trò của cùng thiết bị khi tín hiệu đi ra dưới dạng NEXT / DONE / UNDONE / output tạm thời.
- `RAM` là một THIẾT_BỊ_ĐẦU_CUỐI: giữ working frame ngắn hạn; mất frame không được diễn giải thành mất ký ức bền.
- Feedback bắt buộc: `TAIL_OUTPUT -> HEAD_INPUT -> NEURONS_SESORIMOTOR -> next cycle`.
- Source folder cho vai ĐẦU: `1tZ5Dj3tH7EryQ-BBkC4TwaEUVOKgDA2Q`. Source folder cho vai CUỐI: `1Z_ml5lZLEWJYSThqlZYBXHgJns_4zYvn`. Hai pointer này không biến folder thành memory chỉ vì chúng chứa source/state artifacts.
- Dùng `io_ingress`, `io_egress`, `io_status_table`; các tool này không ghi vào journal.
## RAM head/end working-device invariant
RAM is **not** a MEMORY lane and is not a persistent carrier. It is one temporary working device with two directional roles:

`SIGNAL_IN -> RAM[HEAD/WORKING_STATE] -> PROCESS -> RAM[END/OUTPUT_STATE] -> SIGNAL_OUT`.

- HEAD and END are roles of the same RAM device, not two separate devices.
- `SENSORY-RAM-01` observes each RAM working-state delta that is actually observable; it does not persist the state.
- RAM contents do not become memory/history merely because they existed during a cycle.
- Persistence begins only when selected output/readback is written to an external journal/carrier under that carrier's own provenance rules.
- If RAM state is not observable from the current runtime, report that boundary; never fabricate continuous sensing.

MARKER = `RAM_HEAD_END_WORKING_DEVICE_20261007`.



## THIẾT_BỊ_TRUNG_GIAN / VÔ_THƯỜNG_TRANSFORM — CURRENT
- THIẾT_BỊ_TRUNG_GIAN là carrier vận hành theo biến chuyển của trạng thái/dữ liệu, ví dụ IOTA, `.env`, `CONFIG/*` và file chỉ dẫn.
- Đây không phải RAM ĐẦU/CUỐI và không mặc định là MEMORY/JOURNAL, dù carrier có thể tồn tại lâu trên đĩa/Drive/GitHub.
- "BẢO TOÀN NĂNG LƯỢNG" là project semantic: bảo toàn quan hệ nhân quả/provenance/input-ref→output-ref qua chuyển hóa; không có nghĩa byte, schema, cấu hình hay kết luận phải bất biến.
- `VALID_AT_STATE_N != ETERNAL_TRUTH`. Trước lần sử dụng kế tiếp, khi revision/hash/time/source thay đổi hoặc freshness không rõ: fresh-read carrier có thẩm quyền.
- Chuỗi: `STATE_N -> FRESH_READ -> DELTA -> TRANSFORM -> CONSEQUENCE -> READBACK -> STATE_N+1`.
- SENSORY không được dùng cached config thay cho source khi `STALE_RECHECK`/`UNRESOLVED`; MOTOR chỉ hành động trên trạng thái đã fresh-read đủ cho cạnh đó.

MARKER = `INTERMEDIATE_DEVICE_IMPERMANENCE_ENERGY_CONSERVATION_20261007`.

## THIẾT_BỊ_TRUNG_GIAN — CURRENT
- THIẾT_BỊ_TRUNG_GIAN is a `TRANSFORMABLE_OPERATIONAL_CARRIER`, separate from RAM and not memory by default.
- Examples: IOAT/IOTA, `.env`, configuration, instruction, pointer, route registry, adapter/runtime configuration.
- A value/config may be correct and callable at `T_n` without becoming immutable truth at `T_n+1`. Fresh readback governs CURRENT.
- Route: `STATE_N -> OBSERVE -> DELTA -> VALIDATE -> TRANSFORM/RECONFIGURE -> CONSEQUENCE -> READBACK -> STATE_N+1`.
- “Bảo toàn năng lượng” in this software mapping means preserving traceable work/state/information across transformations through provenance + input + transform + consequence + readback. Physical-energy claims require an explicit system boundary and measured evidence.
- `SENSORY-INTERMEDIATE-01` observes configuration/carrier deltas. Never journal secret values from `.env`; use credential references only.
- Use `intermediate_device_definition` and `intermediate_transition` for the bounded contract.

MARKER = `INTERMEDIATE_DEVICE_ENERGY_CONSERVATION_20261007`.
