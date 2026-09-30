---
name: wiring
description: >-
  Kanon integrasi frontend↔backend di Minimals — menghubungkan Vue 3 ke Flask
  /api/v1 lewat axios + Pinia. Pakai saat bikin/ubah data fetching, store,
  form submit, error/loading state, route & auth flow. PENTING: repo ini
  TIDAK memakai data-layer frappe-ui (useCall/createResource) — backendnya
  Flask, bukan Frappe.
---

# Wiring — Kanon Integrasi Vue ↔ Flask di Minimals

Skill ini soal **plumbing**: bagaimana komponen Vue mengambil & mengirim data
ke backend **Flask** (`/api/v1`). Sumber kebenaran = kode yang sudah jalan di
`frontend/src/`.

Skill ini **pelengkap**:

- **`polish`** → cosmetics/presentasi (token, tipografi, pola komponen).
- **`wiring`** (skill ini) → data layer, store, envelope, auth, routing.
- `frappe-ui` provides the **components**; the **data layer is ours**.

## Kapan pakai

- **Pakai** saat: bikin/ubah fetch data, Pinia store, form submit, loading/
  error state, route baru, atau auth/session flow.
- **Jangan pakai** untuk: cosmetics (pakai `polish`) atau logika backend.

## Override paling penting (baca dulu)

> **JANGAN pakai `useCall` / `createResource` / `frappeRequest` / `fetch()`
> langsung.** Itu data-layer frappe-ui yang mengharap backend **Frappe**
> (envelope `{ data }`, `/api/v2/method/...`). Backend repo ini **Flask**.
> Semua request lewat **instance `api` dari `@/shared/api/client`** + **Pinia
> store**.

---

## 1. Layout

```
frontend/src/
├── app/          AppShell.vue, useMediaQuery.ts   — shell, layout, responsive
├── features/
│   └── <name>/
│       ├── routes.ts     RouteRecordRaw[] + meta
│       ├── store.ts      defineStore (setup style)
│       ├── validation.ts (opsional) validator per-field
│       └── views/        *.vue
├── router/
│   ├── index.ts   compose routes, global listeners
│   ├── guard.ts   authGuard + setup gate
│   └── meta.d.ts  deklarasi RouteMeta
└── shared/
    └── api/
        ├── client.ts   axios instance + interceptor
        ├── errors.ts   getErrorMessage
        └── index.ts    barrel
```

Feature = satu domain. Domain baru → folder `features/<name>/` dengan
`routes.ts` + `views/`, lalu daftarkan di `router/index.ts`. Tambahkan
`store.ts` hanya kalau domain itu butuh state sendiri — `features/dashboard/`
tidak punya store karena view-nya cuma baca auth store.

---

## 2. HTTP client

`shared/api/client.ts` sudah dikonfigurasi:

- `baseURL: '/api/v1'` — **panggil rute tanpa prefix** (`api.get('/auth/me')`).
- `withCredentials: true` — cookie session ikut tiap request.
- **CSRF otomatis** — request interceptor fetch `/api/v1/csrf` sekali lalu
  set header `X-CSRFToken` untuk `POST/PUT/PATCH/DELETE`. Kalau server balas
  400 dengan pesan mengandung "csrf", interceptor retry sekali. **Jangan**
  set header CSRF manual di call site.
- **401 global** — response interceptor fire `window` event `'auth:unauthorized'`.
  **Jangan** tangani 401 per-call; `router/index.ts` sudah listen.

Impor dari `@/shared/api` (barrel) atau path langsung. **Jangan** bikin
`axios.create(...)` baru, **jangan** `fetch()` langsung.

### Vite dev proxy

`vite.config.js` proxy `/api` dan `/uploads` ke `VITE_BACKEND_ORIGIN`
(default `http://127.0.0.1:8000`). Relative `baseURL` tetap sama-origin → tidak
perlu CORS saat dev.

---

## 3. Response envelope

| Jenis | Bentuk | Ambil dengan |
|---|---|---|
| Single / mutasi | objek telanjang `T` | `data` |
| List | `{ items: T[] }` | `data.items ?? []` |
| List paginate | `{ items, total, page, perPage }` | `data.items ?? []` |
| Error | `{ message: "snake_case_key" }` | `getErrorMessage(e, fallback)` |

Field **camelCase** (backend presenter map snake→camel). Type response
dideklarasikan **di dalam store** sebagai `interface` (lihat
`features/auth/store.ts` → `AuthUser`). Tidak ada file `types.ts` terpusat.

`getErrorMessage(e, fallback)` sudah humanize key: `invalid_credentials` →
`Invalid credentials`. Selalu pakai, jangan render objek error mentah.

---

## 4. Pinia store — pola kanonik (setup style)

Repo ini memakai **setup/function store**, bukan options store:

```ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/shared/api/client'
import { getErrorMessage } from '@/shared/api/errors'

export interface Thing {
  id: string
  name: string
}

export const useThingStore = defineStore('thing', () => {
  const items = ref<Thing[]>([])
  const loading = ref(false)
  const error = ref('')

  async function fetchAll(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<{ items: Thing[] }>('/things')
      items.value = data.items ?? []
    } catch (e: any) {
      error.value = getErrorMessage(e, 'Failed to load')
    } finally {
      loading.value = false
    }
  }

  async function create(payload: { name: string }): Promise<Thing | null> {
    error.value = ''
    try {
      const { data } = await api.post<Thing>('/things', payload)
      items.value.unshift(data)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, 'Failed to create')
      return null
    }
  }

  return { items, loading, error, fetchAll, create }
})
```

Aturan store:
- `ref` untuk semua state, `return` di akhir — bukan `state:`/`actions:`.
- Type response di-`export` sebagai `interface` di file store yang sama.
- Read: set `loading` + reset `error` di awal, `finally` matikan `loading`.
- Mutasi: **kembalikan hasil atau `null`** supaya view tahu sukses/gagal —
  view yang menangani `toast` dan redirect.
- Update array lokal setelah sukses (`unshift` / map replace / filter).
- Pesan error selalu lewat `getErrorMessage`.

---

## 5. Routing & guard

### `features/<name>/routes.ts`

```ts
import type { RouteRecordRaw } from 'vue-router'

export const thingRoutes: RouteRecordRaw[] = [
  {
    path: '',
    name: 'Thing',
    component: () => import('./views/ThingView.vue'),
    meta: { requiresAuth: true },
  },
]
```

- `component` = lazy `() => import(...)`.
- `meta.requiresAuth` / `meta.guestOnly` — dideklarasikan di `router/meta.d.ts`.

### `router/guard.ts` — dua tahap, urutan itu penting

```ts
export async function authGuard(to: any) {
  const setup = useSetupStore()
  if (setup.status === null) await setup.fetchStatus()
  if (setup.status?.setupRequired) return to.path === '/setup' ? true : '/setup'
  if (to.path === '/setup') return '/'

  const auth = useAuthStore()
  if (!auth.checked) await auth.fetchMe()
  if (to.meta.requiresAuth && !auth.user) return '/login'
  if (to.meta.guestOnly && auth.user) return '/'
  return true
}
```

Setup gate jalan **lebih dulu** — sebelum database ada, `/setup` harus
menghijau semua navigasi. `fetchStatus` fail-open (biarkan `null`) supaya guard
retry di navigasi berikutnya.

### `router/index.ts`

- Susun `routes` dari setiap `*Routes` export, `AppShell` sebagai parent route
  untuk route terautentikasi.
- `router.beforeEach(authGuard)`.
- Global listener `auth:unauthorized` → clear user, redirect ke `/login` kalau
  route sekarang butuh auth.
- `meta` baru wajib ditambah ke `router/meta.d.ts`.

---

## 6. Auth flow

State di `features/auth/store.ts`: `user` / `checked` / `error` + `login`,
`register`, `fetchMe`, `logout`. Guard memanggil `fetchMe()` sekali (dijaga
`checked`) sebelum redirect.

Register/login sukses → backend sudah `login_user`, cookie session langsung
sah. Tidak ada token yang disimpan di frontend.

Logout: `auth.logout()` lalu `router.replace('/login')`.

API key (`X-API-Key`) hanya untuk integrasi service-to-service, bukan flow UI.

---

## 7. Binding state ke UI

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { Button, ErrorMessage, Spinner, toast } from 'frappe-ui'

import { useThingStore } from '@/features/thing/store'

const things = useThingStore()
onMounted(() => things.fetchAll())

async function add() {
  const created = await things.create({ name: 'New' })
  if (created) toast.success('Added')
}
</script>

<template>
  <ErrorMessage v-if="things.error" :message="things.error" />
  <Spinner v-if="things.loading && !things.items.length" />
  <!-- list … -->
</template>
```

- Loading gate di `loading && !items.length` — jangan blank saat refetch.
- `<ErrorMessage :message="..." />` menerima string.
- `<Button :loading="submitting" :disabled="disabled">` untuk submit.
- `toast.*` **setelah** await selesai, hanya kalau hasilnya sukses.
- Submit form: `<form @submit.prevent="onSubmit">` + `<Button type="submit">`.

---

## 8. Ketersediaan komponen

Pinned `frappe-ui@1.0.0-rc.2` (`frontend/package.json`).

**Sudah dipakai & terbukti** di repo ini: `Alert`, `Badge`, `Button`,
`DesktopShell`, `ErrorMessage`, `FormControl`, `FrappeUI`, `FrappeUIProvider`,
`MobileNav`, `MobileNavItem`, `MobileShell`, `PageHeader`, `PageHeaderTitle`,
`Select`, `Sidebar`, `SidebarCollapseToggle`, `SidebarHeader`, `SidebarItem`,
`SidebarSection`, `useColorScheme`, `toast`.

**Ada di rc.2 tapi belum dipakai** — boleh dipakai kalau memang butuh:
`Checkbox`, `Combobox`, `DatePicker`, `Dialog`, `Dropdown`, `HoverCard`,
`MultiSelect`, `Password`, `Popover`, `Radio`, `Rating`, `Slider`, `Spinner`,
`Switch`, `Tabs`, `Textarea`, `TextInput`, `Tooltip`.

**Tidak ada di rc.2** — jangan cari: `Card`, `ListView`, `Input`,
`Autocomplete`, `Input.vue`. `Dialog` sudah include `dismissible`/`showCloseButton`
sebagai prop flat. Grouping menu pakai `{ group, options }`.

Kalau sebuah API tidak ada di versi terpasang, cek
`frontend/node_modules/frappe-ui/src/components/<Name>/types.ts` sebelum
memakai. Kalau ragu, konfirmasi reviewer.

### Ikon

Kanon: string `lucide-<name>` — lewat `icon` / `icon-left` / `icon-right` prop,
atau `<span class="lucide-package size-6" />` di dalam slot. Tanpa import
(di-scan Tailwind). Konstruksi dinamis `` `lucide-${x}` `` **tidak** ter-emit
oleh JIT — pakai literal atau whitelist.

---

## 9. Verifikasi

| Target | Perintah | Root |
|---|---|---|
| Typecheck | `yarn typecheck` | `frontend/` |
| Build | `yarn build` | `frontend/` |
| Dev | `yarn dev` (`:5173`) | `frontend/` |

Tidak ada test runner frontend. Kalau `import` gagal, `yarn install` dulu —
bukan bug kode.

---

## Referensi

- Kode kanonik: `frontend/src/shared/api/{client,errors}.ts`,
  `frontend/src/features/{auth,setup}/store.ts`,
  `frontend/src/router/{index,guard,meta.d.ts}.ts`,
  `frontend/src/app/AppShell.vue`.
- Backend presenter (bentuk payload camelCase): `app/*/presenters.py`.
- Skill lain: `.claude/skills/polish/SKILL.md`.
