# PUBLIC SAFE POLICY

Repository visibility was verified as PUBLIC on 2026-10-07.

- RAW chat bytes: LOCAL_ONLY.
- Private memory / identity records: LOCAL_ONLY.
- Secrets, tokens, credentials, browser/session state: NEVER_COMMIT.
- .gdoc/.gsheet local shortcut files are pointers, not the document bodies.
- Promotion to Git requires classification and readback.
- Existing unrelated dirty worktree changes are not staged by this process.
- History is append-first; no destructive rewrite of source trees.
