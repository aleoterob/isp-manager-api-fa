# isp-manager-api-fa

REST API for **ISP Manager**: FastAPI + SQLAlchemy 2 on **PostgreSQL** (Neon-compatible). Authentication uses **access JWTs** and **opaque refresh tokens** in httpOnly cookies, with database-backed sessions and rotation.

---

## Architecture (Summary)

| Layer                    | Role                                                                                                                                                                         |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Feature packages**     | `Auth`, `User`, `Customer`, `Order` — each with its own router / service / repository / schemas / models; code lives under **`app/features/`**.                              |
| **SQLAlchemy + Alembic** | Data access through SQLAlchemy ORM; schema migrations live under **`alembic/`**. The schema mirrors the Nest/Prisma API tables and enum values.                              |
| **Shared HTTP layer**    | `app/main.py`: CORS (`FRONTEND_ORIGINS`), global response envelope, rate limiting, optional Sentry, and app factory for tests. Production fails at startup without origins.  |
| **Global cross-cutting** | Pydantic validation, FastAPI dependencies for JWT / roles / CSRF, global exception handlers, response wrapper, structured Python logging, and optional Sentry SDK reporting. |

All HTTP errors go through the global handlers in **`app/core/errors.py`** with a unified JSON shape; successful responses go through **`EnvelopeRoute`** (wrapper `{ success, data, ... }`). Configuration is centralized in **`app/core/config.py`** and loaded from environment variables / `.env`.

---

## Database (Neon)

- **PostgreSQL** managed in **Neon** (TLS connection string in `DATABASE_URL`).
- The ORM models live under `app/features/**/models.py`; Alembic migrations live in `alembic/versions/`.
- **Optional seed**: `python -m app.db.seed` or `isp-manager-seed` after installing the project.
- **SQL schema and diagram** (reference view in dbdiagram.io): [https://dbdiagram.io/d/ISP-Manager-Schema-69f11828ddb9320fdc7f81c5](https://dbdiagram.io/d/ISP-Manager-Schema-69f11828ddb9320fdc7f81c5)

---

## Run Locally

**Requirements:** Python 3.12+.

Create a **`.env`** file at the repo root. The app loads it at startup and validates critical production requirements.

### `.env` Variables

```env
DATABASE_URL="Ask aleoterob@gmail for the URL (due to GitHub's secret policies for public repositories)."

# JWT
JWT_ACCESS_SECRET="replace-with-a-random-secret-of-at-least-32-characters"

ACCESS_COOKIE_NAME="access_token"
REFRESH_COOKIE_NAME="refresh_token"

# App
NODE_ENV=development
PORT=3000
APP_NAME="isp-manager-api-fa"
JWT_ACCESS_EXPIRES_IN=15m
REFRESH_TOKEN_EXPIRES_IN=7d
COOKIE_MAX_AGE=900000
JWT_ISSUER=isp-manager-api
JWT_AUDIENCE=isp-manager-api
COOKIE_SAMESITE=strict
CSRF_COOKIE_NAME=csrf_token
CSRF_HEADER_NAME=x-csrf-token
FRONTEND_ORIGINS=http://localhost:5173
```

Other accepted keys include **`COOKIE_SECURE`**, **`COOKIE_DOMAIN`**, **`TRUST_PROXY`**, **`SWAGGER_ENABLED`**, **`SENTRY_DSN`**, **`SENTRY_ENABLED`**, and **`SENTRY_SEND_DEFAULT_PII`**.

> **Note:** Do not commit real credentials or secrets. Use private environment variables in real environments and rotate any exposed values.

### Commands

```bash
cd isp-manager-api-fa
python -m pip install -e .[dev]

# Migrations applied against DATABASE_URL
python -m alembic upgrade head

# Optional demo data
python -m app.db.seed

python -m uvicorn main:app --reload --port 3000
```

With the API running locally, interactive documentation is available at **[http://localhost:3000/docs](http://localhost:3000/docs)** when `SWAGGER_ENABLED` is not set to `false`.

### Docker Image (`Dockerfile`)

At runtime, the container needs real **`DATABASE_URL`**, **`JWT_ACCESS_SECRET`**, and the rest of the environment through **`--env-file`** or `-e`.

```bash
docker build -t isp-manager-api-fa .
docker run --rm -p 8080:8080 --env-file .env isp-manager-api-fa
```

The app listens on **`PORT`** in local commands; the Docker image exposes **8080**, aligned with Cloud Run. Before the first startup against a new DB, apply migrations with the same **`DATABASE_URL`**:

```bash
python -m alembic upgrade head
```

---

## Google Cloud Platform (Cloud Run)

This FastAPI service can be deployed to Cloud Run with the same runtime environment contract as the Nest API.

| Resource              | Notes                                                                                                                                                                                                                                                                                                                                                      |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **API service**       | Build from the **Dockerfile** in this repo. The image installs the Python package and starts **Uvicorn** with `main:app`.                                                                                                                                                                                                                                  |
| **Runtime variables** | `DATABASE_URL`, `JWT_ACCESS_SECRET` (>=32 chars), `FRONTEND_ORIGINS` (CSV of SPA origins for CORS/credentials), `NODE_ENV`, `COOKIE_*`, `JWT_*`, `CSRF_*`, `SENTRY_*`. Behind a proxy: **`TRUST_PROXY=true`**. SPA on another hostname: typically **`COOKIE_SAMESITE=none`** + **`COOKIE_SECURE=true`**; cookies use **Partitioned** when `SameSite=None`. |
| **Migrations**        | Run `python -m alembic upgrade head` from CI/CD or a one-off job using the same production `DATABASE_URL` before serving a fresh database.                                                                                                                                                                                                                 |

For production, **`FRONTEND_ORIGINS`** must include every real SPA host that will call the API with credentials. If `NODE_ENV=production` and `FRONTEND_ORIGINS` is empty, startup fails intentionally.

---

## Authentication and Authorization

### Tokens and Cookies

The **access token** is a **JWT** signed with **`JWT_ACCESS_SECRET`**. The payload contains application claims **`sub`** (user UUID), **`email`**, and **`role`**. The signature adds **`iss`** (`JWT_ISSUER`, default `isp-manager-api`), **`aud`** (`JWT_AUDIENCE`, default `isp-manager-api`), **`exp`**, and **`iat`**. It is sent in the httpOnly **`ACCESS_COOKIE_NAME`** cookie (default `access_token`) with **`maxAge`** aligned with **`JWT_ACCESS_EXPIRES_IN`** (default **15 minutes**). **`Authorization: Bearer <jwt>`** is also accepted.

The **refresh token** is not a JWT: it is an **opaque token**. Only the **SHA-256 hash** is stored in **`refresh_sessions`**; the raw value is sent in the **`REFRESH_COOKIE_NAME`** cookie (default `refresh_token`) with a lifetime of **`REFRESH_TOKEN_EXPIRES_IN`** (default **7 days**). This allows session family **rotation**, **reuse** detection, and revocation in **`POST /auth/logout`**.

The **CSRF token** protects mutations when the browser authenticates with cookies. The client gets a token with **`GET /auth/csrf`**; the API sets a non-httpOnly **`CSRF_COOKIE_NAME`** cookie (default `csrf_token`) and returns the same value in `data.token` for cross-origin SPAs. Every mutating method must send **`CSRF_HEADER_NAME`** (default `X-CSRF-Token`) with that value. If the header is missing or does not match the cookie, the API responds with **403 `CSRF_INVALID`**.

### Flow Summary

1. **`GET /auth/csrf`** (public): issues a CSRF token so the SPA can send it in mutations.
2. **`POST /auth/login`** (public + CSRF): validates credentials, creates a **`refresh_sessions`** row (new family), issues the access JWT and refresh cookie, and updates **`lastLoginAt`**.
3. Protected routes require a valid JWT. The dependency looks up the current user in the DB: inactive users are rejected, and role checks use the current DB role.
4. If access expires, the client can call **`POST /auth/refresh`** with the refresh cookie + CSRF: the DB session is validated, rotated, and **new** access + refresh cookies are issued. If reuse is detected, the family is revoked.
5. **`POST /auth/logout`** (CSRF): invalidates sessions and clears cookies.

### Role-Based Authorization

Route dependencies restrict endpoints by role (**ADMIN**, **SUPERVISOR**, **INSTALLER**) to match the Nest guards. Public routes skip JWT authentication.

---

## Error Handling and Validation

| Mechanism                        | Brief description                                                                                                                                                                   |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pydantic schemas**             | Request bodies and query/path parameters are validated at the API boundary. Validation errors are flattened into `errors[]` with `property` and `messages`.                         |
| **Global exception handlers**    | `app/core/errors.py` catches validation errors, invalid JSON, stable business exceptions, `HTTPException`, and DB unique violations where applicable.                               |
| **`AppException` + `ErrorCode`** | Stable `code` + `message` contract in the error JSON, matching the Nest API codes such as `AUTH_INVALID_CREDENTIALS`, `USR_EMAIL_TAKEN`, `CUS_COORDS_MISSING`, and `ORD_NOT_FOUND`. |

**Successful response example (envelope wrapper):**

```json
{
  "success": true,
  "statusCode": 200,
  "statusText": "OK",
  "timestamp": "2026-05-03T15:03:35.850Z",
  "path": "/auth/login",
  "data": {
    "id": "4205f869-ae6a-4e32-9d59-8c70b770989f",
    "name": "Admin User",
    "email": "admin@example.com",
    "phone": "+54 11 1234-1178",
    "role": "ADMIN",
    "active": true,
    "lastLoginAt": "2026-05-03T14:18:50.466Z",
    "createdAt": "2026-05-02T13:57:25.931Z",
    "updatedAt": "2026-05-03T14:18:50.467Z"
  }
}
```

**Validation error example (400):**

```json
{
  "success": false,
  "statusCode": 400,
  "statusText": "Bad Request",
  "timestamp": "2026-05-03T15:05:37.397Z",
  "path": "/users",
  "message": "Validation error",
  "errors": [
    {
      "property": "name",
      "messages": ["String should have at least 1 character"]
    },
    {
      "property": "email",
      "messages": ["Value error, email must be an email"]
    }
  ],
  "code": "VALIDATION_ERROR"
}
```

**Business / auth error example (401):**

```json
{
  "success": false,
  "statusCode": 401,
  "statusText": "Unauthorized",
  "timestamp": "2026-05-02T18:00:00.000Z",
  "path": "/auth/login",
  "message": "Invalid credentials",
  "code": "AUTH_INVALID_CREDENTIALS"
}
```

---

## Global Configuration and Rate Limiting

### Centralized Config

**`app/core/config.py`** centralizes:

- **App**: `APP_NAME`, `PORT`, `NODE_ENV`, CORS / origins, `LOG_LEVEL`, Swagger, Sentry.
- **Database**: `DATABASE_URL` for SQLAlchemy / Alembic.
- **Auth**: JWT, cookies, access/refresh duration, `SameSite`, `Secure`, CSRF names.

### Request Limits

- Default limit: **120** requests per **60 s window**.
- Sensitive auth routes use lower limits in the same 60 s window:
  - **`POST /auth/signup`**: **5** / minute
  - **`POST /auth/login`**: **10** / minute
  - **`POST /auth/refresh`**: **30** / minute
- Mutations that use cookie authentication require CSRF cookie + header and return **403 `CSRF_INVALID`** when invalid.

---

## Observability

- **HTTP / app logs**: Python logging configured from `LOG_LEVEL`.
- **Sentry**: `sentry-sdk` integration. Enabled only with `SENTRY_ENABLED=true` and `SENTRY_DSN`; `SENTRY_SEND_DEFAULT_PII` is disabled unless explicitly configured.

---

## Main Libraries

FastAPI, Starlette, Uvicorn, SQLAlchemy 2, Alembic, psycopg 3, PyJWT, bcrypt, Pydantic v2, python-dotenv, Sentry SDK, pytest, httpx, Ruff.

---

## Tests

```bash
python -m ruff check .
python -m pytest
```

Tests use FastAPI **`TestClient`**, dependency overrides, and an isolated in-memory SQLite database. Coverage mirrors the Nest e2e tests:

| Test file                 | Main coverage                                                                |
| ------------------------- | ---------------------------------------------------------------------------- |
| `tests/test_app.py`       | `GET /` health envelope                                                      |
| `tests/test_auth.py`      | signup, login, `/auth/me`, refresh, logout                                   |
| `tests/test_customers.py` | `GET /customers` (401 without session, list with JWT, bounded `take`)        |
| `tests/test_orders.py`    | `GET/POST /orders` (roles, creation with georeferenced customer, 404 lookup) |

---

## Public App Routes

- **`GET /`**: compatibility with a simple health check.
- **`GET /health/live`**: liveness without external dependencies.
- **`GET /health/ready`**: readiness with a real DB check.

The remaining public routes are in **`Auth`** (`/auth/csrf`, `/auth/login`, etc.). Domain resources mount **`/users`**, **`/customers`**, and **`/orders`**.
