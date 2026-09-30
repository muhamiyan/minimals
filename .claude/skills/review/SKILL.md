---
name: review
description: >-
  Review & fix workflow untuk Minimals (Flask backend + Vue 3 frontend). Dua
  mode — Review (temukan masalah, lapor ringkas) & Fix (perbaikan kecil
  terfokus). Objeknya git working tree, bukan GitHub/gh. Pakai saat me-review
  perubahan, atau saat diminta "review"/"perbaiki". Menegakkan pola domain
  berlapis existing + disiplin pair-programming (breaking change & migration
  = STOP, minta approval).
---

# Review — Review & Fix Workflow

Skill ini untuk repo **Minimals**: Flask backend (`app/`, `framework/`) +
Vue 3 + Vite frontend (`frontend/`).

- **Review** → cari masalah nyata, abaikan noise, lapor **ringkas** (verdict +
  bullet `path:line`). Bukan linter, bukan style-police.
- **Fix** → perbaikan **kecil, terfokus, reversible**. Kalau tidak kecil atau
  menyentuh breaking/migration → **berhenti & lapor**, jangan paksa.

Sumber kebenaran konvensi = kode existing: `app/account/`, `app/auth/`,
`app/infra/`, `framework/`, `frontend/src/`. Skill `polish` (cosmetics) &
`wiring` (data layer) memegang detail frontend.

## Guardrail pair-programming (override semua)

> Aku coder, user reviewer. **Breaking changes di repo & database migration
> WAJIB dikonfirmasi dulu.** Di **mode Fix**: kalau perbaikan menyentuh
> breaking change, schema/migration (`app/migrations/versions/`, kolom model),
> kontrak API publik, deps, atau config → **JANGAN kerjakan. Bail + lapor**
> sebagai temuan Review supaya user putuskan. Kerja per **phase**; tunggu
> "lanjut" tiap phase. **Ikuti pola fitur existing**, jangan invent gaya baru.

---

## Kapan pakai

- **Pakai** saat: user bilang "review", "cek perubahan", "perbaiki X", atau
  sebelum commit ingin second-pass.
- **Jangan** untuk: menulis fitur besar baru (itu alur normal berfase), atau
  cosmetics murni (pakai `polish`).

---

## Mode A — Review

### Alur

1. **Tentukan scope.** Default = perubahan belum di-commit:
   `git status`, `git diff`, `git diff --staged`. Kalau user sebut path/fitur,
   fokus ke situ. Skim sekali untuk bentuk, lalu baca teliti.
2. **Baca in situ.** Untuk tiap file non-trivial, `Read` konteks sekitar hunk —
   bukan cuma diff. Cari **caller** simbol yang berubah (Grep). Cek **test**
   terkait; kalau logic berubah tanpa test, catat.
3. **Cek history** bila perlu: `git log --oneline -n 5 -- <file>`,
   `git blame -L a,b <file>` untuk regresi.
4. **Jalankan checklist**, bentuk **verdict**, lapor **satu** ringkasan.
   Cap investigasi: ~20 read/grep, ~5 git call. Berhenti kalau sebabnya jelas.

### Checklist backend — layering

Tiap domain: `api.py` / `dto.py` / `services.py` / `repositories.py` /
`models.py` / `presenters.py` + `__init__.py` sebagai public surface.
Urutan: `api → dto → services → repositories → models → presenters`.
Acuan: `app/account/`, `app/auth/`.

| Aspek | ✅ Kanon | ❌ Flag |
|---|---|---|
| **Blueprint** | `BlueprintFactory("account", __name__, url_prefix="/api/v1/account")` | `flask.Blueprint()` langsung |
| **Controller** (`api.py`) | tipis: guard → `Dto.validate(request.get_json(silent=True) or {})` → `Service()` → `ok(Out.from_x(...).to_dict())` | query/business logic di `api.py` |
| **Guard** | `@login_required` lalu `if denied := require_role("admin"): return denied` | cek ownership/role manual bolong |
| **DTO** | subclass `DTOBase`; **setiap field API pakai `field(default, alias="camelCase")` eksplisit** — tidak ada inferensi alias; `@field_validator` raise `ValueError("snake_code")`; `model_config = dict(DTOBase.model_config, extra="ignore")` + `@model_validator` `no_fields_to_update` untuk PATCH | field snake_case tanpa alias (client kirim `fullName` → diam-diam jatuh ke default); `request.json` parsed manual |
| **Error** | service `raise NotFound("user_not_found")` / `Conflict` / `InvalidOperation` dari `framework.exceptions` | `ValueError("snake_code")` di service; pesan error free-form |
| **HTTP status** | exception sudah membawa status (`NotFound`→404, `Conflict`→409, `InvalidOperation`→422, `ValidationFailed`→400) | `return error("...", 404)` padahal service bisa raise |
| **Response** | `ok` / `created` / `no_content` / `error` dari `framework.api`; list non-paginate `ok({"items": [...]})` | `jsonify` manual; paginate lewat `paginate(...)` + `paginated_response(...)` |
| **Presenter** | subclass `PresenterBase`; `from_model(obj, **overrides)`; `.to_dict()` → camelCase | `model_dump()` manual; field snake_case bocor |
| **Service** | `ServiceBase[Repo]`, set `repository_class`; `_commit()` setelah tulis, `_flush()` bila butuh id dulu; `audit_log(action, user_id=…, resource=…)` sebelum `_commit()` | `db.session.commit()` langsung; `commit()` di controller |
| **Repository** | subclass `RepositoryBase[Model]`, set `model`; pakai `get`/`find_one`/`find`/`list`/`add`/`delete`/`count`/`paginate` | `commit()`/`rollback()` di repo; SQL mentah tanpa justify |
| **Cross-domain** | import **service** domain lain | import repo/model domain lain |
| **Typing** | `from __future__ import annotations` + type hints di surface publik | tanpa hint |
| **Paginasi** | `PageIn.validate(request.args)` → `.page` / `.per_page` | parse `request.args` integer manual |

**Wajib dicek per write**: `@login_required` ada, guard role sesuai, `audit_log`
dipanggil, DTO rejecting unknown/empty field.

### Cross-cutting (urut prioritas)

1. **Breaking change / migration** — rename/hapus kolom, ubah kontrak API
   publik, file baru di `app/migrations/versions/`, ubah schema model.
   **Selalu flag + tandai butuh approval user.** Jangan pernah anggap remeh.
2. **Correctness** — logic salah, null path, default keliru, race, ownership
   check yang bisa dilewati.
3. **Security** — ownership bolong, `v-html`/XSS, secret ke client/log, CSRF
   exempt tak sengaja, API key mentah bocor.
4. **Tests** — `pytest` (`tests/`). Logic berisiko tanpa test → flag
   (proporsional; jangan tuntut test untuk 1-liner).
5. **Pattern drift** — tak ikut pola fitur existing (bikin layer baru, skip
   service, pakai `ValueError` di service).

### Verdict & format laporan

- Pimpin dengan **satu baris verdict**: `Aman` / `Nits` / `Concerns`.
- Bullet, tiap temuan sendiri, `path:line` dalam backtick + konsekuensinya.
- **Bahasa lugas** (Indonesia ringkas + English tech term). Tanpa emoji,
  tanpa filler, tanpa tanda tangan.
- Panjang: Concerns ~6–15 baris, Nits ~3–6, Aman 1–3.
- Jujur soal keyakinan: "kelihatannya", "belum kepastikan", "perlu dicek".

Contoh (finding nyata di repo ini saat skill ini ditulis — pakai sebagai
pola laporan, bukan daftar tugas yang masih terbuka):
> **Nits** — error contract bocor ke controller di dua view.
> - `app/account/api.py:55` — `get_user` handle `user is None` sendiri lewat
>   `return error("user_not_found", 404)`, padahal jalur tulis di
>   `services.py:43` sudah `raise NotFound("user_not_found")`. Baca dan tulis
>   bedah aturan; samakan ke service.
> - `app/account/api.py:111` — `delete_role` cek `service.get_role(role_id)
>   is None` dulu, lalu `service.delete_role` (`services.py:124`) cek lagi
>   dan `raise NotFound` sendiri. Dua query untuk satu request, dan status
>   mapping terpecah antara `error()` dan exception handler.

### Yang JANGAN di-flag

- Nits yang ruff / vue-tsc sudah tangkap.
- Selera pribadi ("aku akan struktur beda").
- Apa pun yang tak bisa ditaut ke file:line / konsekuensi konkret.
- Frontend cosmetics → pakai `polish`. Data layer → `wiring`.

---

## Mode B — Fix

Fix mode = tracer bullet: **kecil, terfokus, satu perubahan logis**.

### Cocok untuk

- Typo, docstring, dead link, `console.log` tertinggal.
- Bug 1-file dengan root cause jelas & blast radius sempit.
- Menambah guard/audit/validasi yang jelas hilang **tanpa** ubah kontrak.

### WAJIB bail (jangan kerjakan, lapor sebagai temuan)

- **Breaking change / DB migration / schema** → butuh approval user.
- Ubah **kontrak API publik** (rename field response, hapus endpoint).
- Sentuh **deps/config**: `package.json`, `pyproject.toml`, lockfile,
  `alembic.ini`, `app/config.py`, `.env*`, `tailwind.config.js`, `vite.config.js`.
- Perubahan **arsitektural** / komponen baru / butuh design tradeoff.
- Ubah guardrail pair-programming.
- Diff membengkak (>~150 baris / >5 file) atau kamu tidak yakin.

### Disiplin

1. **Diff minimal.** Tak ada cleanup oportunistik, tak ada rename-sekalian.
2. **Ikut pola existing** (layer, penamaan, envelope).
3. **Verifikasi** setelah edit: `uv run pytest`; `cd frontend && yarn typecheck`.
   Catat kalau tidak dijalankan.
4. `git diff` sanity — kalau menyentuh path denylist di atas → **stop & bail**.
5. Lapor ringkas: apa yang diubah (`file:line`), kenapa aman, apa yang **tidak**
   dikerjakan (mis. "test belum ditambah", "butuh approval untuk migration").

---

## Perintah verifikasi

| Target | Perintah | Root |
|---|---|---|
| Backend test | `uv run pytest` | repo |
| Backend lint | `uv run ruff check .` | repo |
| Frontend typecheck | `yarn typecheck` | `frontend/` |
| Frontend build | `yarn build` | `frontend/` |
| Dev server | `yarn serve` (backend `:8000`) + `yarn dev` (Vite `:5173`, proxy `/api`) | repo / `frontend/` |

Tidak ada test runner frontend — verifikasi FE via `typecheck` + `build`.

---

## Referensi

- Fitur acuan: `app/account/` (api/dto/services/repositories/models/presenters),
  `app/auth/`.
- Cross-domain infra: `app/infra/` (`audit`, `csrf`, `rate_limit`, `roles`,
  `security`, `api_key_auth`, `setup`).
- Framework: `framework/base/` (DTOBase, PresenterBase, ServiceBase,
  RepositoryBase), `framework/api/` (BlueprintFactory, response, pagination),
  `framework/exceptions/`, `framework/auth/helpers.py`, `framework/infra/errors.py`.
- Registrasi app: `app/create_app.py` — urutan init, import model, blueprint,
  `register_spa`, `register_error_handlers`.
- Skill lain: `.claude/skills/polish/SKILL.md`, `.claude/skills/wiring/SKILL.md`.
