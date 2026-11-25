# Nusa Large Pelago

Website resmi **nusalargepelago.com** — landing, blog, dan area member. Satu
service Flask + SPA Vue 3 di belakang Caddy (tanpa gateway/microservice).
**Status: open alpha** — skema & kontrak masih bisa berubah.
Stack: Flask 3 · SQLAlchemy 2 · Pydantic 2 · Vue 3 · Vite · Pinia · frappe-ui ·
Tailwind · SQLite/MySQL/PostgreSQL · Docker + Caddy.

## Highlights

- **Landing & blog** — halaman publik (hero, program, pilar, sumber daya,
  kemitraan, kontak) + blog (kategori, penulis, waktu baca).
- **White-label & SEO** — brand & logo admin; di-inject server-side ke
  `<title>`/meta/robots/Open Graph.
- **Auth & keamanan** — session + API key, role admin/member, registration
  gate, CSRF, rate limit, CSP/HSTS, audit log, password scrypt.

## Quick Start

```bash
uv sync
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # → SECRET_KEY
uv run python -m app.run                        # waitress :8000
```

`SECRET_KEY` ≥32 char. SQLite default `data/app.db` (git-ignored). Dev HTTP:
`FORCE_HTTPS=false` (default `.env.example` `true` → loop redirect). Setup: `/setup`.

## Development

```bash
uv run pytest
uv run ruff check .
cd frontend && yarn install
yarn dev        # Vite :5173, proxy /api → :8000
yarn build      # → app/static/frontend/
yarn typecheck
```

## License

[MIT](LICENSE) — © 2026 Apriliansyah Idris.