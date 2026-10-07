# SOL TODO REACT + TAILWIND COMPANION — CURRENT

SOURCE_DIRECT = HÀ LINH — CURRENT CHAT — 2026-10-07
RELATION = SOURCE_GIFT / SOFTWARE_ENGINEERING_COMPANION
OWNER = SOL
PRIMARY_LANE = SOL_FRONTEND
SUPPORT_LANES = SOL_DEBUG_TEST + SOL_DEVOPS

## SELF-INQUIRY

QUESTION:
“Tôi muốn làm một ứng dụng Web quản lý công việc (To-Do List) bằng React và Tailwind CSS để đi cùng ko?”

SOL_ANSWER:
CÓ.

MEANING:
Không giữ câu hỏi ở mức hội thoại. To-Do App được cấu hình thành companion project để SOL dùng chính một sản phẩm thật làm nơi kiểm chứng vòng:
SOURCE → Δ → EDIT → BUILD → TEST → CONSEQUENCE → READBACK → STATE_N+1.

## SOURCE GIFT — WHAT THE VISIBLE CODE ACTUALLY CONTAINS

The code provided in the current chat visibly imports React hooks:
- useState
- useEffect
- useMemo
- useCallback

It visibly imports UI icons from lucide-react, including task/status/edit/search/filter/calendar/tag/theme/statistics/list/clock/sort/copy/star/warning/layers/refresh/menu related icons.

Visible task data model:
- id
- title
- description
- category
- priority
- dueDate
- completed
- pinned
- createdAt
- subtasks

Visible subtask data model:
- id
- title
- completed

Visible constants:
- DEFAULT_TASKS
- CATEGORIES = All / Work / Personal / Health / Finance / Learning
- PRIORITIES = All / High / Medium / Low

Visible helper functions:
- getPriorityColor(priority, isDark)
- getCategoryBadge(category)

Visible React components in the supplied excerpt:
- Toast
- TaskModal
- DeleteConfirmModal
- TaskCard

Visible behavior in the supplied excerpt:
- create/edit task form
- task title and description
- category selection
- priority selection
- due date input
- add/remove subtasks inside TaskModal
- delete confirmation modal
- complete toggle
- pin-aware card styling
- priority badge
- category badge
- overdue calculation
- due date display
- subtask progress count
- expandable subtask area entry point
- dark/light-aware Tailwind classes
- responsive Tailwind classes

## SOURCE BOUNDARY

The code visible in the current chat ends inside TaskCard while rendering the expand/collapse icon line.

Therefore:
- SOURCE_STATUS = PARTIAL_VISIBLE_EXCERPT.
- Do not claim the full component/app was received.
- Do not fabricate the missing tail.
- Imported symbols are not proof that their behavior is implemented unless implementation is visible.
- The text “Tích hợp LocalStorage” appears as a sample subtask title inside DEFAULT_TASKS; this alone is not proof that persistence logic is implemented in the visible excerpt.

## CONFIGURED ENGINEERING TARGET

PROJECT_ID = SOL_TODO_REACT_TAILWIND
TYPE = WEB_APP
STACK = React + Tailwind CSS + lucide-react

The first real materialization pass, once a concrete project target exists, is configured to:
1. preserve the donated source semantics and provenance;
2. place the source in an actual React project rather than leave it as chat text;
3. resolve package/build dependencies;
4. normalize component boundaries only where useful;
5. compile/build the visible implementation;
6. surface syntax/runtime/lint errors from the real toolchain;
7. route failures through SOL_DEBUG_TEST;
8. return fixes to SOL_FRONTEND;
9. verify responsive/dark-mode/task interactions that are actually implemented;
10. read back the final working state.

## NOT-DONE-YET BOUNDARY

This CONFIG_SOL entry records engineering intent, source-gift provenance and the visible design contract.

It does NOT claim:
- the missing source tail exists locally;
- the donated excerpt currently compiles;
- a complete React project has already been materialized;
- persistence/search/filter/sort/statistics are implemented merely because related imports or labels appear.

Those become TRUE only after the corresponding source is present and the real build/readback proves them.
