# RBAC model (Epic 1 artifact)

Design-only document. **Epic 2 (данные и API):** поле `User.role` и enum в коде и БД — ✅. **Backend enforcement (deps + routes, users + metrics):** ✅ Epic 4. **Frontend capability model (role-driven decisions):** ✅ Epic 6. **Dedicated forbidden UX + guards/buttons + 401/403 UX split:** ✅ Epic 7.

## Permission matrix (MVP)

| Action | admin | manager | member |
| --- | --- | --- | --- |
| List users | yes | yes | no |
| Create user | yes | no | no |
| View metrics | yes | yes | no |
| View own profile | yes | yes | yes |
| Update own profile | yes | yes | yes |
| Update any profile | yes | no | no |

## Chosen decision

**Option C** — map `is_superuser` ↔ `admin` in one backend layer; all assignment authorization is expressed in terms of `User.role` and shared deps/helpers, not ad hoc checks in route bodies.

### Why

- Small diff from the full-stack-fastapi-template baseline.
- Keeps the existing `is_superuser` column for compatibility with seeds and template expectations.
- Avoids two incompatible sources of truth by making `role` the authorization source of truth and constraining superuser handling to a single place.

### Consequences

- New and refactored access checks for this assignment use `User.role` and reusable FastAPI dependencies (e.g. `require_roles`).
- Mapping between `is_superuser` and the admin role lives in **one backend layer** (for example the auth dependency chain or user normalization), **not** in individual route handlers.
- Removing raw `if current_user.is_superuser` from routes is done in Epic 3–4 as endpoints are migrated; not part of Epic 1.

## Policy (canonical English)

> `User.role` is the authorization source of truth for this assignment.  
> `is_superuser` is kept temporarily for baseline compatibility and is mapped to `admin` in one place only.  
> Mapping between `is_superuser` and the admin role must be implemented in a single backend layer (e.g. auth dependency or user normalization), not in route handlers.

Кратко по-русски: маппинг `is_superuser` ↔ admin не размазывать по `if is_superuser` в роутерах; один backend-слой (deps / нормализация пользователя).

## Rejected alternatives

- **Option A** — Bootstrap-only superuser is compatible with the spirit of the template, but Option C makes the “one place” rule explicit and easier to enforce in review.
- **Option B** — Dropping `is_superuser` from all authorization paths would touch more of the baseline and tests than is justified for this timeboxed assignment.

## Role contract (JSON and code)

Serialized role values in API JSON must be exactly:

`"admin"` | `"manager"` | `"member"`

These strings must match the future Python `UserRole` enum and the generated OpenAPI / TypeScript types to avoid drift.

## Principles

- **Enforcement:** backend is the only security boundary; return **403** for forbidden access.
- **Frontend:** derives capabilities from `GET /users/me` (and related) for UX only — hide links, show Access Denied on direct navigation; never rely on UI-only protection.
- **New protected behavior:** implement backend checks first, then UI (navigation, guards, buttons).

## Traceability to API surface

| Matrix row | Intended API (prefix typically `/api/v1`) |
| --- | --- |
| List users | `GET /users/` |
| Create user | `POST /users/` |
| View metrics | `GET /metrics/` (or agreed stub name) |
| View own profile | `GET /users/me` |
| Update own profile | `PATCH /users/me` |
| Update any profile | `PATCH /users/{user_id}` |

## Out of scope for Epic 1

- No database migration
- No API or Pydantic schema changes
- No frontend OpenAPI client regeneration
- No changes to routes, `deps.py`, or endpoint protection
- **No application code changes in this epic** — this artifact only

## Gate before Epic 2

Do not start Epic 2 until:

- [x] **Decision** Option C is accepted for this repo.
- [x] The three-line policy above is present and understood (including `User.role` as SoT and mapping in a single backend layer, not in route handlers).
- [x] Epic 1 is not mistaken for permission to change application code — schema and migrations belong to Epic 2.

**✅ Gate пройден; Epic 2 реализован в коде** (модель, миграция, API, клиент — см. [plan.md](plan.md) Epic 2).
