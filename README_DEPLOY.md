# Taland AI — Deploy ke Streamlit Community Cloud (Gratis)

Paket ini berisi semua yang dibutuhkan supaya aplikasi Taland AI
(`app_groq.py`) bisa dibuka lewat link oleh tim, tanpa install apa pun
di laptop mereka.

## Isi paket

| File | Keterangan |
|---|---|
| `app_groq.py` | Aplikasi utama (versi terbaru, sudah cloud-safe) |
| `style.css` | Tampilan aplikasi (opsional, tapi ikutkan) |
| `requirements.txt` | Library yang di-install otomatis di cloud |
| `.gitignore` | Mencegah `.env`, `boiler_db`, dan `data` ikut ter-upload |
| `.streamlit/secrets.toml.example` | Contoh format Secrets (bukan key asli) |
| `README_DEPLOY.md` | File ini |

Yang **TIDAK ADA** di paket ini (dan memang tidak boleh ikut):
`boiler_db/`, folder `data/`, file `.env`, dan `Logo.png`.
`boiler_db` dan `data` berisi dokumen perusahaan — jangan di-upload
ke repo publik. Logo bersifat opsional; kalau mau dipakai, salin
`Logo.png` dari `A:\BoilerAI` ke folder ini dan rename jadi
`logo.png` (huruf kecil semua, karena server cloud membedakan huruf
besar/kecil, sedangkan Windows tidak).

## Yang jalan di versi online — dan yang tidak

**Jalan penuh:** Engineering Chat (penalaran umum), Steam Calculator,
Fuel Calculator, Boiler Sizing, Proposal Generator.

**Tidak jalan online:** jawaban dari dokumen (`boiler_db`). Aplikasi
di cloud tidak punya Ollama dan tidak punya folder dokumen itu.
Kalau ada yang bertanya soal Taland/produk, aplikasi menampilkan
pemberitahuan dan menjawab dengan penalaran umum. Untuk jawaban dari
dokumen, tetap pakai aplikasi di laptop.

**Batas gratis yang perlu diketahui tim:**
- Aplikasi tidur kalau 12 jam tidak ada yang membuka. Begitu ada yang
  membuka link, dia bangun lagi dalam 30–60 detik.
- Key Groq gratis: 200.000 token/hari per model, dipakai bersama
  satu tim. Kalau kena limit (pesan 429), tunggu dan coba lagi.

## Langkah deploy (sekali saja)

### Langkah 1 — Siapkan akun GitHub
Kalau belum punya, daftar gratis di github.com (cukup email +
password). Tidak perlu kartu kredit.

### Langkah 2 — Buat repository baru
1. Di GitHub, klik **New repository**.
2. Nama bebas, contoh: `taland-ai`.
3. Pilih **Public** (yang gratis; 1 repo privat juga boleh, tapi
   Public paling mudah).
4. **Jangan** centang "Add a README" — biarkan repo kosong.
5. Klik **Create repository**.

### Langkah 3 — Upload file paket ini ke repo
1. Di halaman repo yang baru dibuat, klik **uploading an existing file**.
2. Seret semua isi folder paket ini ke sana: `app_groq.py`,
   `style.css`, `requirements.txt`, `.gitignore`, dan folder
   `.streamlit` (berisi `secrets.toml.example`).
3. Klik **Commit changes**.

### Langkah 4 — Deploy di Streamlit Cloud
1. Buka share.streamlit.io dan login dengan akun GitHub yang sama.
2. Klik **Create app** (atau **New app**).
3. Isi: Repository = `taland-ai` (repo tadi), Branch = `main`,
   Main file path = `app_groq.py`.
4. Klik **Deploy**. Tunggu 2–5 menit sampai build selesai.
5. Link aplikasi muncul, bentuknya
   `https://taland-ai.streamlit.app` (nama mengikuti nama repo).
   Bagikan link ini ke tim.

### Langkah 5 — Pasang API key Groq di Secrets
1. Di halaman aplikasi (share.streamlit.io), klik **Manage app**
   (atau titik tiga di kanan atas) → **Settings** → **Secrets**.
2. Tulis persis seperti ini, ganti `gsk_...` dengan key Groq asli:
   `GROQ_API_KEY = "gsk_..."` (tanda petik tetap dipakai).
3. Klik **Save**. Aplikasi restart otomatis.
4. Tes: buka link, tanyakan hitungan steam. Kalau sidebar
   menampilkan "API key Groq terpasang otomatis", berarti beres.

Key Groq bisa dibuat gratis di console.groq.com → menu API Keys.
Jangan pernah menulis key asli di file repo, di chat, atau di
`secrets.toml.example`.

## Kalau ada masalah

- **App tidak mau start / "Error installing requirements":**
  cek `requirements.txt` tidak berubah isinya, lalu di Streamlit
  Cloud klik **Reboot app**.
- **"API key Groq belum dipasang":** Secrets belum terisi atau
  salah ketik. Cek lagi Langkah 5 — key diawali `gsk_` dan tidak
  ada spasi di ujungnya.
- **"Limit gratis Groq habis (error 429)":** jatah harian tim
  habis. Tunggu hari berikutnya, atau cek sisa jatah di halaman
  Limits console.groq.com.
- **Link lambat saat pertama dibuka pagi hari:** normal — aplikasi
  sedang bangun dari tidur (12 jam tanpa pengunjung). Tunggu
  30–60 detik dan refresh sekali.
- **Pertanyaan Taland dijawab penalaran umum:** normal di versi
  online (mode dokumen tidak tersedia). Pakai aplikasi laptop
  untuk jawaban dari dokumen.

## Update aplikasi ke depannya

Setiap ada `app_groq.py` baru dari Cing: upload file itu ke repo
GitHub (timpa file lama) → Streamlit Cloud otomatis deploy ulang
dalam beberapa menit. Tidak perlu ulang Langkah 4–5.
