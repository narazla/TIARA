# 07 - Security and Privacy

Dokumen ini merupakan ringkasan keamanan untuk keperluan proyek. Panduan lengkap ada di [`SECURITY.md`](../SECURITY.md) di root repositori.

---

## Autentikasi

- Kata sandi di-hash dengan **bcrypt** sebelum disimpan.
- JWT access token berlaku 60 menit, ditandatangani HS256, bertipe `"access"`.
- Dashboard token caregiver berlaku 30 menit; diterbitkan setelah verifikasi PIN berhasil.

---

## Kontrol Akses Berbasis Peran

`require_role` dependency FastAPI diterapkan di setiap endpoint yang dilindungi. Tiga peran: `elderly`, `caregiver`, `healthcare`. Peran `admin` tercantum di dokumen desain lama tetapi tidak diimplementasikan.

---

## PIN Caregiver dan X-Dashboard-Token

Semua endpoint caregiver memerlukan header `X-Dashboard-Token`. Tanpa header ini, respons adalah 403 dengan detail `"PIN_DIPERLUKAN"`. Token diverifikasi milik akun yang sama dengan JWT utama.

---

## CORS

Dikonfigurasi untuk `FRONTEND_URL` saja. Header `X-Dashboard-Token` ada di daftar header yang diizinkan. Jangan atur `FRONTEND_URL=*` di produksi.

---

## Enkripsi Rekaman

Berkas audio disimpan sebagai `.webm.enc` (enkripsi Fernet, satu berkas per pertanyaan dalam folder session_id). Kunci dari `MEDIA_ENCRYPTION_KEY`. Dekripsi hanya di memori. Kehilangan kunci membuat rekaman tidak bisa dibuka.

---

## Apa yang Tidak Dienkripsi

Teks transkrip di tabel `transcripts` disimpan sebagai plaintext di database PostgreSQL.

---

## Tata Kelola Data

- Data analisis sesi nyata tersimpan di PostgreSQL bersama data simulasi seed.
- Data simulasi ditandai dengan `provider="simulasi-demo"`.
- Jurnal suasana hati dan pilihan kondisi sebelum check-in tersimpan di tabel yang sama (`mood_entries`) tetapi belum ditampilkan ke caregiver.
- Tidak ada kebijakan retensi otomatis di kode saat ini.

## Data yang Keluar dari Server

- Teks pertanyaan chat panduan caregiver dikirim ke Langflow (bila dikonfigurasi) dan ke Gemini API (Google) untuk menyusun jawaban. Sistem tidak menambahkan data pasien ke prompt, tetapi teks apa pun yang diketik caregiver ikut terkirim, sehingga caregiver sebaiknya tidak menulis identitas pasien dalam pertanyaan.
- Audio check-in dan teks transkrip diproses secara lokal oleh faster-whisper dan tidak dikirim ke layanan eksternal.
- Selain unduhan model saat pertama kali dipakai (faster-whisper dan model embedding), tidak ada panggilan yang membawa data pengguna ke luar server selain ke Langflow dan Gemini API di atas.

---

## Yang Belum Ada

- HTTPS di lapisan aplikasi (perlu reverse proxy/hosting untuk produksi)
- Enkripsi teks transkrip di database
- Audit log akses dashboard
- Rate limiting pada endpoint auth
- Notifikasi push, WhatsApp, atau email
- Pemisahan tabel kredensial
- Audit keamanan eksternal

Untuk detail lengkap, lihat [`SECURITY.md`](../SECURITY.md).
