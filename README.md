# Yayasan Islam Selaparang

Portal resmi Yayasan Islam Selaparang Kediri — pondok pesantren tradisional di Lombok Barat yang memadukan pendidikan agama dan kurikulum formal, dari MI dan MTs hingga MA, Ma'had, dan STIS Syariah.

**Berakar pada ilmu dan akhlak.** Visi yayasan: membentuk generasi berakhlak mulia, berilmu luas, dan mampu menghidupkan nilai Islam dalam kehidupan modern.

## Yang ada di situs

- **Beranda & Profil** — visi, misi, prinsip, dan sejarah yayasan.
- **Jenjang Pendidikan** — tujuh lembaga dari madrasah dasar hingga kajian Islam tingkat tinggi.
- **Artikel & Kegiatan** — kabar, pengajian, dan program masyarakat.
- **Struktur, Fasilitas & Galeri** — pengurus, perpustakaan, asrama putra/putri, dan dokumentasi kegiatan.
- **PPDB Online** — pendaftaran santri baru, 1 April – 10 Juli 2026 · 08.00–18.00 WITA.
- **Kontak** — pesan ke sekretariat lewat formulir situs.

Formulir pendaftaran: https://forms.gle/b979B8YdGVm1Me2t7

## Kontak

- Alamat: Jl. TGH Abdul Hafidz, Kediri, Lombok Barat, Nusa Tenggara Barat
- Email: siimad.ponpesselaparang@gmail.com
- WhatsApp: https://wa.me/087864706565 · Facebook: https://www.facebook.com/manw.selaparangkediri

## Pengelolaan konten

Admin mengelola artikel, kegiatan, jenjang pendidikan, galeri, dan pesan masuk lewat halaman `/admin`. Registrasi pengguna bisa ditutup untuk menjaga akses. Brand situs (nama, tagline, logo, bahasa, site URL) diatur di **Pengaturan → Aplikasi → Brand**; default sudah **Yayasan Islam Selaparang**.

Angka di beranda (`7+` program, `3+` siswa, `100+` pengajar, `0` beasiswa) diambil dari situs sumber dan **perlu dikonfirmasi** sebelum dipakai publik.

## Dijalankan dengan

Aplikasi satu service: Flask + Vue 3 (frappe-ui), SQLite/MySQL/PostgreSQL, dengan konten awal tersimpan di `app/*/seed/*.json`. Detail teknis ada di `CLAUDE.md`.

```bash
uv sync && cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"  # → SECRET_KEY
MIGRATE_ON_BOOT=true uv run python -m app.run  # :8000, set FORCE_HTTPS=false untuk HTTP lokal
```

Wizard first-run di `/setup` (hanya dari localhost / SSH tunnel) menyiapkan database dan akun admin. Konten awal diimpor dengan `uv run python -m app.cli seed-articles`, `seed-activities`, `seed-programs` (idempotent).

## Deploy & keamanan

Docker Compose (`docker compose up --build`) atau cPanel + Caddy; panduan: `docs/deploy-cpanel.md`. Pastikan Caddy mengarah ke `localhost:8000`.

File unggahan di `/uploads/*` dapat diakses publik — jangan simpan berkas sensitif. Beri `app_role=admin` hanya kepada pengelola tepercaya. Pemeriksaan: `uv run pytest`, `uv run ruff check .`.

## Status

Open alpha — skema & kontrak masih bisa berubah; kontribusi berupa perbaikan bug. MIT © 2026 Apriliansyah Idris.
