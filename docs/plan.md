# RBAC test assignment — implementation epics

## Repository baseline

Starting point: **`chore: initial commit — full-stack-fastapi-template baseline`** — the official [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) (FastAPI + React), not an empty skeleton.

Already in place:

* **Stack:** FastAPI, SQLModel, Pydantic settings, PostgreSQL, Alembic; JWT via OAuth2 password flow; frontend — React, TypeScript, Vite, TanStack Router (file routes), TanStack Query, shadcn/ui, OpenAPI-generated client.
* **Authentication:** `backend/app/api/deps.py` — `OAuth2PasswordBearer`, `get_current_user`, `get_current_active_superuser`; token at `login/access-token`.
* **User model:** `backend/app/models.py` — `User` with `is_superuser`, `is_active`, **`User.role`** (`UserRole`: admin / manager / member), string-backed SQLAlchemy Enum (`native_enum=False`, values: `admin|manager|member`); DTOs (`UserPublic`, `UserCreate`, `UserUpdate`, …) отдают `role` в JSON. Дальше — enforcement в Epic 3–4.
* **API routes:** `backend/app/api/main.py` — `login`, `users`, `utils`, `items`; under `local`, also `private`.
* **First user:** `backend/app/core/db.py` — `init_db` creates the first superuser from `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` in `.env`.
* **Run:** `compose.yml`, `docker compose watch`; local dev see `development.md` — backend `:8000`, frontend `:5173`, prestart/migrations.
* **Frontend — session and protection:** token in `localStorage`, `useAuth` / `isLoggedIn`; layout `/_layout` redirects unauthenticated users to `/login`; admin page `/_layout/admin` calls `UsersService.readUserMe()` in `beforeLoad` and allows access only when `is_superuser` — extension point for roles and forbidden UX.
* **Tests:** `backend/tests` (pytest), e2e — Playwright (see CI).

Epic 1 must **lock a decision** on `is_superuser` vs `role` (see below) so there are not two incompatible sources of truth.

---

## Epic 0. Kickoff and template analysis

### Goal

Align the **actual** baseline architecture with the RBAC test requirements and identify integration points without unnecessary refactoring.

### Before any code changes (assignment requirement: run the app)

* Bring the project up “out of the box” per `development.md` / `docker compose watch` (or equivalent from the template README).
* Verify: backend responds, frontend loads, login with the first superuser from `.env` works, `/docs` if needed.
* Confirm for yourself: baseline is green — safe to change code. Otherwise a reviewer cannot tell template breakage from RBAC regressions.

### Already known from baseline (see Baseline above)

* Authentication: JWT + dependencies in `deps.py`
* User model and CRUD — entry point for `role`
* User APIs — `routes/users.py` and related dependencies
* Current “admin” on the frontend and partly on the backend is tied to `is_superuser`

### To clarify before coding

* Which template endpoints are actually used for the assignment scenarios (list/create users, profile, metrics) and what stays as-is (e.g. `items`)
* How the OpenAPI client is generated (`scripts/generate-client.sh`, scripts in `frontend/package.json`)

### Outcome

* A concrete list of files/dependencies per downstream epic
* Draft decision on `role` and `is_superuser` → finalized in Epic 1
* Minimal change surface vs. baseline

### Status (Epic 0 — актуализация)

**✅ Проверено (curl/HTTP/API, без правок кода):**

* Стек: `docker compose watch` с merge `compose.yml` + `compose.override.yml` (см. корневой `development.md`).
* `GET /api/v1/utils/health-check/` → `true`.
* `GET http://localhost:8000/docs` → 200 (Swagger UI).
* `GET http://localhost:5173/` → 200 (фронт из контейнера).
* `POST /api/v1/login/access-token` с учёткой `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` из `.env` → JWT.
* `GET /api/v1/users/me` с Bearer → `is_superuser: true` для первого суперпользователя.

**Не отмечено ✅ (нужен ручной смоук в браузере или не обязательно для фиксации baseline):**

* Видимость пункта Admin в сайдбаре после логина — логика совпадает с `is_superuser` из API; визуально в этой сессии не подтверждалось.

Детальный чеклист и карта endpoint’ов дублируются во внутреннем плане Epic 0 (если ведётся в IDE); в репозитории достаточно этого файла и чеклиста выше.

### Why this is a separate epic

In a timed test, the goal is to **fit into** the template, not rewrite it.

---

## Epic 1. RBAC model design

**Status — ✅ 100%:** [rbac-model.md](rbac-model.md) — Option C, матрица, политика SoT; out of scope для Epic 1 соблюдён; gate перед Epic 2 выполнен.

### Goal

Establish a **simple, consistent access model** so nothing is improvised later.

### Decisions to make

* Role list:

    * `admin`
    * `manager`
    * `member`
* How the role is stored:

    * `role` field on `User` (recommended for this assignment)
* **Decision (one mandatory policy line in the Epic 1 artifact): `is_superuser` vs `role`**

    * Option A: `is_superuser` only for bootstrap / template compatibility; all access checks in code go through `role`; first user from `.env` gets `role=admin` and if needed `is_superuser=True` until superuser logic is removed from routes
    * Option B: remove `is_superuser` from authorization paths entirely; keep the DB column for migration or drop later; seed sets `role` only
    * Option C: temporarily map `is_superuser=True` ↔ `role=admin` in one place (helper); other roles only via `role` — no duplicated checks across routers

    Do not start Epic 2 without a chosen option — risk of an inconsistent system (and review feedback).

* Role format:

    * enum / centralized constants on the backend + derived capabilities on the frontend
* Permission matrix:

    * who can list users
    * who can create user
    * who can view metrics
    * who can update own profile
    * who can update any profile

### Artifacts

* A written permission matrix
* **Hard rule:** backend is the single source of truth for access; frontend reflects capabilities and UX only, not enforcement
* Rule: any new protected scenario is backend first, then UI

### Outcome

One clear model that backs:

* backend checks
* frontend guards
* tests
* README

---

## Epic 2. Backend: extend data model for roles

**Status — ✅ 100%:** `UserRole` и поле `role` в модели и схемах; колонка `user.role` + Alembic (`c4a8f1e2b3d4`); дефолт `member`, первый пользователь из `init_db` — `admin` + `is_superuser=True`; `UserUpdate` оформлен как отдельный PATCH DTO (без наследования от `UserBase`); `private` и CRUD создают пользователей с корректной ролью; OpenAPI-клиент в `frontend/src/client` содержит `role` / `UserRole`.

### Goal

Add a role to the backend model with minimal invasiveness and clear intent.

### Tasks

* Add `role` to the user model and to Pydantic schemas exposed via the API
* **API contract:** update schemas, including `UserPublic`, so `role` appears in JSON for the current user (and elsewhere per the matrix)
* **After schema changes:** regenerate the frontend OpenAPI client (`scripts/generate-client.sh` or the command from `frontend/package.json`) and verify types
* Define default role for a normal user
* Alembic migration for the new field
* Validate create/register/init flow (`crud`, `init_db`)

### Decisions

* Default role is usually `member`
* First user from `.env` must get a role aligned with Epic 1 (e.g. `admin`)
* Hook into existing `init_db`; avoid a second mechanism unless necessary

### Outcome

Backend stores and returns user role; the frontend sees `role` in the generated client.

Вот по факту того, что всплывало при выполнении Epic 2:

1. SQLAlchemy / SQLModel и тип колонки role
   Миграция кладёт в БД строковые значения (`admin`, `manager`, `member`). Для согласованности с API-контрактом и статической типизацией поле `User.role` задано через SQLAlchemy Enum с `native_enum=False` и `values_callable`, чтобы в БД и JSON стабильно использовать именно строковые значения enum.

2. Окружение (tooling)
   Не везде в PATH были uv / python — приходилось опираться на python3 и ставить dev-зависимости вручную для прогона тестов.
   Скрипт scripts/generate-client.sh завязан на uv run python — без uv генерация ломается; обходили ручным дампом OpenAPI и npm/npx в frontend.
   Дамп OpenAPI без PYTHONWARNINGS=ignore (или перенаправления stderr) заливал в JSON warnings из config — файл становился невалидным.
3. БД и тесты
   Пока не выполнен alembic upgrade head, колонки role нет — тесты сыпятся с UndefinedColumn. Это ожидаемо, но легко спутать с багом в коде.

4. Побочные артефакты
   После npm install в корне появился package-lock.json, тогда как в репо ориентир bun.lock — лишний шум для коммита.
   docs/ в .gitignore — правки документации по эпикам сами в git не попадают, пока явно не решить (убрать игнор, -f, вынести файлы).
---

## Epic 3. Authorization layer (deps / helpers)

**Status — ✅ 100%:** добавлен единый authz-слой `backend/app/api/authz.py` (`get_effective_role`, `require_roles`, `require_admin`, `require_admin_or_manager`, `require_self_or_admin`, `require_owner_or_admin`); route-level guards переведены на dependency-паттерн в `routes/users.py`, `routes/utils.py`, `routes/login.py`, `routes/items.py`; прямые `is_superuser`/`get_current_active_superuser` проверки убраны из роутеров; deny в authz-guards унифицирован как `403 Forbidden`; добавлены тесты `backend/tests/api/test_authz.py` и обновлены contract-ожидания `403` в route tests.

### Goal

Create **one authorization check mechanism** so checks are not scattered.

### Invariant (explicit)

All access rules **must** be enforced on the backend regardless of the frontend. The frontend is not a security boundary.

### Implement

* Reusable dependency/helper for role checks (alongside `CurrentUser` / legacy `get_current_active_superuser` in `deps.py`)
* If needed, separate dependencies for:

    * `self or admin`
    * `admin only`
    * `admin or manager`

### Preferred approach

* Dependency-based checks on FastAPI endpoints
* Small, obvious helpers

### Important

* Do not mix authorization with business logic
* Avoid “magic” middleware for the whole app unless justified
* Each endpoint should show its access rule clearly

### Outcome

A single backend pattern for access control.

---

## Epic 4. Backend: protect surface (users + metrics stub)

**Status — ✅ 100%:** добавлен отдельный router `backend/app/api/routes/metrics.py` с `GET /metrics/` и стабильным stub payload (`status`, `generated_at`, `summary`), доступ `admin|manager` через `Depends(require_admin_or_manager())`; router подключен в `backend/app/api/main.py` под `/api/v1`.  
Users surface выровнен по матрице Epic 4 и по паттерну enforcement: авторизация на delete-операциях вынесена в authz dependencies (`require_non_admin`, `require_not_self`) без inline role checks в route handlers.  
Тесты покрывают allow/deny и authn vs authz semantics: `backend/tests/api/routes/test_metrics.py`, обновления в `backend/tests/api/routes/test_users.py`, и unit-тесты новых authz helper-ов в `backend/tests/api/test_authz.py`.

### Goal

Apply RBAC to all assignment scenarios in one pass: **user management** and a **separate protected metrics surface** (no standalone metrics in baseline — the stub belongs in this epic, not “after all backend work”).

### Invariant

Same as Epic 3: denial is `403`, no privilege escalation; matrix from Epic 1.

### Surface

#### 1. List users

* Access: `admin`, `manager`

#### 2. Create user

* Access: `admin`

#### 3. View metrics/insights

* Access: `admin`, `manager`
* **Implementation:** simple endpoint under `API_V1_STR` (e.g. `/metrics/` or an agreed name), stub response; register the router in `api/main.py`
* **Page:** minimal frontend route for metrics (can follow client regen in Epic 6, but endpoint and access rules live here)

#### 4. View own profile

* Access: all authenticated users

#### 5. Update own profile

* Access: all authenticated users

#### 6. Update any profile

* Access: `admin`

### Important here

* Correct `403 Forbidden`
* No privilege escalation
* Consistency: same model on every endpoint, including metrics

### Outcome

All backend endpoints required by the assignment, including the metrics stub, are protected consistently.

---

## Epic 5. Backend: seed/init data for roles

**Status — ✅ 100%:** `init_db` расширен идемпотентным role-seed для `admin|manager|member`; `admin` берется из env (`FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD`), `manager/member` задаются как встроенный bootstrap seed в seed-слое (`backend/app/core/db.py`) для local/review; для существующих seed-аккаунтов обновляются только `role` и `is_superuser` (без перезаписи пароля).  
Прозрачность и DX: `backend/app/initial_data.py` логирует результат сидинга (`created/updated`) без секретов; добавлены focused tests `backend/tests/core/test_db_seed.py` (наличие ролей, идемпотентность, no-password-override), README обновлен инструкциями по проверке.

### Goal

Make it easy for a reviewer to **run the project and immediately verify RBAC**.

### Need

* At least one `admin`
* At least one `manager` or non-admin user
* At least one `member`
* A clear way to create them:

    * extend `init_db` / fixtures
    * seed script
    * documented manual steps

### Important

This is part of the assignment’s **Developer UX**.
Do not leave the reviewer guessing how to create users for each role.

### Outcome

After startup, test users exist for scenario checks.

---

## Epic 6. Frontend: data and capability model

**Status — ✅ 100%:** добавлен централизованный слой `frontend/src/lib/capabilities.ts` с полной матрицей boolean-capabilities и безопасным fallback для `null|undefined`; `frontend/src/hooks/useCapabilities.ts` как тонкий адаптер поверх `useAuth`; route-level guard `/_layout/admin` переведен на `getCapabilities(user.role).canManageUsers`; sidebar/admin-nav, кнопка `Add User` и `UserActionsMenu` используют capability checks (`canManageUsers`, `canCreateUser`, `canEditAnyProfile`) вместо `is_superuser`; admin формы (`AddUser`/`EditUser`) работают role-driven через `UserRole`, без legacy `is_superuser` поля в UI-слое; добавлены/обновлены фронтенд-тесты `frontend/tests/capabilities-model.spec.ts` и `frontend/tests/admin.spec.ts` для role->capabilities, fallback и manager-access сценариев.

### Goal

Teach the frontend, from **user data** (including `role` from the API), **what the current user may do**, without chaotic role string comparisons across JSX.

### Tasks

* Build on `UserPublic` / generated client after Epic 2
* Helper or capability mapping (`canViewMetrics`, `canManageUsers`, …)
* Define how the UI knows:

    * users list / admin page
    * metrics
    * create user

### Important

* Frontend must not be the security boundary
* Logic centralized
* Do not compare role strings in 20 places

### Outcome

One “what’s allowed” layer for the current user, ready for navigation and guards (Epic 7).

---

## Epic 7. Frontend: navigation, guards, buttons, forbidden UX

**Status — ✅ 100%:** добавлен dedicated forbidden route `/forbidden` и экран `Access Denied`; внедрены единые route-guards (`requireAuth`, `requireCapability`) с loop protection для `/forbidden`; `/_layout/admin` переведен с silent redirect на capability-based deny; action/nav gating доведен в UI (admin create-user и item actions/create-button через capabilities); добавлен защищенный frontend route `/_layout/metrics` с `requireCapability("canViewMetrics")`, загрузкой metrics stub через OpenAPI client и условной видимостью пункта `Metrics` в sidebar по capability; глобальный API error handling разделен: `401` -> logout/login, `403` -> denied UX без forced logout.

### Goal

Meet the assignment’s UX: hide what’s forbidden + explicit denial on direct navigation.

### Implement

#### Navigation

* Hide links to sections the user cannot access (e.g. `AppSidebar` and similar)

#### Actions / buttons

* Hide actions the user cannot use
* Example: create user for admin only

#### Route/page protection

* TanStack Router: `beforeLoad` / guards — on direct navigation to a forbidden page:

    * `Forbidden` / `Access Denied`
    * Friendly message (today admin redirects to `/` — for RBAC a dedicated denial page is better)

### Important

* No silent failure
* No blank screen
* Not “API error with no explanation”

### Outcome

Frontend matches UX requirements: hides what’s forbidden and handles direct access correctly.

---

## Epic 8. Backend tests for critical authorization paths

**Status — ⏳ in progress:** critical authz matrix tests расширены по users/metrics/items и authz helper unit-cases; финальная валидация ожидает green CI run в окружении с поднятой test DB.

### Goal

Show RBAC is not only “looks fine in the UI” but is enforced by tests.

### Minimum set

* `admin` can list users
* `manager` can list users
* `member` cannot list users
* `admin` can create user
* `manager` cannot create user
* `member` cannot view metrics
* `manager` can view metrics

### If time is short

Cut scope to 3–5 tests:

* admin allowed
* manager denied on create
* member denied on list
* manager allowed on metrics
* member denied on metrics

### Important

* Test the critical authorization contract
* Prefer quality over quantity
* Test names should read clearly

### Outcome

Focused backend tests in the spirit of existing `backend/tests`, aligned with the assignment.

---

## Epic 9. README and archi/Users/kostiantyn/Projects/rbac-react-python-sql-assignment/docstectural notes

### Goal

Make the solution understandable without reading the entire repo (what gets committed is the root README, not drafts under `docs/`).

### Must include

* How to run locally (including docker / dev from `development.md`)
* How to apply migrations
* How to create/seed test users
* How to run tests
* Permission matrix
* Short explanation of approach:

    * where authorization checks live
    * how role is stored
    * how the frontend learns capabilities
* How to regenerate the API client when schemas change (if a reviewer changes backend)

### Nice to have

* Brief note on scope cuts if anything is unfinished
* Trade-offs

### Optional

* ADR 1: why dependency-based RBAC
* ADR 2: why simple RBAC instead of a policy engine

### Outcome

README covers run, verification, and architecture.

---

## Epic 10. Final end-to-end validation

### Goal

Confirm the solution actually works, not “files look OK in isolation”.

### Checklist

* Project runs locally
* Migrations succeed
* Seed works
* Admin sees everything required
* Manager sees users list + metrics but not create user
* Member sees only their scope
* Forbidden states are friendly
* Backend returns real `403`s
* Tests pass
* README matches the repo

### Outcome

A deliverable ready to submit.

---

# Recommended implementation order

1. **Epic 0** — bring up baseline, then analyze
2. **Epic 1** — RBAC model + **final decision** `is_superuser` vs `role`
3. **Epic 2** — model + migration + **UserPublic + OpenAPI client regen**
4. **Epic 3** — authorization deps/helpers
5. **Epic 4** — protect users **and** metrics stub (one RBAC surface)
6. **Epic 5** — seed/init data
7. **Epic 6** — capability helpers (data)
8. **Epic 7** — UI: nav, guards, forbidden
9. **Epic 8** — backend tests
10. **Epic 9** — README
11. **Epic 10** — final check

---

# Phases

## Phase 1 — Discovery + run baseline

* Epic 0
* Epic 1

## Phase 2 — Backend RBAC foundation

* Epic 2
* Epic 3

## Phase 3 — Backend enforcement (users + metrics together)

* Epic 4
* Epic 5

## Phase 4 — Frontend enforcement & UX

* Epic 6
* Epic 7

## Phase 5 — Verification & handover

* Epic 8
* Epic 9
* Epic 10

---

# Core of the assignment when time is tight

If time is limited, the core is:

* **Epic 1**
* **Epic 2**
* **Epic 3**
* **Epic 4**
* **Epic 7**
* **Epic 8**
* **Epic 9**

I.e.:

* role model and superuser policy
* backend enforcement (including metrics)
* frontend forbidden UX
* tests
* README
