# Repository Guidelines

## Project Structure & Module Organization
- `frontend/` hosts the Next.js 14 App Router UI; colocate screens in `frontend/app`, shared UI in `frontend/components`, hooks/utilities in `frontend/lib`, and fixtures under `frontend/tests`.
- `backend/` contains the FastAPI service (`backend/app`), domain modules (`api`, `services`, `schemas`, `prompts`), and `backend/alembic` for migrations; automated specs live in `backend/tests`.
- `docs/`, `ARCHITECTURE.md`, and `API.md` summarize product decisions; `scripts/` supports data backfills and `docker-compose*.yml` captures local orchestration.

## Build, Test, and Development Commands
- Full stack via Docker: `docker-compose -f docker-compose.dev.yml up --build` then `docker-compose exec backend pdm run alembic upgrade head`.
- Frontend: `cd frontend && npm install && npm run dev` for hot reload, `npm run build` for production bundles, and `npm run lint` before committing.
- Backend: `cd backend && pdm install` to sync deps, `pdm run uvicorn app.main:app --reload --port 8000` for the API, and `pdm run alembic upgrade head` after schema changes.

## Coding Style & Naming Conventions
- TypeScript/TSX files follow ESLint’s `next/core-web-vitals` config; keep two-space indentation, PascalCase components (`Navbar.tsx`), `useCamelCase` hooks, and tidy Tailwind class groupings.
- Python code is formatted with `pdm run black app` (line length 120) and linted via `pdm run ruff check app`; modules, files, and functions stay snake_case, while Pydantic models remain PascalCase with explicit type hints.

## Testing Guidelines
- Backend uses Pytest with async fixtures; all specs belong in `backend/tests/test_*.py`. `pdm run pytest` enforces `--cov=app --cov-fail-under=95`, so add meaningful assertions and mark slow API calls appropriately.
- Frontend uses Jest + Testing Library (`npm run test` or `npm run test:coverage`) for component logic; snapshot files live next to the source. End-to-end coverage relies on Playwright (`cd frontend && npx playwright test`).

## Commit & Pull Request Guidelines
- Follow the conventional style seen in `git log` (`fix: ...`, `docs(project): ...`, `test(version-control): ...`). Use imperative verbs and keep the subject under 72 characters; bilingual context is optional but must clarify the change.
- Pull requests should describe the problem, solution, and validation (list the exact commands executed). Link issues when available, attach UI screenshots for visual work, and ensure CI-critical commands (`npm run lint`, `pdm run pytest`) have been run locally.

## Security & Configuration Tips
- Never commit secrets; copy `frontend/.env.local.example` or `backend/.env.example` and keep overrides in local files. Required keys include `NEXT_PUBLIC_API_URL`, database URLs, and Redis credentials.
