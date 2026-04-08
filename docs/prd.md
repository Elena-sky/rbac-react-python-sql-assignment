# PRD: RBAC for Fullstack FastAPI Template

## 0. Repository and baseline

**Root of history:** `chore: initial commit — full-stack-fastapi-template baseline` (upstream: [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)).

This document describes the **target** state after RBAC. Below: **as-is** baseline to build from.

### As-is (what the baseline already has)

| Area | State |
|------|--------|
| User model | `User`: `is_superuser: bool`, **no** `role` field / role enum |
| API authorization | JWT, `get_current_user`; privileges — `get_current_active_superuser` in `app/api/deps.py` |
| `GET/POST /api/v1/users/` | Superuser only |
| `PATCH /api/v1/users/me`, `GET /users/me` | Any authenticated user |
| `PATCH/DELETE /api/v1/users/{id}` | Superuser only |
| Metrics / insights | **No** dedicated endpoint or page for the assignment |
| Frontend | Dashboard `/`, Items `/items`, Admin `/admin`; Admin in sidebar and router guard by `is_superuser`; on denial — **redirect** to `/`, no dedicated Access Denied screen |
| Seeds | First superuser from `.env` (`FIRST_SUPERUSER`, etc.), not three roles out of the box |
| Backend tests | Pytest: superuser vs normal user for users/items (template), **no** admin/manager/member matrix |

### To-be (this PRD)

Sections 1–12 define the goal: three roles and the matrix in §3.

---

## 1. Goal

Add **Role-Based Access Control (RBAC)** to the existing full-stack app (FastAPI + React) so that:

* API and UI access is limited by role
* **Backend and frontend behave consistently**
* The design is **extensible and readable in ~5 minutes**

---

## 2. User roles

The system must support three roles:

* **admin**
* **manager**
* **member**

(Replacing the “superuser-only” model with an explicit role field or equivalent — implementer’s choice; see §5.)

---

## 3. Permission matrix (MVP scope)

| Action             | admin | manager | member |
| ------------------ | ----- | ------- | ------ |
| List users         | ✅     | ✅       | ❌      |
| Create user        | ✅     | ❌       | ❌      |
| View metrics       | ✅     | ✅       | ❌      |
| View own profile   | ✅     | ✅       | ✅      |
| Update own profile | ✅     | ✅       | ✅      |
| Update any profile | ✅     | ❌       | ❌      |

---

## 4. Scope (what we implement)

### Backend (FastAPI)

Endpoints to protect (API prefix as in the project, usually `/api/v1`):

1. **GET /users/** — admin, manager
2. **POST /users/** — admin only
3. **GET /metrics/** (or agreed stub name) — admin, manager  
   *Not in baseline — add.*
4. **GET /users/me** — all authenticated
5. **PATCH /users/me** — all authenticated  
   *(Template uses `PATCH`, not `PUT`.)*
6. **PATCH /users/{id}** — admin only  
   *(Template already has `PATCH /users/{user_id}`.)*

### Frontend (React)

* Hide:
  * “Create user” for users without permission (non-admin per matrix)
  * navigation/access to metrics for members
* On direct navigation to a forbidden route — explicit **Access Denied** (baseline only redirects — bring to assignment DoD)
* No silent failure or empty UI without explanation

---

## 5. Architectural approach

### Backend

#### Where authorization lives

**FastAPI dependencies** (in the spirit of current `deps.py`, extend from `is_superuser` checks to roles).

Sketch:

```python
def require_role(*roles):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return dependency
```

Usage:

```python
@router.get("/users")
def list_users(user=Depends(require_role("admin", "manager"))):
    ...
```

#### Storing roles

* DB: `role` column on `User` (Alembic migration on top of baseline schema)
* Enum:

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
```

Mapping with existing `is_superuser` during migration/seeds — optional (e.g. first superuser → `admin`).

### Frontend

* Role and rights via `GET /users/me` (extend `UserPublic` if needed)
* State (context / query cache — as with `useAuth` today)
* Conditional rendering and routing via helper like `canAccess(user, "metrics")`

---

## 6. Architectural principles

* Single responsibility: auth separate from business logic
* Low coupling: roles not smeared across dozens of `if`s
* Easy extension: new role → ideally one matrix / one check layer

---

## 7. Testing (required)

At least 3–5 tests for **critical** cases after roles exist:

| # | Scenario |
|---|----------|
| 1 | admin can create user |
| 2 | manager cannot create user |
| 3 | member does not get list users (403 / contract) |
| 4 | manager sees metrics (200) |
| 5 | member gets 403 on metrics |

*Baseline superuser tests remain useful but do not cover this matrix.*

---

## 8. Non-functional requirements

### Maintainability

* Single pattern: `require_role` (or equivalent)
* Clear dependency names

### Security

* Do not trust the frontend: enforce on backend

### UX

* Hide unavailable actions
* 403 and clear UI message where appropriate

---

## 9. Developer experience

README (root or `docs/`) should include:

### Setup

* backend + frontend + DB (as in `development.md` / Docker — partially documented in baseline)

### Seed

* Users with **admin**, **manager**, **member** (minimum to verify matrix)

### Tests

```bash
cd backend && pytest
```

---

## 10. Documentation

### Required

* Permission matrix table
* Short note: why dependency-based RBAC; how the frontend learns rights

### Optional (bonus)

#### ADR 1 — Why dependencies instead of middleware

**Decision:** FastAPI dependencies on endpoints.

**Why:** explicit, readable, less hidden magic.

#### ADR 2 — Simple RBAC without a policy engine

**Decision:** role-based checks.

**Why:** timebox, low overhead; can add complexity later.

---

## 11. Scope cut strategy (if you run out of time)

Keep:

* backend RBAC
* 3+ narrow tests
* README with matrix and run instructions

Can trim:

* UI polish
* ADRs
* diagrams

---

## 12. Definition of done

* Backend RBAC matches matrix §3
* Frontend hides what it should and blocks direct navigation meaningfully (not only silent redirect)
* 403 on forbidden APIs aligned with UI
* README allows bringing the project up and running seeds/tests
* Tests cover key allow/deny scenarios per role

---

## Evaluation criteria (short)

**Stronger:** simple clean solution, no ACL/overengineering, readable code.

**Weaker:** checks scattered, frontend-only, missing backend enforcement.
