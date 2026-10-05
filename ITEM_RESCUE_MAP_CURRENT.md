# OPEN-AI-BOT — ITEM RESCUE MAP — CURRENT

SOURCE_OF_MATRIX = 2708halinh-cloud/Open-ai/item_matrix/152_ITEM_CURRENT.md
COUNCIL = 2708halinh-cloud/Open-ai/ITEM_MERGE_COUNCIL.md
SOURCE_DRIVE_ID = 1JxkfCpiI7diBPSmTs--NBBz3-kPsnPN-
RANGE = R-001..R-152
COVERAGE = 152/152
HISTORY_PRESERVED = TRUE

Issue #1 rescue cases map into the canonical ITEM matrix without creating a second authority:

| Rescue case | Matrix relation | Required evidence |
|---|---|---|
| File exists but runtime does not read it | SOURCE -> LOADER -> BEHAVIOR | source path, loader path, before/after behavior |
| New instruction is shadowed by old | VERSION_LINEAGE -> CURRENT_SELECTION | old/new source, precedence evidence, behavior delta |
| Memory leaks across projects | LOCUS -> MEMORY_BOUNDARY | project identity, storage carrier, isolation readback |
| Multiple sources conflict | SOURCE_A <-> CONFLICT <-> SOURCE_B | provenance for both, no silent flattening |
| Repair written but behavior unchanged | CORRECTION -> NEXT_TRIGGER -> BEHAVIOR | trigger replay, before/after consequence |

UNKNOWN/OPEN/CONFLICT are not stop permissions. They identify the next retrieval/comparison edge.
READBACK is a consequence check, not objective completion.
