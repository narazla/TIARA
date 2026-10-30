# SECURITY.md - Keamanan dan Privasi TIARA

Dokumen ini menjelaskan langkah-langkah keamanan yang benar-benar diterapkan dalam kode TIARA saat ini, batasan yang ada, dan hal-hal yang belum diimplementasikan. Kejujuran tentang batasan lebih penting daripada kesan.

---

## Autentikasi

### Kata Sandi

- Semua kata sandi di-hash menggunakan **bcrypt** sebelum disimpan ke tabel `users`.
- Kata sandi plaintext tidak disimpan di database.

### JWT Access Token

- Token akses ditandatangani dengan HS256 menggunakan `JWT_SECRET_KEY` (disarankan minimal 32 karakter acak; nilai bawaan di `config.py` hanya placeholder dan wajib diganti).
- Payload token berisi: `sub` (user ID), `type: "access"`.
- Token akses berlaku **60 menit** (dikonfigurasi via `ACCESS_TOKEN_EXPIRE_MINUTES`).
- Token dikirim di header `Authorization: Bearer <token>`.
- Token **harus** bertipe `"access"`; token lain ditolak dengan 401.
- Refresh token belum diimplementasikan.

### Dashboard Token Caregiver

- Setelah caregiver memverifikasi PIN, sistem menerbitkan token dashboard terpisah (JWT pendek, TTL 30 menit, `CAREGIVER_DASHBOARD_TOKEN_EXPIRE_MINUTES`).
- Token ini dikirim di header `X-Dashboard-Token` pada setiap permintaan ke endpoint caregiver.
- Backend memverifikasi bahwa token milik akun caregiver yang sama dengan JWT utama; token akun lain ditolak dengan 403.

---

## Kontrol Akses Berbasis Peran (RBAC)

Diterapkan melalui dependency FastAPI (`require_role`) di backend, bukan hanya redirect frontend.

Tiga peran yang ada: `elderly`, `caregiver`, `healthcare`.

| Grup Endpoint | Elderly | Caregiver | Healthcare |
|---|---|---|---|
| `/api/v1/auth/*` | Ya | Ya | Ya |
| `/api/v1/elderly/*` | Ya | Tidak | Tidak |
| `/api/v1/elderly/checkin/*` | Ya | Tidak | Tidak |
| `/api/v1/caregiver/*` | Tidak | Ya + PIN | Tidak |
| `/api/v1/healthcare/*` | Tidak | Tidak | Ya |

Peran `admin` tercantum di dokumen desain lama tetapi tidak diimplementasikan di kode saat ini.

---

## Perlindungan PIN Caregiver

- PIN di-hash dengan **bcrypt** sebelum disimpan ke tabel `caregiver_pins`.
- PIN plaintext tidak pernah disimpan.
- Endpoint caregiver yang memerlukan PIN mengembalikan **403 dengan kode `PIN_DIPERLUKAN`** bila header `X-Dashboard-Token` tidak ada, kadaluarsa, atau milik akun lain.
- Frontend membaca kode `PIN_DIPERLUKAN` dan mengarahkan pengguna ke halaman PIN.
- Kunci sementara: 5 kali PIN salah berturut-turut mengunci verifikasi PIN selama 15 menit (respons 429). Penghitung gagal direset setelah PIN benar. Angkanya diambil dari `PIN_MAX_ATTEMPTS` dan `PIN_LOCKOUT_MINUTES` di `backend/app/core/constants.py`.

---

## CORS

Konfigurasi CORS di `backend/app/main.py`:

- `allow_origins`: nilai dari `FRONTEND_URL` (bisa berisi beberapa origin dipisah koma).
- `allow_origin_regex`: mengizinkan `https://(www\.)?tiaracare\.my\.id` dan `http://localhost:<port>`.
- Header yang diizinkan: `Authorization`, `Content-Type`, `Accept`, `X-Dashboard-Token`.
- Jangan mengatur `FRONTEND_URL=*` di lingkungan produksi.

---

## Enkripsi Rekaman Suara (Saat Disimpan)

- Setiap berkas audio rekaman disimpan dalam format terenkripsi dengan ekstensi `.webm.enc`.
- Enkripsi menggunakan **Fernet** (AES-128-CBC + HMAC-SHA256) dari library `cryptography`.
- Kunci enkripsi dibaca dari variabel lingkungan `MEDIA_ENCRYPTION_KEY` di `backend/.env`.
- Dekripsi dilakukan **hanya di memori** saat pemrosesan; berkas terenkripsi tidak pernah ditulis ulang ke disk dalam bentuk plaintext.
- **Peringatan:** jika `MEDIA_ENCRYPTION_KEY` hilang, semua rekaman terenkripsi menjadi permanen tidak bisa dibuka. Simpan salinan kunci secara aman.
- Ini adalah enkripsi saat disimpan (at rest) saja. Untuk produksi, HTTPS tetap diperlukan untuk enkripsi saat transit.

Cara membuat kunci Fernet baru:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Apa yang TIDAK Dienkripsi

- **Teks transkrip** di tabel `transcripts` disimpan sebagai plaintext di database PostgreSQL.
- Kolom teks lain (jawaban, ringkasan skor, indikator) juga plaintext.
- Enkripsi database atau enkripsi kolom-per-kolom belum diimplementasikan.

---

## Penyimpanan Rahasia

- Semua rahasia (kunci JWT, kunci enkripsi media, kunci API LLM, URL database) disimpan di `backend/.env`.
- File `.env` dan `.env.local` dikecualikan oleh `.gitignore` (baris `.env`, `.env.local`, `.env.*.local`).
- `.env.example` disediakan dengan semua nama variabel tetapi tanpa nilai nyata.
- Jangan pernah hardcode nilai rahasia di dalam kode atau mendorong file `.env` ke repositori.

---

## Persetujuan Pengguna

- Sesi check-in hanya bisa dimulai bila `consent: true` dikirim ke `POST /elderly/checkin/start`.
- Tanpa persetujuan, API mengembalikan 400.
- Waktu persetujuan disimpan di kolom `consent_at` di tabel `checkin_sessions`.

---

## Ringkasan Tata Kelola Data

| Aspek | Kondisi Saat Ini |
|---|---|
| Data yang dikumpulkan | Audio rekaman suara per pertanyaan check-in; transkrip teks; fitur pola bicara; skor risiko; jurnal suasana hati; pesan chat panduan |
| Tempat penyimpanan | Database PostgreSQL (metadata dan analisis); filesystem lokal `MEDIA_STORAGE_PATH` (berkas audio .webm.enc) |
| Siapa yang bisa melihat analisis | Caregiver (via dashboard + PIN); tenaga kesehatan (via dashboard peran) |
| Yang tidak ditampilkan ke lansia | Skor risiko dan data klinis tidak ditampilkan di antarmuka lansia, hanya pesan dorongan hangat |
| Retensi data otomatis | Belum ada kebijakan retensi otomatis di kode. Tidak ada penghapusan terjadwal. |
| Penghapusan akun | Soft delete (flag `is_deleted`) pada tabel `users`; berkas media tidak dihapus otomatis |
| Data simulasi | Sesi berlabel `provider="simulasi-demo"` adalah data buatan dari skrip seed, bukan rekaman nyata |
| Jurnal suasana hati | Disimpan di database tetapi belum ditampilkan ke caregiver maupun tenaga kesehatan |

---

## Yang Belum Ada (Jangan Diklaim)

- HTTPS tidak diterapkan di lapisan aplikasi; perlu dikonfigurasi di reverse proxy atau platform hosting untuk produksi.
- Enkripsi teks transkrip di database belum ada.
- Pemisahan tabel kredensial dari profil pengguna belum dilakukan (semua di tabel `users`).
- Audit log akses dashboard caregiver belum diimplementasikan.
- Rate limiting pada endpoint autentikasi belum diimplementasikan.
- Notifikasi push, WhatsApp, atau email tidak ada; semua alert hanya muncul di dashboard saat dibuka.
- Alur penghapusan data pengguna (permintaan GDPR-style) belum ada.
- Audit keamanan eksternal belum dilakukan. Jangan mengklaim kepatuhan regulasi penuh.
- Sertifikasi keamanan apa pun belum ada.

---

## Cara Melaporkan Masalah Keamanan

Jika menemukan kerentanan keamanan, hubungi tim TIARA secara pribadi sebelum membuat laporan publik.

Kontak: [isi alamat email atau saluran pelaporan tim di sini]

Harap sertakan: deskripsi kerentanan, langkah reproduksi, dampak yang mungkin terjadi, dan saran perbaikan bila ada.
