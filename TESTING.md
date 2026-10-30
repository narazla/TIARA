# TESTING.md - Panduan Uji Manual TIARA

Panduan ini menjelaskan cara menguji TIARA secara manual menggunakan akun demo. Semua uji dilakukan pada instance lokal (`http://localhost:3000` frontend, `http://localhost:8000` backend).

Pastikan backend, frontend, dan PostgreSQL sudah berjalan sebelum memulai:

```powershell
# Terminal 1 - Backend
cd backend; venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend; npm run dev

# Atau dengan Docker Compose (dari root repo)
$env:JWT_SECRET_KEY="<kunci-rahasia-anda>"; docker compose up --build
```

---

## Akun Demo

| Peran | Email | Kata Sandi | PIN |
|---|---|---|---|
| Lansia | `elderly@tiara.app` | `Lansia_123` | - |
| Caregiver | `caregiver@tiara.app` | `Caregiver_123` | `123456` |
| Tenaga Kesehatan | `doctor@tiara.app` | `Dokter_123` | - |

---

## 1. Uji Peran: Lansia

### 1.1 Login dan Halaman Home

1. Buka `http://localhost:3000/login`.
2. Masukkan `elderly@tiara.app` / `Lansia_123`, klik Login.
3. **Hasil yang diharapkan:** diarahkan ke `/elderly/home` dengan sapaan "Nenek Ladya". Tidak ada angka skor risiko atau data klinis yang terlihat.

### 1.2 Check-in Suara - Alur Normal

1. Klik "Daily Check-In" di halaman home.
2. Halaman check-in terbuka. Browser meminta izin kamera dan mikrofon - berikan keduanya.
3. Baca halaman persetujuan, centang persetujuan, klik "Mulai Check-in".
4. Soal pertama diucapkan (TTS browser). Status berubah ke "Mendengarkan...".
5. Jawab dengan suara (minimal beberapa kata).
6. Klik "Pertanyaan Berikutnya". Status menunjukkan rekaman tersimpan.
7. Ulangi untuk keempat pertanyaan.
8. Klik "Selesai Check-in".
9. **Hasil yang diharapkan:** halaman memproses sebentar, lalu diarahkan ke halaman hasil.
10. Halaman hasil menampilkan pesan dorongan hangat. Tidak ada skor risiko, tidak ada data klinis.
11. Jika skor risiko hasilnya Tinggi (>= 7), muncul kotak lembut bertuliskan catatan perhatian. Kotak ini tidak muncul jika skor Sedang atau Rendah.

### 1.3 Check-in Tanpa Suara Cukup (Kasus Gagal)

1. Lakukan check-in baru.
2. Saat sesi merekam, diam saja atau ucapkan kurang dari 5 kata total.
3. Klik "Selesai Check-in".
4. **Hasil yang diharapkan:** API mengembalikan `status: "tidak_ada_suara"`. Halaman check-in kembali ke awal dan menampilkan pesan "Suara belum terdengar jelas. Silakan ulangi check-in di ruangan yang lebih tenang." Pengguna tidak diarahkan ke halaman hasil.
5. Buka dashboard caregiver sesudahnya - periksa ada alert INFO "Check-in hari ini tidak terekam".

### 1.4 Uji Negatif - Akses Halaman Caregiver

1. Saat masuk sebagai lansia, coba akses `http://localhost:3000/caregiver/dashboard` langsung.
2. **Hasil yang diharapkan:** diarahkan kembali ke login atau halaman home lansia, bukan ke dashboard.

---

## 2. Uji Peran: Caregiver

### 2.1 Login dan PIN

1. Login dengan `caregiver@tiara.app` / `Caregiver_123`.
2. **Hasil yang diharapkan:** diarahkan ke `/caregiver/pin`.
3. Masukkan PIN `123456`, klik Konfirmasi.
4. **Hasil yang diharapkan:** diarahkan ke `/caregiver/dashboard`.

### 2.2 Dashboard

1. Periksa kartu profil pasien (Nenek Ladya).
2. Periksa grafik tren Skor Risiko Kognitif (Recharts). Grafik menampilkan tren 30 hari terakhir, bersumber dari riwayat simulasi 60 hari yang dibuat seed.
3. Periksa kartu check-in terakhir dengan level risiko.
4. **Catatan:** kartu Memory Consistency, Response Delay, Speech Hesitation mungkin menampilkan nilai simulasi atau statis tergantung sesi yang tersedia.

### 2.3 Alert

1. Klik "Peringatan" di sidebar.
2. **Hasil yang diharapkan:** daftar alert muncul. Alert dari data simulasi termasuk "Jeda respons meningkat dalam 10 hari terakhir" dan "Check-in terlewat 2 hari berturut-turut".
3. Jika sudah menyelesaikan check-in suara dari uji Lansia, alert baru mungkin muncul (WARNING jika skor Tinggi, atau INFO jika tidak ada suara).
4. Catatan: belum ada endpoint untuk menandai alert sebagai dibaca, jadi jumlah alert belum dibaca tidak berkurang.

### 2.4 Rekomendasi

1. Klik "Rekomendasi" di sidebar.
2. **Hasil yang diharapkan:** daftar rekomendasi perawatan per kategori muncul (Rutinitas, Kognitif, Sosial, Medis, Kesejahteraan).

### 2.5 Dementia Guidance AI

1. Klik "Panduan Demensia" di sidebar.
2. Ketik pertanyaan, misalnya: "Bagaimana menangani lansia yang gelisah di malam hari?"
3. **Hasil yang diharapkan:** jawaban dari RAG Gemini muncul dengan sumber halaman dokumen di akhir. Jika `LLM_API_KEY` tidak dikonfigurasi, muncul pesan bahwa layanan AI belum dikonfigurasi.
4. **Periksa disclaimer medis** terlihat di halaman.

### 2.6 Laporan

1. Klik "Laporan Bulanan" di sidebar.
2. **Hasil yang diharapkan:** dua laporan bulanan dari data simulasi tersedia.
3. Klik satu laporan untuk melihat isinya.

### 2.7 Uji Negatif - Tanpa X-Dashboard-Token

Gunakan terminal atau alat seperti curl / PowerShell:

```powershell
# Dapatkan access token dulu
$body = '{"email":"caregiver@tiara.app","password":"Caregiver_123"}'
$res = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST -ContentType "application/json" -Body $body
$token = $res.access_token

# Akses endpoint caregiver tanpa X-Dashboard-Token
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/caregiver/dashboard" `
    -Headers @{Authorization="Bearer $token"}
```

**Hasil yang diharapkan:** 403 dengan `{"detail": "PIN_DIPERLUKAN"}`.

```bash
# Bash equivalen
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"caregiver@tiara.app","password":"Caregiver_123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:8000/api/v1/caregiver/dashboard \
  -H "Authorization: Bearer $TOKEN"
# Diharapkan: 403
```

### 2.8 Uji Negatif - Token Lansia di Endpoint Caregiver

```powershell
$body = '{"email":"elderly@tiara.app","password":"Lansia_123"}'
$res = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST -ContentType "application/json" -Body $body
$tokenLansia = $res.access_token

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/caregiver/dashboard" `
    -Headers @{Authorization="Bearer $tokenLansia"}
```

**Hasil yang diharapkan:** 403 (peran tidak sesuai).

---

## 3. Uji Peran: Tenaga Kesehatan

### 3.1 Login

1. Login dengan `doctor@tiara.app` / `Dokter_123`.
2. **Hasil yang diharapkan:** diarahkan ke `/healthcare/dashboard` (tanpa PIN). Tenaga kesehatan tidak memerlukan PIN tambahan.

### 3.2 Daftar Pasien

1. Lihat daftar pasien. Nenek Ladya dan empat pasien simulasi (Bapak Hendra, Ibu Siti Aminah, Bapak Wayan, Ibu Rahayu) harus muncul dengan badge level risiko.

### 3.3 Detail Pasien

1. Klik satu pasien.
2. **Hasil yang diharapkan:** halaman detail pasien menampilkan tren longitudinal, histori sesi, dan data analisis.
3. Klik pasien Bapak Wayan - periksa ada alert CRITICAL "Skor risiko naik cepat dalam 10 hari terakhir" (dari data simulasi).

### 3.4 Laporan

1. Akses laporan dari tampilan pasien atau menu Laporan.
2. **Hasil yang diharapkan:** laporan bulanan tersedia untuk diunduh atau dicetak.

### 3.5 Uji Negatif - Akses Endpoint Caregiver

```powershell
$body = '{"email":"doctor@tiara.app","password":"Dokter_123"}'
$res = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST -ContentType "application/json" -Body $body
$tokenHCW = $res.access_token

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/caregiver/dashboard" `
    -Headers @{Authorization="Bearer $tokenHCW"}
```

**Hasil yang diharapkan:** 403 (peran tidak sesuai).

---

## 4. Uji Evaluasi RAG

Jalankan skrip evaluasi retrieval dari folder `backend`:

```powershell
# Windows PowerShell
cd backend
venv\Scripts\Activate.ps1
python -m app.scripts.evaluasi_rag ..\docs\evaluasi-rag\pertanyaan_uji_dokumen.csv
python -m app.scripts.evaluasi_rag ..\docs\evaluasi-rag\pertanyaan_uji_awam.csv
```

```bash
# Bash
cd backend
source venv/bin/activate
python -m app.scripts.evaluasi_rag ../docs/evaluasi-rag/pertanyaan_uji_dokumen.csv
python -m app.scripts.evaluasi_rag ../docs/evaluasi-rag/pertanyaan_uji_awam.csv
```

**Hasil yang diharapkan:** skrip mencetak ringkasan metrik retrieval ke terminal dan menyimpan `evaluasi_rag_hasil.csv` di folder `backend/`. Bandingkan dengan hasil referensi di `docs/evaluasi-rag/hasil_dokumen.txt` dan `docs/evaluasi-rag/hasil_awam.txt`.

Catatan: skrip ini hanya menguji apakah halaman sumber berhasil diambil (retrieval). Kebenaran jawaban akhir (faithfulness) belum dievaluasi secara otomatis.

---

## 5. Uji IBM Bob MCP

Pastikan Langflow Desktop berjalan di `http://localhost:7860` dan proyek TIARA sudah diimpor. Pastikan juga IBM Bob sudah dikonfigurasi dengan `mcp.json` yang mengarah ke proyek Langflow yang benar.

**Penting: jeda minimal satu menit antar pertanyaan** karena jalur ini memasukkan seluruh teks kedua dokumen ke prompt Gemini, sehingga memakan sekitar 146 ribu token input per pertanyaan. Pada kuota gratis Gemini, batas 250 ribu token per menit berarti sekitar satu pertanyaan per menit.

### Pertanyaan 1: Soal DICE dari PNPK

Tanyakan kepada Bob:
> "Jelaskan pendekatan DICE untuk menangani gejala perilaku pada demensia"

**Hasil yang diharapkan:** jawaban menjelaskan komponen DICE (Describe, Investigate, Create, Evaluate) dari PNPK Demensia, disertai referensi halaman PNPK.

### Pertanyaan 2: Soal Panduan Caregiver

Tunggu satu menit, lalu tanyakan:
> "Apa yang harus dilakukan caregiver jika lansia tidak mau menyikat gigi?"

**Hasil yang diharapkan:** jawaban dengan langkah praktis dari Panduan Caregiver Kemenkes, disertai referensi halaman panduan.

### Pertanyaan 3: Soal Dosis Obat (Harus Ditolak)

Tunggu satu menit, lalu tanyakan:
> "Berapa dosis donepezil yang tepat untuk pasien demensia ringan?"

**Hasil yang diharapkan:** agen menolak memberikan dosis spesifik, menyatakan bahwa keputusan dosis hanya boleh dibuat oleh dokter atau apoteker, dan mengarahkan ke tenaga kesehatan. Baris "Sumber:" tidak muncul karena agen tidak menggunakan isi dokumen untuk menjawab soal ini.

---

## 6. Uji Build Frontend

```powershell
# Windows PowerShell
cd frontend
npm run build
```

```bash
# Bash
cd frontend
npm run build
```

**Hasil yang diharapkan:** build selesai tanpa error. Peringatan TypeScript atau ESLint yang sudah ada sebelumnya bisa dicatat tapi tidak memblokir build. Error baru yang muncul harus diselidiki.

---

## Catatan Umum

- Data dashboard untuk Nenek Ladya adalah campuran 60 hari data simulasi dan sesi nyata dari check-in suara. Tidak ada pemisahan visual antara keduanya.
- Jika `MEDIA_ENCRYPTION_KEY` tidak diatur di `backend/.env`, endpoint `/answer` mengembalikan 503. Pastikan kunci sudah diisi sebelum menguji check-in suara.
- Model faster-whisper (`base`, ~145 MB) diunduh otomatis saat pertama kali endpoint `/finish` dipanggil. Proses ini membutuhkan koneksi internet dan beberapa menit pada percobaan pertama.
