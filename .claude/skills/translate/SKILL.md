---
name: translate
description: >-
  Kanon i18n/terjemahan EN+ID di Minimals — vue-i18n legacy:false di
  frontend plus bahasa aplikasi dari settings backend. Pakai saat menambah
  atau mengubah teks UI, menambah key locale, menerjemahkan view, mengubah
  error dictionary, mengubah opsi bahasa wizard setup, atau menambah bahasa
  baru. Berisi peta file, pola t(), rantai resolusi locale, kontrak backend
  appLang/cookie, dan checklist parity EN/ID.
---

# Translate — Kanon i18n EN/ID di Minimals

Skill ini soal **semua teks yang diterjemahkan**: locale key FE, error
dictionary dari backend, head per-route, dan bahasa default aplikasi.
Sumber kebenaran = kode di `frontend/src/app/{i18n.ts,locales/}` dan
`app/infra/seo.py` (implementasi kanonik: commit `2dd0775`).

Pelengkap: `wiring` (api & error flow), `polish` (cosmetics), `review`.

## Kapan pakai

- **Pakai** saat: tambah/ubah teks view, tambah route/page, tambah endpoint
  yang error-nya tampil di FE, ubah wizard setup, ganti/menambah bahasa.
- **Jangan pakai** untuk: styling (pakai `polish`), data fetching (pakai
  `wiring`), logika bisnis backend.

## Aturan #1

> **Setiap key wajib ada di `en.json` DAN `id.json` — struktur identik,
> placeholder identik.** `vue-tsc` **tidak** memvalidasi `t('key')`: key
> yang hilang baru ketahuan saat runtime (UI menampilkan literal key-nya).

---

## 1. Peta file

| File | Peran |
|---|---|
| `frontend/src/app/i18n.ts` | `createI18n` legacy:false; resolusi + persistensi locale; deklarasi `Window.appLang` |
| `frontend/src/app/locales/en.json` / `id.json` | Kamus — **satu-satunya** tempat teks UI |
| `frontend/src/shared/api/errors.ts` | `getErrorMessage` → `error.<key>` / humanize / `error.generic` |
| `frontend/src/router/index.ts` | `applyHead` (`route.<Name>.*`) + `watch(locale)` re-apply |
| `frontend/src/app/AppShell.vue` | switcher: grup Language di menu avatar + toggle mobile nav |
| `frontend/src/app/breadcrumbs.ts` | label crumb = key `crumb.*` |
| `frontend/src/features/auth/validation.ts` | label password rule = key `auth.passwordRules.*` |
| `frontend/src/features/setup/views/SetupView.vue` | Select bahasa langkah Brand → `setup.run(db, brand, admin, lang)` |
| `app/infra/seo.py` | `SUPPORTED_LANGS`, `get_app_lang`, `save_app_lang`, `_request_lang`, `index_context` (boot `appLang`) |
| `app/infra/setup_dto.py` / `setup_service.py` | `SetupIn.lang`, validasi `unsupported_lang`, seed `settings.appLang` |
| `tests/test_seo.py` / `tests/test_setup.py` | kontrak bahasa: boot, cookie, seed, reject |

## 2. Resolusi locale (FE)

Urutan `storedLocale()` di `i18n.ts` — **yang pertama valid menang**:

1. `localStorage['minimals-lang']` — pilihan user via switcher
2. cookie `minimals-lang` — di-set watch FE, dibaca backend untuk `<html lang>`
3. `window.appLang` — default aplikasi (hasil setup / config `APP_LANG`)
4. `'en'`

`watch(locale, …, { immediate: true })` di `i18n.ts` = **persistensi wajib,
jangan dihapus**: setiap perubahan menulis localStorage + cookie
(`path=/; max-age=31536000; samesite=lax`) + `document.documentElement.lang`.

Dua sumbu **by design** (jangan disamakan):

- `<html lang>` (server) = `_request_lang()` → **cookie** → preferensi
  per pengunjung.
- `window.appLang` = **default app** → `get_app_lang()`: `settings.appLang`
  → config `APP_LANG` → `en`. Pengunjung yang belum pernah memilih ikut
  default; switcher FE langsung override via localStorage.

## 3. Pola pemakaian t()

**Di komponen** (`<script setup>`):

```ts
const { t, locale } = useI18n()
```

```html
<h1>{{ t('auth.signIn') }}</h1>
<FormControl :label="t('field.email')" />
```

- **Reaktivitas**: `t()` di template / `computed` ikut locale otomatis.
  Label yang dibangun sebagai array (mis. `headerMenu` AppShell) **harus
  `computed`** — array statis tidak ter-update saat ganti bahasa.
- **Di luar komponen** (store, router, `errors.ts`) → `i18n.global.t(…)` /
  `i18n.global.te(…)`; dipanggil tiap request jadi selalu segar.
- **Interpolasi**: `t('auth.login.welcome', { name })` — placeholder
  `{name}` harus **persis sama** di value kedua locale.
- **Dynamic key yang sah** (pola sudah ada): `t(rule.label)` (label berisi
  key), `te(key) ? t(key) : fallback` (head router), `` `error.${message}` ``
  (`errors.ts`).
- **Tetap literal — jangan diterjemahkan**: nama bahasa sendiri
  ('English' / 'Bahasa Indonesia'), nama brand, nilai data dari DB
  (role, appRole, status), placeholder contoh (`abdulah@example.com`,
  `127.0.0.1`).

❌ **Dilarang** hardcode teks Inggris di attribute:
`label="Dashboard"`, `title="…"`, `placeholder="Search…"`, `tooltip="…"`,
`aria-label="…"` → semua jadi `:label="t('…')"`.

## 4. Struktur key (nested by area)

`nav.*` · `menu.*` · `crumb.*` · `route.<RouteName>.{title,description}` ·
`field.*` · `auth.*` · `shared.*` · `dash.*` · `setup.*` · `error.*`

- Key FE: **camelCase** (`perPage`, `passwordRules`, `welcomeBack`).
- `error.*`: **snake_case = key wire backend** (`role_not_found`), value =
  kalimat bersih yang enak dibaca (bukan sekadar underscore→spasi).
- Route baru = tambah `route.<Name>.title` + `route.<Name>.description` di
  **kedua** locale (`meta.title`/`meta.description` di `routes.ts` tetap
  sebagai fallback untuk `applyHead`).
- Value murni data (URL, angka) boleh identik di dua locale.

## 5. Error dictionary (backend → FE)

Backend **selalu** kirim `{"message": "<snake_case_key>"}` — tidak pernah
kalimat. Alur `getErrorMessage(e, fallback?)` (`errors.ts`):

1. ada `error.<key>` di locale → `t('error.<key>')` (ikut bahasa)
2. tidak ada → **humanize**: underscore→spasi + kapital pertama
3. respons tanpa message → argumen `fallback`, atau `error.generic`

Aturan:

- Backend mulai `raise ValidationFailed("key_baru")` / `error("key_baru", …)`
  dan key itu **tampil di FE** (view/store/setup) → **tambah
  `error.key_baru` ke kedua locale**. Ekstraksi:
  `rg -U -o 'raise \w+\(\s*"([a-z0-9_]+)"' -r '$1' app framework` dan
  `rg -o 'error\("([a-z0-9_]+)"' -r '$1' app framework` — diff vs blok
  `error.*`.
- **Dynamic DTO key** (`<field>_required`,
  `username_must_be_at_least_3_characters`, `email_invalid_email`) tidak
  bisa dienumerasi → biarkan jatuh ke humanize (sudah terbaca).
- Fallback di store **jangan literal Inggris**:
  `getErrorMessage(e, i18n.global.t('auth.errors.loginFailed'))`.

## 6. Kontrak backend

- `app/infra/seo.py`:
  - `SUPPORTED_LANGS = ("en", "id")` — **tambah di sini** saat bahasa baru.
  - `get_app_lang()` → `settings.appLang` → config `APP_LANG` → `en`;
    **tidak pernah raise** (aman sebelum schema ada / tabel settings hilang).
  - `save_app_lang(session, lang)` dipanggil **di dalam sesi seed setup**
    (`_seed_initial`) — satu transaksi dengan admin + brand.
  - `_request_lang()` → cookie `minimals-lang` → `get_app_lang()` →
    `seo.lang` / atribut `<html lang>`.
  - `index_context()` → `{"brand", "seo", "appLang"}`: `seo` di-pop
    server-side, semua key lain jadi window global (aturan boot payload
    framework) → `window.appLang`.
- Setup: `SetupIn.lang` (default `"en"`, min 2 / max 8) → service
  `strip().lower()` → cek `SUPPORTED_LANGS` →
  `ValidationFailed("unsupported_lang")` **sebelum** kerja DB (setelah
  cek status + validasi brand) → `_seed_initial(…, lang)` menyimpan
  `settings.appLang`.
- Nama cookie **harus sama** di FE dan backend: `minimals-lang`
  (`i18n.ts` ↔ `seo.py` ↔ test). Ganti nama = ganti ketiganya.
- Nilai yang disimpan/divalidasi hanya `"en"`/`"id"`; nama bahasa di UI
  tetap literal.

## 7. Menambah teks baru (checklist)

1. Cari teks hardcoded (§3) → ganti `t('area.keyBaru')`.
2. Tambah `area.keyBaru` ke **`en.json` + `id.json`** (nested, urut konsisten).
3. Ada placeholder? tulis `{nama}` identik di dua value; panggil
   `t('area.keyBaru', { nama })`.
4. Route baru? `route.<Name>.{title,description}` ×2.
5. Error key baru dari backend yang tampil di FE? `error.<key>` ×2 (§5).
6. Verifikasi (§9).

## 8. Menambah bahasa baru (mis. `ja`)

Urutan sentuh:

1. `frontend/src/app/locales/ja.json` (copy `en.json` sebagai kerangka).
2. `i18n.ts`: daftar `SUPPORTED`, `import ja from …`, `messages`.
3. `AppShell.vue`: opsi grup Language + toggle mobile nav.
4. `SetupView.vue`: `langOptions`.
5. `app/infra/seo.py`: `SUPPORTED_LANGS` (config `APP_LANG` otomatis
   ikut valid — `_default_app_lang` mengecek di sini).
6. Test yang meng-hardcode `("en", "id")`.
7. Parity script (§9).

## 9. Verifikasi (wajib sebelum selesai)

```bash
uv run pytest tests/test_seo.py tests/test_setup.py -q   # kontrak bahasa backend
uv run pytest -q                                         # full suite
cd frontend && yarn typecheck && yarn build              # FE
```

Test backend yang mengunci kontrak: `test_setup.py` (seed `id`, default
`en`, reject `fr` → `unsupported_lang`) dan `test_seo.py` (boot
`window.appLang`, cookie menang untuk `<html lang>`, fallback config,
tabel settings hilang).

**Parity/coverage script** — `vue-tsc` tidak menangkap key hilang, jadi
jalankan skrip ini (stdlib saja, dari root repo):

```python
import json, re, pathlib
fe = pathlib.Path("frontend/src")

used = set()
for p in list(fe.rglob("*.ts")) + list(fe.rglob("*.vue")):
    used |= set(re.findall(r"""\b(?:t|te)\(\s*['"]([\w.]+)['"]""",
                            p.read_text(encoding="utf-8")))

def flat(d, p=""):
    o = {}
    for k, v in d.items():
        q = f"{p}.{k}" if p else k
        if isinstance(v, dict): o.update(flat(v, q))
        else: o[q] = v
    return o

en = flat(json.load(open(fe / "app/locales/en.json", encoding="utf-8")))
id = flat(json.load(open(fe / "app/locales/id.json", encoding="utf-8")))

print("missing:", sorted(k for k in used if k not in en) or "ok")
print("parity :", sorted(set(en) ^ set(id)) or "ok")
print("params :", [k for k in en
                   if re.findall(r"\{(\w+)\}", str(en[k]))
                   != re.findall(r"\{(\w+)\}", str(id.get(k, "")))] or "ok")
```

Catatan: key yang dipakai via dynamic (`t(rule.label)`) tidak ter-extract —
itu normal, kebalikannya (key ada di locale tapi tidak ter-extract) bukan
salah. Klaim `error.*` vs backend dicek manual terpisah (§5).

Manual smoke: hard refresh → ganti bahasa via menu avatar → refresh (tetap) →
cek `<html lang>`, `document.title` ikut pindah, cookie `minimals-lang`
muncul. Wizard setup: pilih bahasa di langkah Brand → **seluruh wizard
langsung ikut** (live `locale.value`), dan `settings.appLang` terisi
setelah selesai.

---

## Pitfalls / drift checklist (❌ → ✅)

| ❌ Anti-pattern | ✅ Kanon |
|---|---|
| key ditambah hanya ke `en.json` | ke **kedua** locale + parity script |
| `label="Log out"` literal di template | `:label="t('menu.logout')"` |
| `getErrorMessage(e, 'Login failed')` | `i18n.global.t('auth.errors.loginFailed')` |
| array label statis (computed-less) | `computed(() => [… t() …])` — reaktif ke locale |
| placeholder `{name}` vs `{ Name }` beda antar locale | placeholder identik |
| anggap `window.appLang` menimpa pilihan user | urutan: localStorage → cookie → appLang → en |
| hapus `watch` persistensi `i18n.ts` | jangan — di situ cookie + localStorage + `<html lang>` ditulis |
| ganti nama cookie sepihak | `minimals-lang` di `i18n.ts` + `seo.py` + test |
| backend raise key tampil di FE tanpa `error.*` | tambah ×2 (dynamic DTO key biarkan humanize) |
| terjemahkan data (brand, role, status DB) | biarkan — data, bukan chrome |
| wizard pilih bahasa tapi tidak dikirim | `setup.run(db, brand, admin, lang)` — 4 argumen |
| judul halaman hardcode di `afterEach` | `route.<Name>.*` + fallback `te()` ke meta |
| tambah bahasa = edit hanya `i18n.ts` | sentuh 7 titik di §8 (`SUPPORTED_LANGS` backend termasuk) |
