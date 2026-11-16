---
trigger: glob
globs: "frontend/**/*.js, frontend/**/*.jsx, frontend/**/*.ts, frontend/**/*.tsx"
description: React frontend implementation rules
---

- The browser communicates with FastAPI through the configured Nginx/API origin; it must never connect directly to PostgreSQL or Redis.
- Keep components focused and reusable; separate API access from presentation components.
- Handle loading, empty, error, success, and not-found states.
- Format monetary values without converting exact decimal strings through unsafe floating-point arithmetic.
- Use semantic HTML, accessible labels, visible focus states, and keyboard-operable controls.
- Do not invent branding, currency, authentication, or authorization behavior; consult the frontend design brief and open decisions.
- Confirm destructive actions and prevent accidental duplicate submissions.
- Add/update tests for user-visible behavior when frontend test tooling is selected.
