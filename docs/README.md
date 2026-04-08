# Fullstack-Dev-Test-Task

This is a task to test potential candidate skills in Python + SQL + TypeScript.

- **Assignment**: Add Role-Aware Access + Architecture Decisions + **Run the app**
- **Timebox**: Aim for up to 1 hour. If you cut scope, say what you cut and why.

## Implementation Checklist Rule

- [ ] Any item not fully implemented stays `[ ]`.
- [x] An item becomes `[x]` only at 100% completion.
- [ ] By default, all items below are considered not implemented.

## Repository progress

Alignment with the **original assignment text** (not only template code present).

### Что сделали

- [x] Backend RBAC: роли `admin|manager|member`, `User.role`, миграция, authz deps/helpers
- [x] Защищены users и metrics API по матрице доступа
- [x] Frontend capability model и UI-gating (nav/actions/routes)
- [x] Реализованы `/forbidden` UX и защищённая metrics страница (`/metrics`)
- [x] Расширены backend authz matrix tests (финальный green CI по Epic 8 в процессе)
- [ ] Финальная end-to-end валидация и полное закрытие deliverables в root `README.md`

### Статус эпиков (этот репозиторий)

| Epic | Тема | Статус |
|------|------|--------|
| 0 | Baseline, запуск шаблона | ✅ 100% — см. [plan.md](plan.md) |
| 1 | Модель RBAC (матрица, Option C, политика SoT) | ✅ 100% — [rbac-model.md](rbac-model.md) |
| 2 | Бэкенд: `User.role`, миграция, схемы API, OpenAPI-клиент, `init_db` | ✅ 100% — см. [plan.md](plan.md#epic-2-backend-extend-data-model-for-roles) |
| 3 | Authorization layer (deps/helpers) | ✅ 100% — см. [plan.md](plan.md#epic-3-authorization-layer-deps--helpers) |
| 4 | защита backend surface по матрице (users + metrics stub) | ✅ 100% — см. [plan.md](plan.md#epic-4-backend-protect-surface-users--metrics-stub) |
| 5 | сиды пользователей по ролям | ✅ 100% — см. [plan.md](plan.md#epic-5-backend-seedinit-data-for-roles) |
| 6 | фронтенд capability model (role -> capabilities) | ✅ 100% — см. [plan.md](plan.md#epic-6-frontend-data-and-capability-model) |
| 7+ | forbidden UX, frontend metrics page, расширение матричных тестов, root README | частично: forbidden UX ✅, frontend metrics page ✅, backend authz matrix tests расширены (Epic 8, ожидается green CI), root README в работе |

### Epic 0 — baseline (запуск шаблона)

**✅ Выполнено и проверено:** см. [docs/plan.md](plan.md) («Epic 0 — Status»): Docker Compose, health, Swagger `/docs`, фронт `:5173`, логин OAuth2, `GET /users/me` → `is_superuser: true`. Пункт Admin в сайдбаре — только через соответствие API; ручной UI-смоук не отмечен ✅.

### 1. Clone the Base Template

- [x] Project based on [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)

### 2. Roles and Authorization Surface

- [x] Three roles **admin** / **manager** / **member** defined in backend (`UserRole`, DB column `user.role`, JSON/OpenAPI) — ✅ **Epic 2**
- [x] Same three roles **enforced** by permission matrix in API + UI (beyond data-only roles) — **backend ✅ Epic 4, frontend capabilities ✅ Epic 6, forbidden UX/guards/buttons ✅ Epic 7, metrics page ✅**
- [x] Authorization deps/helpers layer implemented (`backend/app/api/authz.py`; explicit `Depends` guards) — ✅ **Epic 3**
- [x] **List/create users** protected on the API (now via `require_admin` / `require_admin_or_manager` guards)
- [x] **Current user profile** (`GET/PATCH /users/me` and settings UI)
- [x] **Metrics/insights backend stub** (`GET /api/v1/metrics/`, admin|manager, 403 for member)
- [x] **Metrics/insights page** (frontend route/UX)
- [x] Backend/frontend alignment via role capabilities (`getCapabilities(role)`): Admin route guard (`canManageUsers`), sidebar visibility (`canManageUsers`), create-user visibility (`canCreateUser`), user actions visibility (`canEditAnyProfile`)

### 3. Code Quality Expectations

- [ ] “Easy to add a role without touching 10+ files” — will need refactoring once real roles exist

### 4. Architecture & Documentation (required)

- [ ] Permission matrix in the **root** `README.md`
- [ ] Short description of the authorization approach (2–4 paragraphs) in README
- [ ] Inline comments only where authorization logic is non-obvious (essentially none today)

### 5. Optional

- [ ] ADR
- [ ] Diagram

### 6–8. NFR, UX, Developer UX

- [x] Explicit **Access denied / Forbidden** message when navigating directly to a forbidden route (`/forbidden` route + dedicated UI)
- [ ] Root README updated for the assignment: local run, seeds with admin and non-admin **as stated in the assignment**, tests, migrations when schema changes

**Deliverables summary:** see [Submission](#submission). **Готово на 100%:** Epic 0–7 frontend scope (baseline, [rbac-model.md](rbac-model.md), модель данных и API с `role`, миграция Alembic, authz deps/helpers слой, backend enforcement users + metrics stub, frontend capability model, dedicated forbidden UX, route/action deny behavior, metrics page). **Ещё не закрыто:** root README под задание, расширение e2e/contract покрытия и финальная end-to-end валидация.

---

## Table of Contents

- [Implementation Checklist Rule](#implementation-checklist-rule)
- [Repository progress](#repository-progress)
- [Goal](#goal)
- [Base Template](#base-template)
- [Suggested Time Allocation](#suggested-time-allocation)
- [Requirements](#requirements)
  - [1. Clone the Base Template](#1-clone-the-base-template)
  - [2. Roles and Authorization Surface](#2-roles-and-authorization-surface)
  - [3. Code Quality Expectations](#3-code-quality-expectations)
  - [4. Architecture & Documentation](#4-architecture--documentation)
  - [5. Non-Functional Requirements](#5-non-functional-requirements)
  - [6. UX Behavior](#6-ux-behavior)
  - [7. Developer UX](#7-developer-ux)
- [What We Review](#what-we-review)
- [Submission](#submission)

## Goal

Add role-based access control (RBAC) to the existing Full-Stack FastAPI Template so that only authorized users can access sensitive endpoints and UI sections.

**We prioritize clean, maintainable code over comprehensive test coverage or extensive documentation.**

You may reuse any libraries already in the template.

> **Note**: RBAC can be implemented with simple role checks or a small policy layer. Keep scope tight. Favor clarity over cleverness.

## Base Template

**Tech Stack**:
- **Backend**: FastAPI / SQLModel / PostgreSQL
- **Frontend**: React / TypeScript

**Repository**: [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template/tree/master)

## Suggested Time Allocation

How we believe it is doable in a 1-hour timebox:

| Activity | Time           | Priority |
|----------|----------------|----------|
| Understanding the codebase | 15 min         | High |
| Implementation (clear, maintainable code) | 25 mins | **Critical** |
| Testing (focused, critical paths) | 10 min         | High |
| Documentation (README updates) | 10 min         | Medium |

**If running short on time:**
- ✓ **Prioritize**: Clear, working authorization code with consistent patterns
- ✓ **Then**: 3-5 well-chosen tests covering critical scenarios
- ⚠ **Cut if needed**: Extra features, comprehensive test coverage, diagrams
- ❌ **Don't cut**: Security checks, README setup instructions

## Requirements

### 1. Clone the Base Template

Clone the repository: https://github.com/fastapi/full-stack-fastapi-template/tree/master

### 2. Roles and Authorization Surface

#### Implement the Following Roles

| Role | Permissions |
|------|-------------|
| **admin** | Full access to user management and settings |
| **manager** | Can list users and view metrics, but not change global settings |
| **member** | Can only access their own profile and basic app features |

#### Protect a Small but Realistic Surface

- List users
- Create user
- View "metrics/insights" page (simple stub is acceptable)
- View and update own profile

**Exact permission mapping is up to you.**

State it clearly in your docs and enforce it consistently in the backend and frontend.

#### Example Permission Matrix (Document Something Similar)

| Action | admin | manager | member |
|--------|-------|---------|--------|
| List all users | ✓ | ✓ | ✗ |
| Create user | ✓ | ✗ | ✗ |
| View metrics | ✓ | ✓ | ✗ |
| Update own profile | ✓ | ✓ | ✓ |
| Update any profile | ✓ | ✗ | ✗ |

### 3. Code Quality Expectations

**We prioritize maintainable, readable code over clever solutions.**
 
- **Clear naming**: Function/variable names that explain intent without comments
- **Single responsibility**: Small, focused functions
- **Easy to extend**: Adding a new role shouldn't require touching 10+ files
- **Self-documenting**: Code structure makes the authorization model obvious

> **Key principle**: A teammate should understand your authorization model in 5 minutes by reading your code.

### 4. Architecture & Documentation

Document your implementation approach clearly but concisely.

#### Required

- [ ] **Permission matrix** in README showing which role can access what
- [ ] **Brief explanation** (2-4 paragraphs) of your authorization approach:
  - Where authorization checks live (middleware, dependencies, decorators?)
  - How roles are stored and validated
  - How frontend learns about user capabilities
- [ ] **Inline code comments** only for non-obvious authorization logic

#### Optional (Bonus Points)

- [ ] **1-2 Architecture Decision Records (ADRs)** for your most critical decisions
  - Use any simple ADR format (problem, options, decision, trade-offs)
  - 200-400 words each
  - Example topics: Why you chose your authorization pattern, where checks live, how the frontend handles permissions
- [ ] **Simple diagram** showing where auth/authz checks happen
  - Mermaid, C4-style, or hand-drawn PNG is fine

**Philosophy**: We value clear thinking over formal documentation. 
Your code should clearly explain your approach; that's usually sufficient.
RBAC implementation, though, usually has at least a few options to implement, hence an additional README will add value.

### 5. Non-Functional Requirements

Demonstrate you considered real-world constraints:

#### 1. Maintainability (Critical)

- Keep coupling low; use consistent patterns
- A teammate should understand your authorization logic in 5 minutes

#### 2. Testability (Important)

- Provide **focused backend tests** covering critical authorization paths

> **Note**: Tests are required, but we prioritize **quality over quantity**. 3 well-chosen tests with clean code beat 20 tests with spaghetti code.

### 6. UX Behavior

- **The UI** should:
  - Hide navigation links/buttons that the user can't access
  - Show a friendly "Forbidden" or "Access Denied" message if navigating directly to unauthorized routes
  - Not just fail silently or show cryptic errors

### 7. Developer UX

Update the README with:

- **How to run locally** (setup, dependencies, database)
- **How to seed test data** with at least one admin and one non-admin user
- **How to run tests**
- **Database migrations** for any schema changes (if applicable)

Make it easy for us to run your solution without hunting for setup instructions.

## What We Review

### Primary Criteria (60%)

**Code readability and maintainability**
- ✓ Clear separation of concerns
- ✓ Consistent authorization patterns
- ✓ Self-documenting code structure
- ✓ Low coupling between components
- ✓ Easy to understand and extend

**Working RBAC implementation**
- ✓ Consistent enforcement in backend and frontend
- ✓ No obvious security gaps or privilege escalation
- ✓ Correct HTTP status codes and error handling

### Secondary Criteria (30%)

**Test coverage**
- ✓ Focused tests on critical authorization paths
- ✓ Both allowed and denied scenarios tested
- ✓ Tests are clear and well-named

**Setup and documentation**
- ✓ Setup instructions work on first try
- ✓ Clear explanation of authorization approach
- ✓ Permission matrix documented

### Nice to Have (10%)

- Thoughtful UX for forbidden states
- Observability (logging denied attempts)
- Architecture Decision Records (ADRs)
- Helpful diagrams
- Extra polish

> **Philosophy**: We're evaluating your ability to write production-quality code under time constraints. We'd rather hire someone who delivers clean, working code with good tests than someone who delivers everything but it's hard to maintain.

## Submission

**Deliverables** (see [Repository progress](#repository-progress)):

- [ ] PR or repo link with commit history
- [ ] Updated README with:
  - Setup instructions
  - Permission matrix
  - Brief explanation of your approach
- [ ] Backend tests covering critical authorization scenarios (матрица доступа; сейчас — baseline + схема `role`)
- [ ] Working implementation of RBAC (✅ Epic 0–7 frontend scope + metrics page; финальная end-to-end валидация)
- [ ] Optional: `NOTES.md` with anything you want us to know (scope cuts, trade-offs, what you'd do with more time)

---

**Good luck!** Focus on demonstrating clear thinking and solid engineering fundamentals. We're looking for maintainable code, not perfect code.
