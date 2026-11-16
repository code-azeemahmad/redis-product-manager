---
trigger: always_on
description: Verification and documentation maintenance requirements
---

- A task is not complete until relevant tests are run and their actual results are reported.
- Add or update tests for each behavior change; cover normal and failure paths.
- Do not claim tests passed if they were not executed.
- Update the relevant `docs/` page when an implementation changes an API, schema, architecture, security, or operations contract.
- Update `project-management/tasks.md` and `project-management/progress.md` after verified work.
- Keep `README.md` setup and run instructions synchronized with the actual codebase.
- Inspect the current repository and diff before editing; do not overwrite unrelated user work.
