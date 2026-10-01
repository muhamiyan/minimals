# Minimals

Production-ready Flask starter untuk self-hosting di cPanel/VPS di belakang Caddy.
Satu service, satu database, satu container — tanpa gateway, tanpa microservice.

Sudah jadi dan siap pakai: SPA Vue 3 yang di-serve Flask sendiri, auth (session +
API key) dengan role, first-run setup wizard, dan keamanan aktif secara default
(CSRF, rate limit, CSP/HSTS, audit log, scrypt password). Lengkap dengan
Alembic dan structured JSON logging.

| | |
|---|---|
| **Backend** | Flask 3 · SQLAlchemy 2 · Pydantic 2 · Flask-Login · Alembic · waitress |
| **Frontend** | Vue 3 · Vite · Pinia · frappe-ui · Tailwind (TS strict) |
| **Database** | SQLite · MariaDB/MySQL · PostgreSQL |
| **Deploy** | Docker (non-root) + Caddy (TLS) |

## Quick Start

```bash
uv sync
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # → SECRET_KEY
```

`SECRET_KEY` wajib ≥32 karakter; placeholder ditolak dan app refuse boot.
SQLite default ada di `data/app.db` (git-ignored).

```bash
uv run python -m app.run                        # waitress di :8000
MIGRATE_ON_BOOT=true uv run python -m app.run    # migration dulu
```

Untuk dev lokal via HTTP biasa, set `FORCE_HTTPS=false` di `.env` — default
`.env.example` `true`, dan tanpa TLS proxy akan loop redirect.

## First-run Setup

Selama `GET /api/v1/setup/status` melaporkan `setupRequired`, SPA mengarahkan
semua navigasi ke `/setup`: pilih database, tes koneksi, buat administrator.
Wizard menulis `DATABASE_URL` ke `.env`, memigrasi target, dan membuat admin;
kalau target beda dari engine yang jalan, responsnya `restartRequired`.

Endpoint wizard hanya menerima klien loopback, jadi buka dari server
sendiri atau lewat SSH tunnel (`ssh -L 8000:localhost:8000 server` →
`http://127.0.0.1:8000/setup`).

## Development

```bash
uv run pytest
uv run ruff check .

cd frontend && yarn install
yarn dev                     # Vite :5173, proxy /api → :8000
yarn build                   # → app/static/frontend/
yarn typecheck
```

## Production (cPanel/VPS + Caddy)

1. `cd frontend && yarn install && yarn build`
2. `.env` dengan `SECRET_KEY` asli + `DATABASE_URL`
3. Arahkan Caddy (`Caddyfile`) ke `localhost:8000`
4. `TRUSTED_PROXY=true` — hanya di belakang proxy; `X-Forwarded-*` dari peer publik
   tidak pernah dipercaya walau flag aktif
5. `FORCE_HTTPS=true` (default) — Caddy wajib kirim `X-Forwarded-Proto`
6. `uv run python -m app.run`

## Docker

```bash
docker compose up --build
```

Bind `127.0.0.1:8000` saja (Caddy di depan), selalu `MIGRATE_ON_BOOT=true`,
SQLite persist di `./data` (`sudo chown -R 1000:1000 data` di Linux kalau
container user tidak bisa write). Ganti database dari dalam container tidak
persist — env container immutable, pakai `DATABASE_URL` di `.env`.

## Architecture

```
framework/   base classes, API utils, exceptions, extensions, infra, logging
app/
  auth/      User, Role, session auth
  account/   user & role management, API key
  infra/     CSRF, rate limit, roles, security, audit, setup, read API, health
  migrations/  Alembic — alpha: edit 0001_initial.py langsung
frontend/src/
  features/  auth, setup, dashboard
  shared/    satu axios instance untuk semua API call
tests/       pytest; test_docs.py menjaga README ↔ url_map sinkron
```

Tiap domain: `api → dto → services → repositories → models → presenters`, dan
commit hanya di service. Domain memanggil domain lain lewat **service**, bukan
repository/model. Response camelCase, error `{"message": "<snake_case_key>"}`.

Detail lengkap: [`CLAUDE.md`](CLAUDE.md), [`framework/README.md`](framework/README.md).

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user (public, rate-limited) |
| POST | /api/v1/auth/login | Login (public, rate-limited) |
| POST | /api/v1/auth/logout | Logout (session) |
| GET | /api/v1/auth/me | Current user (session) |
| GET | /api/v1/setup/status | First-run setup status (public) |
| POST | /api/v1/setup/db-test | Test DB connection (loopback client only) |
| POST | /api/v1/setup | Run first-run setup (loopback client only) |
| GET | /api/v1/csrf | Fetch CSRF token (public) |
| GET | /api/v1/account/users | List users (admin) |
| GET | /api/v1/account/users/:id | Fetch one user (owner or admin) |
| PATCH | /api/v1/account/users/:id | Update user (admin) |
| GET | /api/v1/account/roles | List roles (admin) |
| POST | /api/v1/account/roles | Create role (admin) |
| PATCH | /api/v1/account/roles/:id | Update role (admin) |
| DELETE | /api/v1/account/roles/:id | Delete role (admin) |
| POST | /api/v1/account/api-keys | Create API key (session) |
| GET | /api/v1/account/api-keys | List API keys (session) |
| DELETE | /api/v1/account/api-keys/:id | Revoke API key (session) |
| GET | /api/v1/app/ping | Liveness of the read API (public) |
| GET | /api/v1/app/users | Cross-service read API (internal token or admin) |
| GET | /api/v1/app/roles | Cross-service read API (internal token or admin) |
| GET | /health | Health check (public) |
| GET | /ready | Readiness check (public) |

## Security notes

Known gaps — baca sebelum eksposur internet:

- `/uploads/*` diserve **tanpa autentikasi**. Jangan taruh file sensitif di
  `app/static/uploads/`
- `POST /api/v1/auth/register` terbuka untuk siapa saja dan langsung login.
  Gate atau disable kalau deployment invite-only
- `/api/v1/setup/status` dan `/health` publik, dan mengekspos engine aktif,
  database URL yang sebagian dimasking, plus metrik per-route
- API key mengautentikasi request read; request mutasi tetap butuh token CSRF
  yang terikat ke session cookie
- Rate limit di-key per IP efektif, hanya untuk route API. SPA asset/route,
  `/uploads/*`, `/health`, `/ready` di-exempt. Set `RATE_LIMIT_STORAGE_URL`
  (mis. `redis://…`) kalau multi-worker
- `TRUSTED_PROXY=true` saja tidak cukup: rewrite `X-Forwarded-*` hanya dipakai
  kalau socket peer juga private/loopback. Kalau app diekspos langsung biarkan
  `false` — dengan `true` dan tanpa proxy, siapa pun bisa memalsukan address
  yang jadi key rate limiting
