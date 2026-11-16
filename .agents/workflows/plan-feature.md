# Plan Feature Workflow

Use this workflow when asked to plan a new feature or a substantial change.

1. Read `AGENTS.md`, `README.md`, and the relevant `docs/` pages.
2. Read `project-management/roadmap.md`, `tasks.md`, and `progress.md`.
3. Inspect the current implementation and tests.
4. Restate the requested outcome and acceptance criteria.
5. Identify affected layers: frontend, Nginx, API, service, database, cache, security, operations.
6. Identify open decisions and risks. Do not invent answers for auth, tenancy, currency, rate limits, or production settings.
7. Propose a small sequence of tasks with files likely to change and tests required.
8. Do not implement until the user asks to proceed or the current task explicitly includes implementation.
