# Planned Repository Structure

The application code will be added gradually. This is the target layout, not a claim that every file already exists.

```text
redis-saas-platform/
├── .agents/
│   ├── rules/                    # Flat Antigravity workspace rule files
│   └── workflows/                # Reusable Antigravity workflows
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   └── product.py
│   │   ├── routers/
│   │   │   ├── products.py
│   │   │   ├── dashboard.py
│   │   │   └── health.py
│   │   ├── services/
│   │   │   ├── redis_service.py
│   │   │   ├── product_service.py
│   │   │   └── rate_limiter.py
│   │   └── cache/
│   │       ├── keys.py
│   │       └── policies.py
│   ├── tests/                    # Backend tests (recommended addition)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                     # React application
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile                # If Nginx image needs custom build assets/config
├── redis/
│   ├── redis.conf
│   └── users.acl
├── docs/                         # Product and engineering documentation
├── project-management/           # Roadmap, tasks, progress, decisions
├── tests/                        # Cross-service or end-to-end tests if needed
├── compose.yaml
├── .env.example
├── .gitignore
├── AGENTS.md
└── README.md
```

## Boundaries

- `routers/` handles HTTP concerns and delegates to services.
- `services/` contains business use cases and orchestration.
- `database/` owns SQLAlchemy engine/session setup and ORM models.
- `schemas/` owns Pydantic request/response types.
- `cache/` owns key generation and cache policies; Redis client lifecycle belongs in a dedicated service/dependency layer.
- `nginx/` and `redis/` contain service configuration, not application business logic.
- `docs/` is the engineering contract; `project-management/` tracks delivery state.

Adjust this layout only when the codebase demonstrates a clear need. Keep this document synchronized after structural changes.
