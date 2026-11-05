# TENANCY.md — Arsitektur, Maksud & Keputusan Desain

> Dokumen **intent** untuk domain tenancy + billing (`app/tenancy/`,
> `app/plans/`, `app/billing/`, `app/todos/`, frontend
> `features/{tenancy,plans,billing,todos}`)
> supaya agent tidak salah paham saat menyentuh kode. **Kalau kode dan dokumen
> ini bertentangan → kode yang menang**, lalu perbarui dokumen ini.
>
> Konvensi umum (layering, wire format, error contract, CSRF, migrations) tetap
> di [`CLAUDE.md`](CLAUDE.md) — dokumen ini hanya melengkapi, bukan mengganti.

---

## 1. Maksud & Filosofi

Minimals **multi-tenant lewat Organization**. Satu user boleh punya kapasitas
berbeda di tiap org — di org A dia owner, di org B dia cuma member, dan dia
bisa saja tidak ikut org manapun.

**Empat prinsip inti:**

1. **`app_role` global ≠ membership `role` per-org.** Orthogonal, tidak pernah
   mensubstitusi satu sama lain. Membership tidak pernah (dan tidak boleh)
   meng-escalate `app_role`.
2. **Platform = superadmin.** Wizard setup, console Tenancy/Infrastructure/
   Billing-admin, dan account management superadmin-level ada di tangan
   superadmin murni.
3. **Fitur ditentukan subscription org, bukan role orang.** Owner tier
   `community` tidak dapat `advanced_reporting`; member tier `professional`
   tetap dapat fiturnya (sepanjang role-nya memberi akses baca fitur tsb).
4. **Backend adalah sumber kebenaran authorization.** FE hanya menyembunyikan
   menu; setiap endpoint punya guard sendiri.

---

## 2. Dua Konsep Role (JANGAN DICAMPUR)

### A. `User.app_role` — kapasitas di **platform** (kolom string `users.app_role`)

| Nilai | Arti | Dibuat oleh | Scope legacy scaffold |
|---|---|---|---|
| `user` | Pengguna biasa | `/register` (default `app_role="user"`) | Tidak ada console sendiri |
| `admin` | Admin **akun** | superadmin via `PATCH /account/users` | **Hanya** konsol account (`/account/users*`, uploads) |
| `superadmin` | Penguasa platform | setup wizard (`setup_service.py` → `app_role="superadmin"`) | Wizard, Tenancy, Infrastructure, Billing console, read API `/app/*` |

Validasi nilai: `VALID_APP_ROLES = ("user", "admin", "superadmin")`
(`app/account/dto.py`).

### B. Membership `role` — kapasitas di **satu organization** (tabel `memberships`)

| Nilai | Hak di org itu |
|---|---|
| `owner` | Kelola anggota (list/add/remove), baca list invoice org, akses `user-lookup`. **Tidak** bisa pay/void invoice, **tidak** bisa ubah subscription. |
| `member` | Read-only: `GET /organizations/:id`, `GET .../features`, `/my-organizations`. Tidak ada satu pun endpoint tulis. |

> **`MEMBER_ROLES = ("owner", "member")` — TIDAK ADA role `admin` di
> membership.** Kalau Anda menemukan diri menulis guard/pemeriksaan
> membership-`admin`, itu salah.

### Mengapa begitu (keputusan eksplisit, sudah disetujui)

- **User yang daftar lewat `/register` memang `app_role="user"` — itu by
  design.** Kapasitas & fitur orang di sebuah org ditentukan **membership
  role-nya di org itu** (+ tier subscription org), bukan `app_role`-nya.
  Undang user biasa sebagai `owner` → dia **penuh owner di org itu**, tanpa
  pernah jadi (dan tidak perlu jadi) admin platform. Tidak masalah — justru
  desainnya begitu.
- **Wizard & platform dikunci `require_role("superadmin")`, BUKAN `admin`** —
  supaya **tidak merusak legacy scaffold**. Di scaffold asli, `admin` bermakna
  sempit = urusan akun (`/account/*`, uploads). Mencampur `admin` ke
  wizard/tenancy/infra/billing akan merusak pembagian warisan itu. **Jangan
  pernah "memperluas" `admin` ke domain platform.**

### Kombinasi nyata

| Skenario | Console Tenancy/Infra/Billing-admin | Nav Organizations & Billing (tenant) | Add member di org-nya |
|---|---|---|---|
| `app_role=superadmin` | ✅ | ✅ (Biling selalu; Organizations kalau ikut owner) | ✅ (bypass) |
| `app_role=user` + membership `owner` | ❌ | ✅ | ✅ |
| `app_role=user` + membership `member` | ❌ | ❌ (nav disembunyikan) | ❌ 403 |
| `app_role=admin` tanpa membership | ❌ (account console saja) | ❌ | ❌ |

---

## 3. Model Data

```
User ──< Membership >── Organization ── Subscription (1:1, uq organization_id)
 │                            │                 │
 │                            │                 └─ plan_id → Plan (RESTRICT), status,
 │                            │                    feature_flags, started_on, expires_on
 │                            ├── (billing) Invoice
 │                            │     UNIQUE (number), uq (organization_id, period_start)
 │                            │       status: issued → paid | void
 │                            ├── InviteCode (org-scoped; code unique, tanpa expiry)
 │                            │     role: member|owner, created_by tanpa FK
 │                            ├── Todo (org-shared; semua member CRUD)
 │                            │     title, description, completed, due_date,
 │                            │     created_by tanpa FK, created_on/changed_on
 │                            └─ created_by (id pembuat: console actor ATAU
 │                               user self-service; tanpa FK; dihitung kuota)
 └─ app_role ("user"|"admin"|"superadmin")
    default_org_id (nullable, tanpa FK — sengaja, lihat 0002)

Plan (katalog, superadmin-managed) — tier turunan subscription
    name (unique), tier, price (nullable = faktur manual),
    duration_value + duration_unit ("days"|"months"), is_default, is_active,
    features (JSON {key: bool}, key ∈ FEATURE_KEYS)
    → tepat satu default per tier; plan yang dipakai subscription tidak
      bisa dihapus (FK RESTRICT + guard 422 plan_in_use)

AppSetting (shared settings store dari migration 0001 — key unique, dipakai
bersama SEO/registration; kuota tenancy hanya sebuah row di dalamnya)
    members_limit → kuota anggota per org, 0 = tanpa batas (superadmin edit)
```

Konstanta:

| Nama | Nilai | Lokasi |
|---|---|---|
| `PLAN_TIERS` | `("community", "professional")` | `app/plans/models.py` |
| `DEFAULT_TIER` | `"community"` — plan default tier ini dipakai org baru | `app/plans/models.py` |
| `DURATION_UNITS` | `("days", "months")` | `app/plans/models.py` |
| `MAX_PRICE` | `1_000_000_000` — batas harga plan & amount invoice | `app/plans/models.py` |
| `MAX_DURATION` | `3650` — batas `duration_value` | `app/plans/models.py` |
| `SUB_STATUSES` | `("trial", "active", "expired", "cancelled")` | `app/tenancy/models.py` |
| `MEMBER_ROLES` | `("owner", "member")` | `app/tenancy/models.py` |
| `INVOICE_STATUSES` | `("issued", "paid", "void")` | `app/billing/models.py` |
| `FEATURE_KEYS` | `("advanced_reporting", "priority_support", "custom_domain", "todos")` — registry fitur | `app/plans/features.py` |
| `DEFAULT_PROFESSIONAL_FEATURES` | 3 flag legacy (`advanced_reporting`, `priority_support`, `custom_domain`) — seed/migrasi **tidak** memberi fitur baru; fitur baru opt-in | `app/plans/features.py` |
| `DUE_AFTER_DAYS` | `14` | `app/billing/services.py` |
| `GENERATION_ATTEMPTS` | `3` | `app/billing/services.py` |
| `CODE_LENGTH` / `GENERATE_ATTEMPTS` | `8` · `3` (retry saat tabrakan kode unik) | `app/tenancy/services.py` |
| `MAX_ORGS_PER_USER` | `10` — kuota **hanya jalur self-service**; console bebas | `app/tenancy/services.py` |
| `MEMBERS_LIMIT_KEY` / `DEFAULT_MEMBERS_LIMIT` | `"members_limit"` / `0` — kuota anggota **global per app**, `0` = tanpa batas | `app/tenancy/services.py` |
| `TRIAL_DAYS_KEY` / `DEFAULT_TRIAL_DAYS` | `"billing_trial_days"` / `30` — expiry org baru; `0` = tanpa expiry | `app/infra/billing_settings.py` |
| `INVOICE_LEAD_DAYS_KEY` / `DEFAULT_INVOICE_LEAD_DAYS` | `"billing_invoice_lead_days"` / `7` — lead renewal; `0` = auto-renew off | `app/infra/billing_settings.py` |
| `BillingSettings` | frozen dataclass: `trial_days`, `invoice_lead_days` | `app/infra/billing_settings.py` |

Migrasi: `0001_initial.py` (milik **master** — jangan disentuh di feature
branch), `0002_tenancy.py`, `0003_billing.py`, `0004_plans.py`,
`0005_todos.py`.

---

## 4. Matriks Guard per Endpoint

Prinsip penulisan: `if denied := require_x(...): return denied` — `None` =
boleh, tuple = response yang langsung di-return.

### Tenancy (`/api/v1/tenancy/*`)

| Endpoint | Guard |
|---|---|
| `GET /organizations` (list console) | `require_role("superadmin")` |
| `POST /organizations` | `require_role("superadmin")` |
| `GET /organizations/:id` | `require_org_access` — superadmin **atau** member org itu |
| `PATCH /organizations/:id` | `require_role("superadmin")` |
| `GET/PUT /organizations/:id/subscription` | `require_role("superadmin")` |
| `GET /organizations/:id/features` | `require_org_access` |
| `GET/POST /organizations/:id/members`, `DELETE .../:userId` | `require_org_role(org_id, "owner")` |
| `GET /organizations/:id/user-lookup?identifier=` | `require_org_role(org_id, "owner")` |
| `GET/POST /organizations/:id/invite-codes`, `DELETE .../:codeId` | `require_org_role(org_id, "owner")` |
| `POST /invites/redeem` | `@login_required` saja — redeem khusus caller |
| `GET /my-organizations`, `POST /my-organizations`, `PUT /my-organizations/default` | `@login_required` saja |
| `GET /settings`, `PUT /settings` | `require_role("superadmin")` |

### Billing (`/api/v1/billing/*`)

| Endpoint | Guard | Catatan |
|---|---|---|
| `GET /invoices` (console, filter/search/paginated) | superadmin | **Side-effect**: memicu generate invoice (lihat §6) |
| `POST /invoices` | `require_role("superadmin")` | Invoice manual: `organizationId` + `periodStart` (+ `amount` opsional); default = harga configured tier |
| `GET /invoices/:id` | `require_org_role(invoice.organization_id, "owner")` | owner bisa baca invoice org-nya |
| `POST /invoices/:id/pay`, `POST /invoices/:id/void` | `require_role("superadmin")` | owner **tidak** boleh tandai bayar; pay menerima `amount` opsional |
| `GET /organizations/:id/invoices` (paginated) | `require_org_role(org_id, "owner")` | juga memicu generate utk org itu |
| `GET/PUT /settings` | `require_role("superadmin")` | trial days + invoice lead days; PUT parsial |

### Plans (`/api/v1/plans/*`)

| Endpoint | Guard | Catatan |
|---|---|---|
| `GET ""` | `require_role("superadmin")` | katalog paginated (`items,total,page,perPage`); filter opsional `?tier=` + `?search=` (nama) |
| `GET /features` | `require_role("superadmin")` | daftar key registry fitur (untuk editor) |
| `POST ""` | `require_role("superadmin")` | community wajib `price`; professional boleh kosong = faktur manual; `features` divalidasi terhadap registry |
| `PUT /:id` | `require_role("superadmin")` | parsial; tier terkunci bila plan default / dipakai subscription |
| `DELETE /:id` | `require_role("superadmin")` | 422 default_plan_cannot_be_deleted · 422 plan_in_use |

### ToDos (`/api/v1/todos/*`)

| Endpoint | Guard | Catatan |
|---|---|---|
| `GET /organizations/:id` | `require_feature(org_id, "todos")` | paginated (`items,total,page,perPage`); filter `?search=` (judul) + `?completed=` |
| `POST /organizations/:id` | `require_feature(org_id, "todos")` | 201 |
| `PUT /organizations/:id/:todoId` | `require_feature(org_id, "todos")` | parsial; `description`/`dueDate` null = clear; todo org lain → 404 `todo_not_found` |
| `DELETE /organizations/:id/:todoId` | `require_feature(org_id, "todos")` | 204 |

Semua member org berbagi satu daftar (org-shared). `require_feature` sudah
mencakup akses org (401/404/403) lalu menambah 403 `feature_not_enabled`.

### Lain (referensi silang)

| Area | Guard |
|---|---|
| `/account/users*` (CRUD user, search) | `require_role("admin", "superadmin")` — **legacy scaffold: admin = akun** |
| Uploads | `require_role("admin", "superadmin")` |
| Read API `/app/*` | `X-Internal-Token` cocok **atau** session `admin`/`superadmin` |
| Infra/DB/setup write | `require_role("superadmin")` |
| `POST /setup*` | loopback-only (bukan role) |

### Guard tenancy (`app/tenancy/guards.py`)

```
require_org_access(org_id)      → 401 anonim · 404 org tak ada · 403 non-member
                                   (superadmin bypass) · set g.current_org/_membership
require_org_role(org_id, *roles) → bangun di atas access; superadmin bypass;
                                   selain itu membership.role harus ∈ roles
require_feature(org_id, flag)    → akses org + subscription harus grant flag
                                   (superadmin bypass membership, TIDAK bypass subscription)
```

---

## 5. Resolusi Fitur (apa yang user "dapat")

```
GET /organizations/:id/features → resolve_features(org_id):
  sub = subscription(org)
  jika org tidak aktif / status ∉ {trial, active} / expires_on lewat
      → semua FEATURE_KEYS = false
  hasil = {flag: override[flag] ?? plan.features[flag] ?? false
           for flag in FEATURE_KEYS}          # strict registry-only
```

- Registry fitur: `FEATURE_KEYS` (`app/plans/features.py`) — satu-satunya
  sumber kebenaran. Menambah fitur = tambah key di registry; plan lama
  otomatis `false` sampai superadmin mengaktifkannya di Plans console.
- **Strict registry-only**: key yang tidak ada di registry tidak pernah
  muncul di hasil, walau plan/override masih menyimpannya (mis. fitur yang
  sudah dihapus). Override hanya bermakna untuk key registry.
- **Plan yang menentukan fitur** (`plans.features`, JSON `{key: bool}`), bukan
  tier. Dua plan professional boleh punya set fitur berbeda.
- Override per-subscription (`featureFlags` di PUT subscription) tetap ada
  sebagai escape hatch per-org dan **menang** atas plan.
- Fitur = properti **subscription org**, bukan orang.
- Superadmin membypass **membership**, tidak pernah **subscription** — fitur
  mati = mati untuk semua orang.
- **`todos` off by default.** Seed dan migrasi memakai
  `DEFAULT_PROFESSIONAL_FEATURES` (3 flag legacy), bukan seluruh
  `FEATURE_KEYS`; superadmin mengaktifkannya per plan di Plans console.

---

## 6. Billing — Invoice Lifecycle

**Siapa yang dapat invoice:**

- Organization aktif, subscription `trial`/`active`, belum lewat `expires_on`,
  dan **`plan.price` tidak `null`**. Plan tanpa harga = faktur manual:
  auto-generation melewatinya, admin menerbitkan invoice manual.
- **Setiap plan berharga tetap diinvoice walau Rp 0** (community gratis).
  `expired`/`cancelled` tidak diinvoice.
- Amount = `plan.price` **saat invoice dibuat** (snapshot): mengubah harga
  plan tidak menulis ulang invoice lama.
- Panjang periode mengikuti plan (`duration_value` + `duration_unit` = `days`
  atau `months`) dari anchor `started_on`; jatuh tempo
  `DUE_AFTER_DAYS = 14` setelah `issued_on`.

**Expiry org baru:** organization dibuat dengan **plan default community yang
aktif** (`ensure_default_plans` menyemai Community + Professional sekali saat
boot). `expires_on = now + settings.billing_trial_days` (default 30 hari,
`0` = tanpa expiry). Bila tier tidak punya plan default → 422
`default_plan_missing`.

**Ubah subscription:** `PUT /organizations/:id/subscription` wajib `planId`
(404 `plan_not_found`, 422 `plan_inactive`). Tanpa `expiresOn` = **term baru**:
`started_on = now` dan `expires_on = now + plan.duration` (anchor restart agar
periode billing selaras dengan masa berlaku). Dengan `expiresOn` eksplisit,
tanggal disimpan apa adanya dan `started_on` tidak berubah.

**Billing settings:** `GET/PUT /billing/settings` hanya menyimpan `trialDays`
dan `invoiceLeadDays`. `PUT` bersifat **parsial** — minimal satu field; field
yang tidak dikirim tidak berubah. Harga & durasi milik plan, bukan settings.

**Generate otomatis (lazy, di endpoints baca):**

- Terpicu oleh `GET /billing/invoices` (superadmin, semua org) dan
  `GET /billing/organizations/:id/invoices` (owner per-org).
- **Ini side-effect yang sudah disetujui** — GET boleh menulis, asal aman
  race: nomor `INV-YYYY-NNNN` count-based + UNIQUE → race dijembatani
  `GENERATION_ATTEMPTS = 3` loop menangkap `Conflict` (lomba baca tidak
  pernah memunculkan 409 ke client).
- **Renewal window**: bila subscription punya `expires_on` dan
  `now >= expires_on - invoice_lead_days` (default 7, `0` = off), invoice
  periode berikutnya dibuat lebih awal. Tetap maksimal satu periode ke depan
  dan idempoten lewat unique `(organization_id, period_start)`.
- Generate memakai **daftar periode yang sudah ada**, bukan hanya periode
  terakhir: periode yang bolong antara invoice lampau terakhir dan periode
  sekarang ikut dibuat (mis. admin sudah membuat invoice dua bulan ke depan
  secara manual). Backfill historis sebelum invoice pertama tetap tidak ada.
- Query dibatch (3 query total, bukan N+1 per org).

**Invoice manual (superadmin):**

- `POST /billing/invoices` dengan `organizationId` + `periodStart`, plus
  `amount` **opsional**.
- `amount` kosong → `plan.price`; bila plan tidak punya harga (faktur manual)
  → 400 `amount_required`. Organization tanpa plan → 422 `plan_missing`.
- `periodStart` menandai **periode**, lalu di-snap ke siklus plan subscription
  (anchor + kelipatan durasi) — tanggal sembarang tidak bisa membuat periode
  ganda di samping invoice otomatis.
- `period_end` = boundary berikutnya menurut `duration_value`/`duration_unit`
  (bulan clamp akhir bulan; hari tepat N×24 jam), `due_on = start +
  DUE_AFTER_DAYS`.
- 404 org tidak ada · 422 org inactive · 400 periode sebelum subscription ·
  409 bila periode sudah punya invoice.
- Race nomor invoice memakai retry yang sama dengan generate otomatis.

**Transisi status — selalu conditional:**

```
issued ──pay(paidOn?, amount?)──> paid   400 paid_on_in_future kalau masa depan
issued ──void──> void
```

`paidOn` di masa depan ditolak, dengan toleransi **+1 hari** (grace
untuk zona waktu klien) — `paid_on > now + 1 day` → `paid_on_in_future`.

`pay` menerima `amount` opsional (nominal diterima, `0..MAX_PRICE`) yang
menimpa amount invoice; dikosongkan = amount invoice dipertahankan.
`InvoiceRepository.transition_status(...)` = `UPDATE ... WHERE status='from'`
+ rowcount, **amount ditulis dalam UPDATE kondisional yang sama** — dua
pay/void bersamaan tidak pernah menimpa dua kali.

**Pay memperpanjang expiry** (hanya bila subscription sudah punya
`expires_on`): `expires_on = max(expires_on, invoice.period_end)`; status
`expired` kembali `active` bila hasilnya masih di masa depan. `cancelled`
tidak pernah diaktifkan otomatis. Subscription tanpa expiry (legacy /
`trialDays=0`) tidak disentuh.

**Keputusan yang sudah disetujui:**

- Owner **melihat** invoice org-nya, **tidak bisa** pay/void; invoice manual
  hanya superadmin (`POST /billing/invoices`).
- List invoice org **paginated** (`items,total,page,perPage`) — cap 200 tidak
  lagi memotong senyap.

---

## 7. Frontend — Perilaku yang Harus Dipahami

**Active organization (sesi UI)** — tenant-facing UI mengikuti satu org aktif:

- `users.default_org_id` = preferensi persisten (nilai awal). Di-seed
  otomatis saat membership pertama (create self-service / add member /
  redeem invite) dan dibersihkan saat membership itu dicabut — §10.
- `activeOrgId` = pilihan sesi, disimpan per user di **`sessionStorage`**
  (`minimals-active-org:<userId>`). Resolusi: active valid → default valid →
  org pertama. Pilihan basi/nonaktif dibuang saat `fetchMyOrgs`.
- **Login selalu mulai dari default.** Logout dan 401 (`auth:unauthorized`)
  memanggil `resetMyOrgs()` yang menghapus pilihan; reload tab tetap
  mempertahankannya.
- Switcher ada di menu avatar (desktop); di mobile lewat **Settings →
  Organization**. Memilih org men-set active + refetch `activeFeatures`.
  Membuka detail org juga men-sinkronkan active.
- `Current` = active org; `Default` = `users.default_org_id`. **Make default
  tidak memindahkan active** — dua konsep terpisah.

**Nav visibility (`menuStore.ts`)** — `isOwner = currentOrg.myRole === 'owner'`:

| Menu | Syarat |
|---|---|
| Organizations | owner di **org aktif** |
| To-dos | **selalu tampil** — gate fitur ada di halaman, bukan di menu |
| Billing | owner di **org aktif** **atau** `appRole === 'superadmin'` |
| Tenancy, Plans, Infrastructure | `appRole === 'superadmin'` |

Route `/billing` juga memakai `meta.ownerOnly` — non-superadmin tanpa role
owner di org aktif diarahkan ke `/`. Backend tetap sumber kebenaran.

**`myRole` hanya ada di `/my-organizations`** — single-org endpoint tidak
mengirimnya. `MyOrganizationView` sengaja meresolve `org` dari `store.myOrgs`
(bukan `fetchOrg`) supaya role org aktif benar. Jangan "memperbaiki" ini
dengan memakai `fetchOrg` — `myRole` akan selalu kosong.

**Alur Add member (keputusan: TANPA daftar/search user):**

```
Dialog "Add member"
  → input "Email or username" (FormControl, bukan Combobox)
  → debounce 300ms → GET /organizations/:id/user-lookup?identifier=<exact>
  → indikator:
       Checking…                                    (lookup berjalan)
       Badge green "Valid · Nama (@username)"        status "ok"
       Badge blue  "Already a member…"               status "already_member"
       ErrorMessage "No user with that email…"       status "not_found"
  → tombol Add aktif HANYA saat status "ok"
```

- Lookup = **exact match** (`find_by_identifier` → email ATAU username).
  **Tidak ada endpoint yang membolehkan non-admin me-listing user** —
  `/account/users` tetap admin-gated. Jangan menambahkannya.
- `MembersPanel` menerima `canManage` prop; caller menentukan:
  `MyOrganizationView` → `:can-manage="isOwner"`, `OrganizationDetailView`
  (console superadmin) → `:can-manage="true"`.

**Onboarding gate (`router/guard.ts` → `enforceOnboarding`)** — prinsipnya:
*user yang masuk dashboard wajib sudah berada di sebuah organization*:

```
route.requiresAuth && auth.user.appRole === 'user'
  → fetchMyOrgs() sekali (memo lewat myOrgsLoaded; in-flight di-dedupe)
  → punya org  → boleh; kalau sedang di /onboarding → redirect '/'
  → tanpa org  → redirect '/onboarding'
  → myOrgsError (jaringan/gagal) → fail-open, jangan kunci user di luar app
```

- `admin`/`superadmin` **tidak** pernah digate. Route `/onboarding` sendiri
  `meta: { requiresAuth: true, fullscreen: true }` — dirender tanpa sidebar.
- `OnboardingView` dua langkah: **step 1** dua card selectable ("New
  organization" / "Invite code" — native `<button>` ber-token tema, tidak
  ada komponen Card di frappe-ui); **step 2** hanya form terpilih (+ tombol
  Back, kedua form tidak pernah tampil bersamaan). Create =
  `POST /my-organizations` (pembuat otomatis `owner`); redeem =
  `POST /invites/redeem`. Sukses → refresh `myOrgs` → navigasi;
  `alreadyMember: true` dijawab toast info, bukan error.
- **`InviteCodesPanel`** (di `MyOrganizationView`, owner-only): generate
  (role member/owner) → kode 8 karakter ditampilkan sekali + tombol copy →
  list kode aktif + revoke (confirm dialog). Tabel: `invite_codes`, kode
  **unique**, tanpa expiry — rotasi = revoke lalu generate baru.
- **Platform settings (dialog di `OrganizationsView`, console tenancy)** —
  `GET/PUT /tenancy/settings`, satu angka `membersLimit` (0 = no limit).
  Kena quota → backend balas 422 `member_limit_reached` (add-member **dan**
  redeem) — cukup render via `getErrorMessage`, tidak ada state khusus.

**Plans console (`PlansView.vue`, superadmin):** CRUD katalog plan —
list dengan **search nama + pagination** (10/20/50; server-side lewat
`GET /plans?search=&page=&per_page=`). Dialog berisi nama, tier, panjang +
satuan durasi, harga (community wajib, professional boleh kosong = faktur
manual), **toggle per fitur registry** (dari `GET /plans/features`; label via
`tenancy.features.*`, fallback humanized), default, dan aktif. Bila registry
gagal dimuat, field `features` tidak dikirim agar grant plan lama tidak
terhapus diam-diam. Backend menolak aksi tidak valid (nama bentrok, tier
terkunci, hapus default / plan terpakai) dan pesannya dirender lewat
`getErrorMessage`.

**Subscription form (`OrganizationDetailView.vue`, superadmin):** select
**plan** (label nama + durasi, meta tier · durasi · harga/manual), status,
dan expiry opsional. Mengosongkan expiry = term baru (lihat §6). Daftar plan
diambil dari katalog penuh (`/plans?per_page=200`, terpisah dari state list
console); plan yang sedang terpasang tetap tampil walau katalog gagal dimuat.

**ToDos (`ToDosView.vue`)** — menu selalu tampil (keputusan user):

```
tanpa org aktif        → pesan; tidak ada request list
features loading       → Spinner
features error         → ErrorMessage + Retry (fetchActiveFeatures ulang)
flag `todos` off       → kartu upsell; TIDAK ada tombol New
flag `todos` on        → list org-shared: search judul, filter status
                         all/open/done, pagination, dialog create/edit/delete
```

- Store `features/todos` di-reset saat org berganti, logout, dan 401 — list
  org lama tidak boleh tampil walau sesaat.
- Backend tetap sumber kebenaran: flag off → `403 feature_not_enabled`.
- `created_by` dicatat backend (audit); list tidak menampilkan identitas
  pembuat.

**Billing console (`BillingView.vue`, superadmin / owner):**

- Owner: daftar invoice di-scope ke org yang dia owner-i; filter awal =
  **org aktif**. Route `/billing` memakai `meta.ownerOnly`; switch ke org
  non-owner saat halaman terbuka juga redirect ke Dashboard. Backend tetap
  sumber kebenaran.
- Superadmin: semua org; dialog create/settings hanya untuk superadmin.
- Dialog **Billing settings**: hanya `trialDays` dan `invoiceLeadDays` —
  integer ≥ 0. Form mengirim **hanya field yang berubah** (PUT parsial), jadi
  perubahan bersamaan dari superadmin lain tidak tertimpa.
- Dialog **Create invoice**: org dipilih lewat **Combobox dengan pencarian
  server-side** (`GET /tenancy/organizations?search=`, debounce 250 ms, 20 hasil;
  org terpilih selalu ikut di opsi agar labelnya tetap tampil), lalu periode
  (disarankan mengikuti durasi plan: hari atau bulan); `amount` opsional —
  kosong = harga plan, wajib bila plan tidak punya harga.
- Dialog **Mark paid**: `amount` terisi otomatis dari amount invoice dan boleh
  diedit (nominal diterima); dikosongkan = amount invoice dipertahankan.

**Store hygiene yang sudah diterapkan (pertahankan):**

- Seq guard pada semua fetch yang bisa stale (`fetchOrg`, `fetchMembers`,
  `fetchMyOrgs`, `fetchActiveFeatures`, `fetchList`, `fetchPlans`,
  `fetchOrgInvoices`, `lookupMember`, `fetchInviteCodes`) — bump seq saat
  save/reset/logout.
- Dedupe promise in-flight (`fetchMyOrgs`, `fetchActiveFeatures`) supaya
  AppShell + Dashboard + view tidak memanggil 2×. **Mutasi (create/redeem)
  dan enter `/onboarding` memakai `refreshMyOrgs()`** — slot dedupe bisa
  dipegang request yang dimulai *sebelum* perubahan, dan hasilnya akan basi.
- `fetchActiveFeatures` di-key per org: switch org membatalkan hasil org
  lama (seq + org id), bukan hanya dedupe promise.
- Gate onboarding memo list kosong (`myOrgsLoaded`) dan tidak retry saat
  error (fail-open) — karena itu `OnboardingView` punya tombol **Check
  again** (`refreshMyOrgs`): user yang baru di-add owner via add-member
  butuh jalan keluar tanpa hard reload.
- Selalu lewat axios `@/shared/api` — tanpa `axios.create` baru, CSRF/401
  otomatis.

---

## 8. Wire Format — Catatan Khusus Tenancy/Billing

- List biasa: `{"items": [...]}`; paginated: `{"items","total","page","perPage"}`.
- **Presenter `exclude_none=True`** → field null **tidak muncul** di JSON
  (mis. `user-lookup` `not_found` → `{"status": "not_found"}` saja; `myRole`
  absen di list superadmin). Jangan assert key null ada.
- `myRole` di `MyOrganizationOut` hanya untuk `/my-organizations` — presenter
  terpisah dari `OrganizationOut` karena alasan itu (jangan digabung).
- Error key snake_case (`already_a_member`, `last_owner_cannot_be_removed`,
  `paid_on_in_future`, `slug_already_taken`, `invalid_role`, ...).
- **`expiresOn` absen/null** pada `PUT /organizations/:id/subscription`
  berarti **term baru**: `started_on = now`, `expires_on = now + plan.duration`
  (lihat §6). Untuk mempertahankan expiry lama, kirim tanggalnya eksplisit.

---

## 9. Aturan untuk Agent (Anti Salah Paham)

1. **Tidak ada jalur membership → `app_role`.** Undang/role org tidak pernah
   mengubah `app_role`; kenaikan ke `admin`/`superadmin` hanya via superadmin
   di account console. Jangan membuat endpoint/flow yang melakukan itu.
2. **Jangan buka wizard/platform/tenancy/infra/billing-console ke `admin`** —
   alasan legacy scaffold (§2). Guard-nya `require_role("superadmin")` murni.
3. **Jangan tambah endpoint listing user untuk non-admin.** Verifikasi satu
   identifier (`user-lookup`) itu cukup dan disengaja.
4. **Endpoint baru → baris README tabel** (`tests/test_docs.py` gagal kalau
   lupa). Field presenter baru = kontrak API berubah (test contract).
5. **Commit hanya di service.** Integrity/race ditangani lewat `Conflict` +
   `transition_status` conditional / retry — jangan ganti dengan overwrite.
6. **`0001_initial.py` milik master.** Perubahan schema tenancy/billing =
   edit `0002`/`0003` (masih satu fitur, unreleased) atau revisi baru.
7. **Membership = `owner`/`member` saja.** Tidak ada membership-`admin`.
8. Guard per endpoint ditulis eksplisit di §4 — kalau menambah endpoint,
   pilih pola yang sama: tulis → owner, baca-anggota → `require_org_access`,
   console → `require_role(...)`.
9. **Tenant-facing UI mengikuti `currentOrg` (org aktif), bukan
   `myOrgs.some(...)`.** Gate owner, filter Billing, dan fitur memakai org
   aktif; default org hanya nilai awal. Jangan menurunkan ulang ke "owner di
   org mana pun".

---

## 10. Decision Log (sudah disetujui user — jangan dibuka lagi tanpa izin)

| Keputusan | Isi |
|---|---|
| Katalog plan | Domain `app/plans/` — superadmin CRUD `/plans`; tier ∈ `community`/`professional`; satu default per tier; subscription menyimpan `plan_id`, tier diturunkan dari plan; plan default / terpakai tidak bisa dihapus, tier terkunci selama default/terpakai |
| Harga & durasi | Milik **Plan**, bukan billing settings: harga integer ≥ 0, kosong = faktur manual (hanya professional); durasi `days`/`months`; invoice menyimpan snapshot saat dibuat |
| Invoice community | **Tetap dibuat** walau Rp 0 (tidak di-skip per harga) |
| Amount kustom | Create invoice dan mark-paid menerima `amount` opsional; kosong = harga plan; pay menulis amount dalam UPDATE kondisional yang sama |
| List invoice org | owner-scoped **dan** superadmin (deviasi kecil dari pola "console = superadmin", disengaja) |
| Invoice manual | **Ada** — superadmin via `POST /billing/invoices` (`organizationId` + `periodStart` + `amount` opsional); owner tetap tanpa tombol create |
| Pay/void | superadmin saja; pay menerima `amount` opsional dan memperpanjang `expires_on` ke `max(expiry, period_end)` serta mengaktifkan kembali status `expired` |
| Generate invoice | lazy di GET, plus renewal window `invoiceLeadDays` sebelum expiry; retry-on-conflict; plan tanpa harga dilewati |
| Nav tenant | Organizations owner-only; Billing owner + superadmin; Plans superadmin |
| Dialog add member | input exact + indikator validitas, **bukan** search/combobox listing |
| `admin` app_role | tetap scoped ke account console (legacy scaffold) |
| Dashboard gate | `app_role=user` tanpa organization → wajib lewat `/onboarding` |
| Create org mandiri | `POST /my-organizations` — pembuat di-enroll `owner`; jalur console tetap tanpa enroll |
| Kuota org self-service | `MAX_ORGS_PER_USER = 10` — hitung via `organizations.created_by`; console tidak kena; invite tidak dihitung |
| Invite code | 8 karakter tanpa I/L/O/0/1, unique, tanpa expiry; redeem idempoten (`alreadyMember`), role mengikuti kode |
| Kuota anggota | **Satu setting global per app** (`settings.members_limit`), bukan per-tier/per-org — superadmin edit via `GET/PUT /tenancy/settings`; default `0` = tanpa batas; di-enforce di `add_member` + `redeem_invite` (422 `member_limit_reached`); create-org tidak pernah diblokir |
| Trial expiry org baru | Organization baru memakai plan default `community`; `expires_on = now + billing_trial_days` (default 30, `0` = tanpa expiry); `PUT` subscription tanpa `expiresOn` = term baru (`started_on = now`, `expires_on = now + plan.duration`) |
| Billing settings | `GET/PUT /billing/settings` (superadmin) — hanya `trialDays`, `invoiceLeadDays`; default 30/7; `0` = fitur terkait off; PUT parsial (minimal satu field) |
| Active org | Tenant UI mengikuti `activeOrgId` per sesi (`sessionStorage` per tab + per user); `default_org_id` hanya nilai awal/fallback; **Make default tidak memindahkan active** |
| Default org otomatis | `default_org_id` di-seed saat membership pertama (create self-service, add member, redeem) bila masih null; tidak menimpa pilihan yang sudah ada; dibersihkan — bukan dipindah — saat membership org itu dicabut |
| Sesi aktif org | Logout/401 menghapus pilihan active → login berikutnya mulai dari `default_org_id`; reload tab tetap mempertahankan pilihan |
| Gate per org aktif | Nav owner, filter Billing, dan `/billing` `ownerOnly` dievaluasi dari `currentOrg.myRole`; non-owner diarahkan ke `/`; superadmin bypass |
| Billing owner | Owner melihat invoice org-org yang dia owner-i; filter awal org aktif; switch ke org non-owner redirect ke Dashboard |
| ToDos | Fitur registry `todos`, **off by default** (tidak di-backfill ke plan lama); workspace **org-shared** — semua member CRUD, `created_by` audit tanpa FK |
| ToDos UI | Menu selalu tampil; flag off → kartu upsell; backend tetap 403 `feature_not_enabled` |

---

## 11. Test Relevan

| File | Cakupan |
|---|---|
| `tests/test_tenancy.py` | CRUD org, guard matrix, members, `TestUserLookup` (exact lookup + anti-listing), `TestOwnerMembership`, `TestMemberOrganizationAccess`, `TestSelfServiceOrganization`, `TestInviteCodes`, `TestRedeemInvite`, `TestMembersQuota` (guard setting, 0=unlimited, boundary, per-org, redeem + recovery), `TestDefaultOrgLifecycle` (seed saat membership pertama, tidak menimpa, clear saat dicabut) |
| `tests/test_guards.py` | 404-sebelum-403, probe, membership sebelum feature |
| `tests/test_billing.py` | plan-driven amount/duration, amount kustom (create/pay), invoice community Rp 0, invoice lifecycle, `TestConcurrency` (retry numbering + conditional transition), owner invoice access |
| `tests/test_plans.py` | seed default per tier, CRUD guard (superadmin), validasi tier/harga/durasi, default swap, tier lock, hapus default/in-use, wiring subscription → plan |
| `tests/test_todos.py` | guard (401/403 forbidden/403 feature_not_enabled/404), CRUD org-shared (superadmin + member), validasi title/dueDate/empty update, search + filter `completed` + pagination, isolasi lintas org → 404 |
| `tests/test_docs.py` | README ↔ `url_map` sinkron |

**Frontend:** tidak ada unit test; verifikasi = `yarn typecheck` + `yarn build`.
Matriks manual: 1 org, 2+ org, default null, default basi, remove membership,
switch ke org non-owner (Billing redirect), superadmin, dan switch lewat
Settings → Organization di mobile.
