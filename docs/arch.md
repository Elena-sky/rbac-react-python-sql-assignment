# Guardrails for the RBAC test implementation

## 1. Overall implementation goal

Implement a **minimal, understandable, extensible RBAC model** in the existing FastAPI + React/TypeScript full-stack template.

Top priorities:

* readability
* consistency between backend and frontend
* predictable architecture
* minimal change surface
* no “magic” or hidden complexity

This is **not** an enterprise IAM system, ACL engine, or policy framework.
Target quality: **small, realistic production MVP**.

### 1.1 Base repository

Starting point: **[Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template)** (baseline commit: `chore: initial commit — full-stack-fastapi-template baseline`). This document sets RBAC constraints **on top of** that code, without rewriting half the template.

### 1.2 Monorepo layout

* `backend/` — FastAPI app (`app.main`), Pytest tests in `backend/tests/`, env and deps via **uv** (`backend/pyproject.toml`).
* `frontend/` — **Vite**, **React**, **TypeScript**, OpenAPI client in `frontend/src/client/` (regenerate: `scripts/generate-client.sh`).
* Root: **Docker Compose** (`compose.yml`, local dev `compose.override.yml`), secrets and config in `.env`, CI in `.github/workflows/` (backend, docker-compose, Playwright, pre-commit, etc.).

### 1.3 Backend before RBAC

* Stack: **FastAPI**, **SQLModel**, **PostgreSQL**, **Alembic** migrations (`backend/app/alembic/`).
* Entry: `backend/app/main.py`; API prefix and router — `backend/app/api/main.py` (`/api/v1/...`).
* Routes: `backend/app/api/routes/` — `login`, `users`, `items`, `utils`; with `ENVIRONMENT=local`, `private` is included.
* Dependencies: `backend/app/api/deps.py` — `get_db`, OAuth2 bearer (`tokenUrl` on login), `get_current_user`, **`get_current_active_superuser`** (access via **`User.is_superuser`** flag).
* Models: `backend/app/models.py` — `User` with `is_active`, **`is_superuser`**, **`role`** (`UserRole`: admin / manager / member), `full_name`, `hashed_password`, relation to `Item`.
* Also: `backend/app/crud.py`, `backend/app/core/config.py`, `backend/app/core/db.py`, `backend/app/core/security.py` (JWT, password hashing).

### 1.4 Frontend before RBAC

* **TanStack Router** — file routes in `frontend/src/routes/` (root layout, `login`, `signup`, `_layout` with `index`, `items`, `admin`, `settings`, etc.).
* **TanStack Query**, **Tailwind CSS**, **shadcn/ui** (`frontend/components.json`), shared components in `frontend/src/components/`.
* Session/token and API calls — generated client and hooks (e.g. `frontend/src/hooks/useAuth.ts`); base URL via `VITE_API_URL`.

### 1.5 Baseline → RBAC

* The template already uses **explicit `Depends`** on endpoints (e.g. `dependencies=[Depends(get_current_active_superuser)]` on `users`) — natural to extend to role checks instead of a “magic” global middleware.
* “Admin” today is **`is_superuser`**. Introducing `admin | manager | member` must be reconciled with that flag (mapping, replacement, or narrowing superuser use) so there are not two incompatible sources of truth.

---

## 2. Architectural boundaries

### 2.1 What we do

* Roles `admin | manager | member`
* Centralized RBAC model
* Backend enforcement on protected endpoints
* Frontend capability-based rendering
* Friendly forbidden state in the UI
* A few focused backend tests
* Short README documentation

---

### 2.2 What we do not do

Do not add:

* A heavy permission engine
* Dynamic permissions from the DB
* Separate `permissions` / `role_permissions` tables unless the template requires them
* Middleware that tries to authorize every case globally
* Overly generic “future-proof” abstractions
* Event bus, audit subsystem, feature flags, policy DSL
* Extra patterns for aesthetics only

---

## 3. Target architecture

Below is the **target RBAC model after changes**; the current template baseline is described in §1.1–1.5.

## 3.1 Backend

RBAC should be implemented via **explicit dependency checks** on FastAPI endpoints.

Preferred approach:

* role stored on `User`
* role represented as an enum
* checks in small reusable dependencies/helpers
* each endpoint shows who has access

Principles:

* authentication answers **who** the user is
* authorization answers **what** they may do
* business logic should not “accidentally” decide access along the way

---

## 3.2 Frontend

The frontend is not the security source of truth.

The frontend should:

* receive the current user and their role
* compute allowed actions via helpers/selectors
* hide inaccessible pages/buttons
* show “Access Denied” on direct navigation

Principle:

* backend protects data
* frontend improves UX

---

## 4. Required principles

## 4.1 Single Responsibility Principle

Each module does one thing:

* `auth` / current user extraction
* `authorization` / role checks
* `routes` / endpoint wiring
* `crud/service` / business operations
* `frontend permission helpers` / UI decisions

Do not mix everything in one place.

---

## 4.2 Explicit over implicit

Authorization must be **explicit**.

Good:

* endpoint shows allowed roles immediately
* helper has a clear name
* UI condition reads without digging

Bad:

* behavior buried in middleware
* access via non-obvious side effects
* unclear why an endpoint is open or closed

---

## 4.3 Centralized policy, decentralized usage

Access rules should be defined **in one clear place** but used in several.

For example:

* backend helper `require_roles(...)`
* frontend helper `canAccess(...)`
* single permission matrix in README

Do not manually duplicate the matrix in ten places.

---

## 4.4 Minimal surface area

Change only what RBAC actually needs.

Do not refactor half the project for a timed test.
Do not rewrite the template architecture if the problem can be solved locally and cleanly.

---

## 4.5 Consistency first

If one check style is chosen, it must be applied the same way everywhere.

For example, if endpoints use dependency-based guards, avoid:

* one endpoint — dependency
* another — inline `if`
* third — service-layer exception
* fourth — frontend-only hiding

---

## 5. Preferred solution shape

## 5.1 Backend

This repo already has (template):

* `backend/app/models.py` — `User` — **`role`** + enum; миграция Alembic применена; **authorization по ролям** — в `deps` / helpers (Epic 3).
* `backend/app/api/deps.py` — `get_current_user`; role authorization helpers are centralized in `backend/app/api/authz.py` (`require_roles`, `require_admin`, `require_admin_or_manager`, `require_self_or_admin`) to avoid scattered duplication across routes.
* `backend/app/api/routes/*.py` — declarative `Depends` / `dependencies=[...]` on endpoints (as for superuser on `users` today).
* `backend/tests/api/routes/` — focused authorization contract tests.

Fit this layout; do not invent a parallel directory structure.

---

## 5.2 Frontend

This repo already has (template):

* current user — TanStack Query + `frontend/src/hooks/useAuth.ts` and generated client;
* routes — `frontend/src/routes/` (TanStack Router); pages `admin`, `items`, etc.;
* navigation — `frontend/src/components/Sidebar/`, shared wrappers — `components/Common/`.

Add: permission/capability helpers, route- or layout-level guard, conditional buttons/menu items, dedicated **forbidden** state on direct URL access.

---

## 6. What counts as good code

## 6.1 Good backend code

* small functions
* names reflect intent
* roles as enum
* permission checks reused
* endpoints declarative
* correct HTTP status codes (`403`, not `500` or `200` with an error body)

Good direction examples:

* `require_roles("admin", "manager")`
* `is_self_or_admin(...)`
* `can_update_user(actor, target)`

---

## 6.2 Good frontend code

* does not compare roles chaotically across the app
* uses helpers like `canViewMetrics(user)` or `canAccess(user, "metrics")`
* does not duplicate the same logic across nav, route, and button
* shows a clear message instead of an empty screen

---

## 7. What not to do

Below are anti-patterns to avoid.

## 7.1 Do not scatter role checks everywhere

Bad:

```python
if user.role == "admin":
    ...
elif user.role == "manager":
    ...
elif user.role == "member":
    ...
```

in dozens of places.

Why bad:

* high coupling
* hard to extend
* easy to get wrong
* access model hard to see quickly

---

## 7.2 Do not mix business logic and authorization

Bad:

```python
def create_user(data, current_user):
    if current_user.role != "admin":
        raise Exception("no")
    ...
```

if this is the main protection pattern in services.

Why bad:

* business layer knows too much about transport/security
* checks are hard to find
* endpoint does not show its access policy

Acceptable only in rare domain cases, not as the primary RBAC mechanism.

---

## 7.3 Do not use the frontend as security

Bad:

* hide a button and call it done
* leave backend endpoint unprotected
* assume the user “won’t click”

Why bad:

* not security
* any direct request bypasses the UI

---

## 7.4 Do not use “magic” middleware for everything

Bad:

* one global middleware decides access per endpoint by path substring
* rules tied to URL strings
* logic hidden from endpoints

Why bad:

* opaque
* brittle
* hard to debug
* fails the “understand in 5 minutes” bar

---

## 7.5 Do not over-abstract

Bad:

* class `PermissionResolverFactoryBuilderRegistry`
* policy inheritance tree
* generic permission registry 200 lines long for five rules

Why bad:

* one-hour test scope
* looks like overengineering
* team won’t want to maintain it

---

## 7.6 Do not manually duplicate the permission matrix

Bad:

* one logic in README
* another in backend
* third in frontend
* fourth in tests

Everything should follow one model.

---

## 7.7 Do not use vague or weak names

Bad:

* `check()`
* `handle_role()`
* `verify_user()`
* `do_auth()`

Good:

* `require_roles`
* `require_admin`
* `can_view_metrics`
* `can_manage_users`

---

## 7.8 Do not return wrong errors

Bad:

* `200 OK` with `"error": "forbidden"`
* `500` on access denial
* raw traceback
* silent redirect with no explanation

Correct:

* backend: `403 Forbidden`
* frontend: friendly forbidden state

---

## 8. Forbidden code smells

## 8.1 Shotgun Surgery

If adding a role touches many unrelated files and places — architecture is wrong.

Goal:
a new role should touch a limited number of places.

---

## 8.2 Primitive Obsession

Do not use raw role strings chaotically across the project.
Use an enum or at least centralized constants.

---

## 8.3 Long Function

Access functions should stay small.
If `canAccess` becomes half a screen of nested conditions — smell.

---

## 8.4 Conditional Complexity

Avoid forests of `if/elif/else` for permissions.
Prefer compact policy helpers and a decision matrix.

---

## 8.5 Divergent Change

If role/capability logic is spread across unrelated modules, every permission change breaks things.

---

## 8.6 Comments explaining bad code

Do not write code that only makes sense with comments.
Comments only for non-obvious spots.

---

## 8.7 Boolean blindness

Bad:

```python
check_access(user, True, False, True)
```

Good:

```python
require_roles(Role.ADMIN, Role.MANAGER)
```

---

## 9. Rules for backend code generation

1. Reuse existing template patterns when present.
2. Add `role` to the user model with minimal invasiveness.
3. Use an enum for roles.
4. Keep authorization helpers separate from routes.
5. Make endpoint guards explicit and declarative.
6. Use `403 Forbidden` for access denial.
7. Do not duplicate the same check more than twice — extract a helper.
8. Avoid large refactors of the existing auth layer.
9. Do not break existing authentication.
10. If there is “update own profile”, distinguish self-update vs any-profile update explicitly.

---

## 10. Rules for frontend code generation

1. Do not put security only in the frontend.
2. Add a permission or capability helper.
3. Hide navigation items and action buttons for forbidden roles.
4. Protect route-level access with a friendly forbidden screen.
5. Do not scatter role checks across JSX.
6. If the same condition appears in several places — extract a helper.
7. Do not complicate state management if existing user state is enough.

---

## 11. Test requirements

Not every test in the world — only critical ones.

Minimum coverage:

* admin can create user
* manager cannot create user
* member cannot list users
* manager/admin can view metrics
* member gets 403 on metrics

Tests should be:

* short
* clear from the name
* focused on the authorization contract

Do not write noisy tests for volume.

---

## 12. README: what to document

The root template `README.md` already covers stack, Docker Compose, and links to `development.md`, `backend/README.md`, `frontend/README.md`. For the assignment, add (or section) at least:

1. How to run the project (including `docker compose` / local — see `development.md`)
2. How to apply Alembic migrations (`backend/app/alembic/`)
3. How to seed users (`backend/app/initial_data.py` / first superuser from `.env`)
4. Which roles exist
5. Permission matrix
6. How authorization works:

    * where backend checks live (`deps`, routes)
    * where `role` is stored
    * how the frontend learns capabilities
7. How to run tests (`bash ./scripts/test.sh`, see `backend/README.md`)

---

## 13. Practical decision rule

When choosing between two options, prefer the one that:

* is easier to explain to a new developer
* needs less hidden context
* is easier to test
* does not break the existing template
* looks like production MVP, not pet overengineering

---

## 14. Definition of “done well”

The solution is strong if:

* backend protects access regardless of frontend
* frontend does not show forbidden actions
* direct navigation to a forbidden page has clear forbidden UX
* permission model is understandable in ~5 minutes
* adding a role does not mean rewriting half the project
* code reads calm, simple, and engineer-like

---

## 15. Short version for Cursor

If you need a compact block for a prompt:

```text
Implement RBAC for a FastAPI + React app based on full-stack-fastapi-template (SQLModel, deps.py, JWT, User.is_superuser today) with 3 roles: admin, manager, member.

Architecture constraints:
- Keep the solution minimal, explicit, and easy to understand in 5 minutes.
- Use backend authorization via clear FastAPI dependencies/helpers, not frontend-only checks.
- Store role on the User model using an enum or centralized constants.
- Keep authorization logic centralized and reusable, but endpoint usage explicit.
- Frontend should use capability/permission helpers for route guards, nav visibility, and buttons.
- Show friendly forbidden UI for unauthorized direct navigation.
- Do not build a complex policy engine, ACL system, middleware magic, or over-abstracted permission framework.
- Avoid scattering raw role checks across many files.
- Avoid mixing business logic and authorization logic everywhere.
- Avoid large refactors unrelated to RBAC.

Code quality rules:
- Small focused functions
- Clear naming that shows intent
- Consistent patterns across endpoints and UI
- Low coupling, easy to extend
- Correct HTTP semantics: use 403 for forbidden access
- Minimal but solid backend tests for critical authorization paths

Code smells to avoid:
- role checks duplicated everywhere
- giant if/elif chains
- magic middleware based on URL matching
- frontend treated as security boundary
- vague names like check(), handleRole(), verify()
- overengineering with factories/builders/registries for simple RBAC
```
