# 09 - Demo Script

## Skrip Demo Kompetisi

**Estimasi durasi**: 8-10 menit
**Prasyarat**: backend, frontend, dan PostgreSQL berjalan; seed sudah dijalankan.

**Akun demo** (hanya untuk penggunaan lokal):

| Peran | Email | Kata Sandi | PIN |
|---|---|---|---|
| Lansia | `elderly@tiara.app` | `Lansia_123` | - |
| Caregiver | `caregiver@tiara.app` | `Caregiver_123` | `123456` |
| Tenaga Kesehatan | `doctor@tiara.app` | `Dokter_123` | - |

**Catatan penting tentang data**: grafik tren di dashboard caregiver menampilkan campuran 60 hari data simulasi (dari seed) dan sesi check-in nyata (dari rekaman suara). Saat demo, sebutkan secara jujur bahwa sebagian data adalah simulasi untuk demonstrasi.

---

## Adegan 1: Halaman Utama (60 detik)

**URL**: `http://localhost:3000`

**Narasi**:
> "TIARA adalah platform pemantauan kognitif berbasis AI untuk lansia dan keluarga mereka. Setiap hari, keluarga kesulitan mendeteksi tanda-tanda perubahan kognitif dini pada orang tua mereka. TIARA membawa pemantauan dini ke dalam kehidupan sehari-hari melalui check-in suara yang sederhana."

**Tunjukkan**:
1. Hero section
2. Tiga kartu pengalaman pengguna (lansia, caregiver, tenaga kesehatan)
3. Klik "Mulai" menuju halaman login

---

## Adegan 2: Login Lansia (30 detik)

**URL**: `http://localhost:3000/login`

**Narasi**: "Masuk sebagai Nenek Ladya, pengguna lansia demo."

**Tindakan**:
1. Masukkan `elderly@tiara.app` / `Lansia_123`
2. Klik Login
3. Diarahkan ke `/elderly/home`

---

## Adegan 3: Halaman Home Lansia (45 detik)

**URL**: `http://localhost:3000/elderly/home`

**Narasi**:
> "Ini halaman home Nenek Ladya. Tampilannya sengaja dibuat hangat dan sederhana. Tidak ada angka risiko, tidak ada data klinis yang terlihat oleh lansia."

**Tunjukkan**:
1. Sapaan personal "Selamat datang, Nenek Ladya"
2. Status check-in hari ini
3. Dua tombol besar: Daily Check-In dan TIARA Companion

---

## Adegan 4: Persetujuan Check-in (30 detik)

**URL**: `http://localhost:3000/elderly/check-in`

**Narasi**:
> "Check-in memerlukan persetujuan merekam suara sebelum dimulai. Video hanya digunakan sebagai pratinjau lokal di browser; tidak dikirim ke server dan tidak dianalisis."

**Tindakan**:
1. Klik "Daily Check-In"
2. Halaman check-in muncul dengan pratinjau kamera
3. Baca persetujuan, centang, klik "Mulai Check-in"
4. Browser meminta izin kamera dan mikrofon; berikan keduanya

---

## Adegan 5: Jawab Pertanyaan dengan Suara (90 detik)

**Narasi**:
> "TIARA mengucapkan setiap pertanyaan. Lansia menjawab dengan suara. Ada empat pertanyaan dalam satu sesi. Audio direkam per pertanyaan."

**Tindakan**:

**Pertanyaan 1 - Orientasi:**
1. TTS browser mengucapkan "Hari apa sekarang, Bapak/Ibu?"
2. Jawab dengan suara (beberapa kalimat)
3. Klik "Pertanyaan Berikutnya"

**Pertanyaan 2 - Daya Ingat:**
1. TTS mengucapkan pertanyaan makanan pagi
2. Jawab dengan suara
3. Klik "Pertanyaan Berikutnya"

**Pertanyaan 3 dan 4**: lanjutkan dengan cara yang sama.

---

## Adegan 6: Selesaikan Check-in (45 detik)

**Narasi**:
> "Setelah semua pertanyaan dijawab, sistem memproses rekaman: mendekripsi berkas audio, mentranskrip dengan faster-whisper, menghitung fitur pola bicara, lalu membuat Skor Risiko Kognitif."

**Tindakan**:
1. Klik "Selesai Check-in"
2. Tampilkan status "Memproses sesi..."
3. Halaman hasil muncul otomatis

---

## Adegan 7: Halaman Hasil Lansia (30 detik)

**URL**: `http://localhost:3000/elderly/check-in/result`

**Narasi**:
> "Halaman hasil menampilkan pesan dorongan, bukan skor risiko. Caregiver melihat data lengkap secara terpisah di dashboard mereka. Jika skor hari ini Tinggi, kotak catatan lembut muncul di sini."

**Tunjukkan**:
1. Pesan dorongan positif
2. Kotak perhatian (hanya muncul jika skor Tinggi; kalau tidak muncul, jelaskan bahwa skor hari ini tidak Tinggi)
3. Klik "Kembali ke Home"

---

## Adegan 8: Masuk Dashboard Caregiver (45 detik)

**Narasi**:
> "Dari perangkat yang sama, caregiver mengakses dashboard. Dashboard memerlukan PIN terpisah agar data klinis tidak terlihat oleh lansia yang menggunakan perangkat yang sama."

**Tindakan**:
1. Klik dropdown profil (pojok kanan atas)
2. Klik "Dashboard" - diarahkan ke `/caregiver/pin`
3. Masukkan PIN `123456`
4. Diarahkan ke `/caregiver/dashboard`

---

## Adegan 9: Dashboard Caregiver (90 detik)

**URL**: `http://localhost:3000/caregiver/dashboard`

**Narasi**:
> "Dashboard menampilkan tren Skor Risiko Kognitif 30 hari terakhir. Sebagian data adalah simulasi untuk demo; sesi nyata dari check-in tadi juga masuk ke grafik yang sama."

**Tunjukkan**:
1. Kartu profil pasien: Nenek Ladya
2. Kartu check-in terakhir dengan level risiko
3. Grafik tren Skor Risiko Kognitif (Recharts)
4. Sebutkan: "Ini campuran data simulasi dan sesi nyata. Produksi akan memisahkan keduanya."

---

## Adegan 10: Peringatan (30 detik)

**URL**: `http://localhost:3000/caregiver/alerts`

**Narasi**:
> "TIARA membuat peringatan otomatis berdasarkan sesi check-in. Alert dari sesi tadi mungkin sudah muncul di sini."

**Tunjukkan**:
1. Daftar alert dengan badge level (INFO/WARNING)
2. Contoh alert: "Jeda respons meningkat dalam 10 hari terakhir" (dari data simulasi)
3. Jika ada alert dari sesi tadi, tunjukkan juga
4. Sebutkan: "Tidak ada push notification atau email. Peringatan hanya muncul saat caregiver membuka dashboard."

---

## Adegan 11: Rekomendasi dan Laporan (30 detik)

**Tunjukkan**:
1. Halaman Rekomendasi: daftar rekomendasi per kategori (Rutinitas, Kognitif, Sosial, Medis)
2. Halaman Laporan: dua laporan bulanan dari data simulasi

---

## Adegan 12: Dementia Guidance AI (60 detik)

**URL**: `http://localhost:3000/caregiver/guidance`

**Narasi**:
> "Caregiver bisa bertanya langsung ke AI berbasis dokumen resmi Kemenkes. Jawaban diambil dari PNPK Tata Laksana Demensia dan Panduan Caregiver Kemenkes menggunakan pencarian vektor FAISS."

**Tindakan**:
1. Klik "Panduan Demensia" di sidebar
2. Ketik: "Bagaimana cara menangani lansia yang gelisah di malam hari?"
3. Tunjukkan jawaban dengan referensi halaman di akhir
4. Tunjukkan disclaimer medis
5. Coba pertanyaan tentang dosis obat - tunjukkan bahwa AI menolak memberikan dosis

---

## Adegan 13: Tenaga Kesehatan (45 detik)

**Narasi**: "Terakhir, tampilan tenaga kesehatan."

**Tindakan**:
1. Logout, login sebagai `doctor@tiara.app` / `Dokter_123`
2. Diarahkan ke `/healthcare/dashboard`
3. Tunjukkan daftar 5 pasien dengan badge risiko berbeda
4. Klik Bapak Wayan - tunjukkan alert CRITICAL (dari data simulasi)
5. Tunjukkan tren longitudinal dan riwayat sesi

---

## Pernyataan Penutup

**Narasi**:
> "TIARA menghubungkan rumah dan klinik. Keluarga mendapat alat untuk mendeteksi perubahan lebih awal, caregiver mendapat wawasan untuk bertindak, dan tenaga kesehatan mendapat data longitudinal yang lebih kaya. Semua ini sambil menjaga pengalaman lansia tetap hangat dan bermartabat. TIARA bukan alat diagnosis medis. Skor yang dihasilkan adalah indikator informatif dari pola bicara, bukan diagnosis, dan belum divalidasi secara klinis."

---

## Cadangan Demo

### Jika kamera atau mikrofon tidak tersedia
- Gunakan sesi yang sudah selesai dari data simulasi
- Tunjukkan dashboard dengan data yang sudah ada
- Jelaskan alur check-in suara secara verbal

### Jika pipeline lebih lambat dari biasa
- Model faster-whisper diunduh saat pertama dipakai (~145 MB). Pastikan sudah diunduh sebelum demo.
- Jika `/finish` butuh waktu lama, jelaskan bahwa transkripsi berjalan di CPU

### Jika LLM tidak dikonfigurasi (tidak ada `LLM_API_KEY`)
- RAG tetap berjalan (retrieval FAISS berhasil, chunk ditemukan)
- Pesan yang muncul: "Layanan AI belum dikonfigurasi"
- Jelaskan arsitektur dua jalur (in-app RAG vs Langflow MCP)

### Jika pertanyaan muncul tentang data yang terlihat di grafik
- Jawab jujur: "60 hari pertama adalah data simulasi dari seed script, ditandai provider 'simulasi-demo'. Sesi check-in nyata dari tadi juga ikut masuk grafik. Di produksi keduanya akan dipisahkan atau hanya data nyata yang ditampilkan."

### Jika pertanyaan tentang enkripsi audio
- Audio disimpan terenkripsi (`.webm.enc`) dengan Fernet AES-128
- Transkrip teks di database tidak dienkripsi (batasan yang diketahui, dicantumkan di SECURITY.md)
