# Content Studio (文策引擎)

短视频内容资料库 + 文案生成系统。FastAPI + Vue 3 全栈项目。

## Quick Start

```bash
# Backend
cd content-studio/backend
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8080

# Frontend
cd content-studio/frontend
npm install
npm run dev  # port 5173
```

## Project Structure

```
content-studio/
├── backend/
│   ├── main.py          # FastAPI app, middleware, lifespan
│   ├── config.py        # Pydantic Settings (all env vars)
│   ├── database.py      # SQLAlchemy engine + migration helpers
│   ├── models/init.py   # All DB models (single file)
│   ├── routers/*.py     # API route handlers (under /api)
│   ├── services/*.py    # Business logic layer
│   └── tests/
├── frontend/            # Vue 3 SPA (Vite)
└── admin/               # Admin SPA (separate Vue app)
```

## Conventions

- **DB migrations**: Use `_ensure_*` functions in `database.py` (lightweight ALTER TABLE), not Alembic
- **Auth deps**: `get_current_user` / `get_admin_user` from `routers/deps.py`
- **Logging**: Use `logging.getLogger("content_studio.*")` with structured format
- **API routes**: All under `/api`, use `routers/__init__.py` to aggregate
- **Config**: All settings in `config.py` with `.env` override
- **Error handling**: Raise HTTPException from routers; use middleware for unhandled exceptions

## Key Config Values

- Backend URL: localhost:8080
- Frontend URL: localhost:5173
- Database: SQLite `content_studio.db`
- JWT secret must be >= 32 chars

## Common Tasks

- Run tests: `cd content-studio/backend && python -m pytest tests/ -v`
- E2E tests: `cd content-studio/backend && uvicorn main:app --port 8080 &` then `npx playwright test`
- Add a DB column: add `_ensure_*` function in `database.py` and call from `init_db()`
