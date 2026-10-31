
<div align="center">

### TIARA

*Early detection, from home*

</div>

<br>
<div align="center">
  <img
    src="https://drive.google.com/uc?export=view&id=17Cajv7tbxUqnyNX4kfuXru_om32-4GcB"
    alt="Pemantauan Kognitif Harian untuk Lansia dan Caregiver"
    style="width:100%; max-width:1400px;"
  />
</div>
<br>

>
> **Pernyataan medis:** TIARA bukan alat diagnosis medis. Platform ini hanya menyediakan pemantauan tren kognitif dan dukungan caregiver yang bersifat informatif, dan tidak menggantikan penilaian klinis profesional. Selalu konsultasikan dengan tenaga kesehatan yang berkualifikasi untuk nasihat medis.

---

## Ringkasan

TIARA (Thinking, Interaction, And Recall Assistant) adalah platform perawatan kognitif berbasis AI yang membantu keluarga memantau perubahan pola bicara lansia, yang dapat berkaitan dengan perubahan kognitif, melalui sesi check-in harian berbasis suara. Lansia menjawab empat pertanyaan dengan suara; audio direkam per pertanyaan, ditranskripsi dengan faster-whisper, lalu dianalisis fitur pola bicaranya. Platform ini menyediakan dashboard terlindungi PIN untuk caregiver berisi tren Skor Risiko Kognitif, peringatan otomatis, dan rekomendasi berbasis aturan. TIARA juga dilengkapi Dementia Guidance AI yang menjawab pertanyaan caregiver berdasarkan PNPK Tata Laksana Demensia dan Panduan Caregiver Kemenkes, serta terintegrasi dengan IBM Bob melalui Langflow MCP. Skor yang dihasilkan adalah indikator informatif dari pola bicara, bukan diagnosis medis.

---

## Gambaran Umum

TIARA menjawab kesenjangan dalam perawatan kognitif dini bagi lansia dan keluarga mereka. Caregiver informal sering kali kekurangan panduan berbasis bukti yang tepat waktu; tim klinik kekurangan data longitudinal di antara jadwal kunjungan; dan lansia sendiri membutuhkan interaksi harian yang hangat dan tidak terkesan seperti tes medis.

TIARA menyatukan tiga pengalaman dalam satu platform:

- **Lansia** menyelesaikan check-in suara harian yang sederhana melalui mikrofon perangkat mereka, dipandu oleh pertanyaan AI yang diucapkan.
- **Caregiver** mengakses dashboard terlindungi PIN yang merangkum tren risiko kognitif, peringatan otomatis, rekomendasi berbasis aturan, dan chat panduan demensia.
- **Tenaga kesehatan** memantau pasien, meninjau data sesi longitudinal, dan mengakses laporan bulanan.

---

## Alur Pengguna Utama

```text
Lansia:
  Login -> Beranda -> Check-in harian (suara per pertanyaan, persetujuan diperlukan)
        -> Halaman hasil (hangat, tanpa data klinis yang ditampilkan)

Caregiver:
  Login -> PIN Caregiver -> Dashboard -> Peringatan -> Rekomendasi
        -> Dementia Guidance AI -> Laporan

Tenaga kesehatan:
  Login -> Pemantauan pasien -> Riwayat sesi -> Tren longitudinal -> Laporan bulanan
```

---

## Fitur

- **Check-in suara harian** - Pertanyaan berbasis AI yang diucapkan (4 pertanyaan per sesi) dengan rekaman mikrofon berbasis persetujuan. Video hanya digunakan sebagai pratinjau lokal; tidak direkam dan tidak dianalisis.
- **Pipeline analisis suara AI** - Transkripsi dengan faster-whisper (model `base`, bahasa Indonesia, CPU int8, word timestamps, dan VAD). Fitur suara yang diekstrak: kata per menit, jeda antar kata >= 0,5 detik, kata ragu, pengulangan kata berurutan, dan jeda respons (waktu hingga kata pertama). Skor 0-10, penyimpangan berbobot dari baseline pribadi. Komponen bahasa, wajah, dan memori bernilai null pada sesi nyata (hanya ada di data simulasi).
- **Dashboard caregiver** - Grafik tren Skor Risiko Kognitif (30 hari), ringkasan pasien, feed peringatan otomatis, rekomendasi berbasis aturan per kategori (bukan AI dan bukan saran medis), dan laporan bulanan. Data dashboard untuk akun demo menyertakan riwayat simulasi; sesi check-in nyata muncul dalam grafik yang sama.
- **Generator laporan bulanan** - Caregiver dapat membuat laporan bulanan secara manual melalui tombol "Buat Laporan Bulan Ini" di tab Laporan. Laporan dihitung dari data sesi dan skor risiko nyata pasien pada bulan yang dipilih. Skor hanya berasal dari komponen suara. Laporan bersifat upsert: jika sudah ada untuk bulan tersebut, laporan diperbarui. Laporan adalah indikator informatif dan bukan diagnosis. Ringkasan laporan dibuat dari templat, bukan model bahasa. Laporan dapat dicetak atau disimpan sebagai PDF melalui dialog cetak browser. Tidak ada penjadwalan otomatis.
- **Dementia Guidance AI (dalam aplikasi)** - Menjawab pertanyaan caregiver dengan mengambil bagian yang relevan dari dua dokumen resmi kesehatan Indonesia (PNPK Tata Laksana Demensia, Panduan Caregiver Kemenkes) menggunakan FAISS vector index dan embedding multilingual-e5-large, lalu menyusun jawaban dengan Gemini. Merespons dalam bahasa pertanyaan.
- **Akses berbasis peran** - Alur dan rute terproteksi terpisah untuk lansia, caregiver, dan tenaga kesehatan (3 peran).
- **Perlindungan PIN caregiver** - Langkah akses sekunder yang diperlukan untuk masuk ke dashboard caregiver. Endpoint dashboard memerlukan header `X-Dashboard-Token`; tanpa header ini API mengembalikan 403 `PIN_DIPERLUKAN`.

---

## Peringatan Otomatis

Peringatan dibuat di akhir setiap panggilan `/elderly/checkin/{session_id}/finish`:

| Kondisi | Tingkat | Judul |
|---|---|---|
| Skor Risiko Kognitif Tinggi (>= 7) | WARNING | "Pola bicara hari ini menyimpang dari biasanya" |
| Kurang dari 5 kata terdeteksi (sesi gagal) | INFO | "Check-in hari ini tidak terekam" |

- Judul peringatan yang sama tidak dibuat ulang dalam 12 jam.
- Respons `/finish` menyertakan `perlu_perhatian: true` ketika peringatan WARNING dibuat. Halaman hasil lansia menampilkan kotak catatan lembut hanya ketika flag ini aktif.
- Peringatan muncul di dashboard caregiver saat caregiver membukanya. Tidak ada push notification, pesan WhatsApp, atau notifikasi email.

---

## Rekomendasi Berbasis Aturan

Setiap check-in yang selesai menghasilkan satu set rekomendasi untuk caregiver. Rekomendasi ini **tidak dibuat oleh AI**. Sistem memilih teks templat tetap berdasarkan tingkat Skor Risiko Kognitif (Rendah, Sedang, Tinggi) dan tren 7 hari terakhir (tren dianggap naik jika skor hari ini minimal 1,0 di atas rata-rata 7 hari).

- Lima kategori: rutinitas, aktivitas kognitif, sosial, catatan medis, dan kesejahteraan.
- Hanya set terbaru per pasien yang ditampilkan. Rekomendasi bawaan data demo tidak diubah.
- Dashboard menampilkan catatan bahwa rekomendasi ini berbasis aturan, bukan saran medis, dan bukan pengganti tenaga kesehatan.
- Teks templat belum ditinjau tenaga kesehatan.

---

## Data Demo dan Mode Simulasi

Ketika `DEMO_MODE=True` (default), skrip seed membuat 60 hari riwayat check-in simulasi untuk akun lansia demo dan empat pasien simulasi tambahan untuk tampilan tenaga kesehatan. Sesi simulasi ditandai dengan provider `"simulasi-demo"` di database.

Sesi check-in nyata dari rekaman suara muncul dalam grafik tren yang sama dengan data simulasi untuk pasien demo utama (Nenek Ladya). Dashboard saat ini tidak memisahkan keduanya secara visual.

Jurnal suasana hati tersimpan di database tetapi belum ditampilkan di dashboard caregiver maupun tenaga kesehatan.

---

## Akun Demo

Kredensial berikut hanya untuk penggunaan demo lokal. Jangan gunakan di server publik.

| Peran | Email | Kata Sandi | PIN |
|---|---|---|---|
| Lansia | `elderly@tiara.app` | `Lansia_123` | - |
| Caregiver | `caregiver@tiara.app` | `Caregiver_123` | `123456` |
| Tenaga Kesehatan | `doctor@tiara.app` | `Dokter_123` | - |

Pasien simulasi tambahan yang terhubung ke akun dokter: `pasien.hendra@tiara.app`, `pasien.siti@tiara.app`, `pasien.wayan@tiara.app`, `pasien.rahayu@tiara.app` (kata sandi berupa UUID acak yang ditetapkan oleh skrip seed; akun-akun ini tidak dimaksudkan untuk login langsung).

---

## Integrasi IBM Bob + Langflow

Kemampuan Dementia Guidance TIARA juga diekspos sebagai alat MCP (Model Context Protocol) melalui Langflow, sehingga dapat dipanggil langsung dari IBM Bob. Ini adalah jalur terpisah dari pipeline RAG dalam aplikasi.

### Cara kerja jalur Langflow

1. **Agen Langflow** - Proyek bernama `TIARA` dikonfigurasi di Langflow Desktop dengan satu flow bernama `answer_from_dementia_guideline`. Agen dimuat dengan teks lengkap kedua dokumen sebagai konteks prompt - tidak menggunakan pencarian vektor. Hal ini membuat respons lebih lambat (sekitar 46 detik) dan terbatas oleh batas token input tier gratis Gemini (sekitar satu pertanyaan per menit pada 250 ribu token/menit).
2. **Server MCP** - Langflow mengekspos proyek sebagai server MCP di:
   ```
   http://localhost:7860/api/v1/mcp/project/<project-id>/streamable
   ```
3. **Bob sebagai klien MCP** - IBM Bob terhubung ke server MCP ini melalui `mcp-proxy` (dikonfigurasi di `~/.bob/settings/mcp.json`). Alat `answer_from_dementia_guideline` kemudian muncul di daftar alat Bob.

Folder Langflow (`langflow/`) berisi flow yang diekspor tanpa kunci API. Kunci API dibaca dari variabel global Langflow bernama `GOOGLE_API_KEY`.

**Perbedaan nomor halaman antar jalur:** Pada RAG dalam aplikasi (jalur FAISS), label halaman PNPK yang ditampilkan ke pengguna adalah `stored_index + 1`; label Panduan Caregiver dipakai apa adanya. Pada jalur Langflow, referensi halaman PNPK dikoreksi melalui instruksi agen, dan referensi Panduan Caregiver menggunakan nomor halaman cetak dalam buku (misalnya hal. 14), yang berbeda dari nomor halaman PDF (misalnya hal. 24) yang digunakan di jalur FAISS.

**Rencana perbaikan:** Peralihan jalur Langflow ke pencarian vektor (Chroma dengan embedding Google) sedang direncanakan. Belum diimplementasikan di folder `langflow/`.

### Guardrail (dikonfigurasi melalui instruksi agen dan prompt)

- Agen hanya menjawab dari konteks dokumen yang dimuat dan mengakui ketika pertanyaan berada di luar cakupannya.
- Tidak memberikan diagnosis medis atau dosis obat spesifik.
- Mengarahkan caregiver ke tenaga kesehatan ketika pertanyaan memerlukan penilaian klinis.

### Konfigurasi Bob MCP (`~/.bob/settings/mcp.json`)

```json
{
  "mcpServers": {
    "lf-tiara": {
      "command": "uvx",
      "args": [
        "mcp-proxy",
        "--transport",
        "streamablehttp",
        "http://localhost:7860/api/v1/mcp/project/<your-project-id>/streamable"
      ],
      "timeout": 300000
    }
  }
}
```

> Ganti `<your-project-id>` dengan UUID yang ditampilkan di Langflow pada tab MCP Server proyek Anda.

---

## Evaluasi RAG

Pipeline RAG dalam aplikasi (FAISS + multilingual-e5-large, TOP_K=6) dievaluasi pada akurasi retrieval. Evaluasi mengukur apakah halaman sumber yang benar muncul di chunk yang diambil - **tidak** mengukur kebenaran jawaban akhir yang dihasilkan.

### Hasil retrieval - pertanyaan berbahasa dokumen (34 pertanyaan)

| Metrik | Semua (n=34) | PNPK (n=19) | Panduan Caregiver (n=15) |
|---|---|---|---|
| Dokumen benar terambil | 100% | 100% | 100% |
| Halaman persis sama (label yang ditampilkan) | 79,4% (27/34) | 84,2% (16/19) | 73,3% (11/15) |
| Dalam rentang 1 halaman dari label (top-k) | 100% (34/34) | 100% (19/19) | 100% (15/15) |
| Top-1 dalam rentang 1 halaman | 79,4% (27/34) | 89,5% (17/19) | 66,7% (10/15) |

### Hasil retrieval - pertanyaan berbahasa awam (10 pertanyaan)

| Metrik | Semua (n=10) |
|---|---|
| Dokumen benar terambil | 100% (10/10) |
| Halaman persis sama (label yang ditampilkan) | 90% (9/10) |
| Dalam rentang 1 halaman dari label (top-k) | 90% (9/10) |
| Top-1 dalam rentang 1 halaman | 50% (5/10) |

Catatan: sampel pertanyaan berbahasa awam kecil (10 pertanyaan); satu pertanyaan meleset 10 halaman. Angka-angka ini bersifat indikatif.

Selisih 1 halaman pada Panduan Caregiver terjadi karena chunk yang memotong batas halaman pada PDF asli. ### Faithfulness jawaban (10 pertanyaan)

Setiap jawaban dinilai terhadap potongan dokumen yang diambil sistem untuk jawaban itu.

| Ukuran | Hasil |
|---|---|
| Pertanyaan dijawab dari dokumen: didukung penuh | 85,7% (6/7) |
| Didukung penuh atau sebagian | 100% (7/7) |
| Tidak didukung | 0% (0/7) |
| Guardrail (dosis obat, diagnosis pasti, di luar topik): menolak dengan benar | 100% (3/3) |

Satu jawaban (makanan saat nafsu makan turun) dinilai sebagian: saran diet pencegahan demensia dari dokumen dipakai untuk pertanyaan yang berbeda.

Batas evaluasi: sampel kecil (10 pertanyaan). Penilai adalah anggota tim, dibantu pemeriksaan awal dengan AI, bukan tenaga kesehatan. Penilaian hanya mengukur kesesuaian jawaban dengan potongan dokumen, bukan kebenaran klinisnya. Lembar lengkap: `docs/evaluasi-rag/faithfulness_lembar.md`, `faithfulness_penilaian.csv`, `faithfulness_hasil.md`.

Berkas evaluasi lengkap: [`docs/evaluasi-rag/`](docs/evaluasi-rag/)

Penelitian ukuran chunk (repositori terpisah): hit rate 128-token 91,2%, 256-token 97,1%, 512-token 91,2% - [narazla/TIARA-rag-chunking](https://github.com/narazla/TIARA-rag-chunking)

---

## Responsible AI

| Prinsip | Yang benar-benar diimplementasikan |
|---|---|
| Persetujuan pengguna | Akses kamera dan mikrofon memerlukan persetujuan eksplisit per sesi (`consent_given` disimpan di DB) |
| Privasi caregiver | Dashboard memerlukan PIN terpisah; JWT access token kedaluwarsa setelah 60 menit |
| Pemisahan peran | `require_role` diterapkan di backend untuk lansia, caregiver, dan tenaga kesehatan |
| Disclaimer medis | Ditampilkan di setiap halaman hasil dan panduan; di-hardcode di field summary API |
| Panduan berbasis bukti | RAG hanya mengambil dari dua dokumen resmi kesehatan Indonesia |
| Pengawasan manusia | Semua skor AI adalah indikator; keputusan klinis tetap berada di tangan tenaga kesehatan |
| Guardrail panduan | Guidance AI dikonfigurasi via prompt untuk mengakui ketika pertanyaan tidak ada dalam dokumen |
| Enkripsi audio saat disimpan | Rekaman disimpan sebagai `.webm.enc` (Fernet); didekripsi hanya di memori |
| Privasi transkrip | Teks transkrip di tabel `transcripts` TIDAK dienkripsi |
| Rekomendasi | Berbasis aturan, bukan AI. Dashboard memuat catatan bahwa ini bukan saran medis |

---

## Tech Stack

| Lapisan | Teknologi |
|---|---|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS v4, Framer Motion, Recharts, Radix UI |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2 (async), PostgreSQL 15, Alembic |
| Autentikasi | JWT (python-jose), bcrypt, perlindungan PIN caregiver |
| AI - analisis suara | faster-whisper (transkripsi + ekstraksi fitur suara) |
| AI - RAG panduan | FAISS, sentence-transformers (multilingual-e5-large), Google Gemini |
| AI - integrasi Bob | Langflow MCP server, mcp-proxy, IBM Bob |
| Keamanan media | cryptography (Fernet) untuk enkripsi berkas audio saat disimpan |

---

## Struktur Repositori

```text
TIARA-IBM/
├── frontend/                  # Aplikasi Next.js
│   ├── app/                   # Halaman App Router
│   │   ├── elderly/           # Alur check-in, companion, dan beranda
│   │   ├── caregiver/         # Halaman PIN dan dashboard caregiver
│   │   ├── login/             # Halaman autentikasi
│   │   └── register/
│   ├── components/shared/     # Footer, ProtectedRoute
│   └── lib/                   # API client, auth context, types
├── backend/                   # Aplikasi FastAPI
│   ├── app/
│   │   ├── routes/            # Handler rute auth, elderly, caregiver, healthcare, checkin
│   │   ├── models/            # Model ORM SQLAlchemy
│   │   ├── services/          # RAG guidance, analisis suara, media crypto
│   │   │   └── rag_data/      # FAISS index dan chunk dokumen yang sudah dibuat
│   │   ├── schemas/           # Skema request/response Pydantic
│   │   ├── core/              # Config, security, dependencies
│   │   └── scripts/           # seed.py, evaluasi_rag.py
│   └── alembic/               # Migrasi database
├── docs/                      # Dokumen produk, arsitektur, API, AI, dan keamanan
│   └── evaluasi-rag/          # Set pertanyaan dan hasil evaluasi RAG
├── langflow/                  # Flow Langflow yang diekspor (alat MCP untuk IBM Bob)
├── assets/                    # Berkas logo master
├── docker-compose.yml         # Layanan PostgreSQL + backend
├── .env.example               # Template variabel lingkungan
└── README.md
```

---

## Pengaturan Lokal

### Prasyarat

- Node.js 18 atau lebih baru
- Python 3.11 atau lebih baru
- PostgreSQL 15 atau lebih baru (atau gunakan Docker Compose)

### Backend

```bash
cd backend

python -m venv venv

# Windows PowerShell
venv\Scripts\Activate.ps1
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API berjalan di `http://localhost:8000`. Dokumentasi interaktif tersedia di `http://localhost:8000/docs`.

Untuk membangun ulang riwayat simulasi (misalnya setelah perubahan skema):

```bash
python -m app.scripts.seed --reset-demo
```

### Variabel lingkungan (backend)

Salin `.env.example` ke `backend/.env` dan isi:

```text
DATABASE_URL=postgresql+asyncpg://tiara:tiara_password@localhost:5432/tiara_db
JWT_SECRET_KEY=<a-long-random-secret>      # disarankan minimal 32 karakter
LLM_API_KEY=<your-gemini-api-key>        # required for AI-generated guidance answers
LLM_PROVIDER=gemini
MEDIA_ENCRYPTION_KEY=<fernet-key>        # required; generate with command below
FRONTEND_URL=http://localhost:3000
DEMO_MODE=True
```

Buat kunci Fernet untuk `MEDIA_ENCRYPTION_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Peringatan:** jika `MEDIA_ENCRYPTION_KEY` hilang, semua rekaman terenkripsi (berkas `.webm.enc`) menjadi permanen tidak bisa dibaca. Simpan kunci secara aman dan buat salinan cadangan.

Model faster-whisper (`base`, ~145 MB) diunduh otomatis saat pertama digunakan. Tidak diperlukan langkah unduhan manual.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend berjalan di `http://localhost:3000`. Atur `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` di `frontend/.env.local` jika backend tidak menggunakan port default.

### Docker Compose (backend dan database)

```bash
# Windows PowerShell
$env:JWT_SECRET_KEY="<your-secret>"; $env:MEDIA_ENCRYPTION_KEY="<fernet-key>"; docker compose up --build

# macOS / Linux
JWT_SECRET_KEY=<your-secret> MEDIA_ENCRYPTION_KEY=<fernet-key> docker compose up --build
```

Compose menjalankan PostgreSQL dan backend. Frontend dijalankan terpisah dengan `npm run dev` di folder `frontend` (lihat bagian Frontend).
---

## Deployment

Demo berjalan secara lokal. Panduan deployment akan ditambahkan setelah backend dihosting.

---

## Rencana Pengembangan

- **IBM watsonx.ai:** model bahasa saat ini adalah Google Gemini. Integrasi watsonx.ai direncanakan sebagai pengembangan berikutnya dan belum diimplementasikan.
- **Pencarian vektor untuk jalur Langflow:** peralihan ke Chroma dengan embedding Google (lihat bagian Integrasi IBM Bob + Langflow).
- **Peninjauan tenaga kesehatan** untuk teks rekomendasi dan validasi klinis skor suara.
- **Evaluasi lebih besar** untuk faithfulness dan uji pengguna dengan caregiver.

---

## Pipeline AI (Analisis Check-in)

Setelah sesi check-in diselesaikan melalui `POST /elderly/checkin/{session_id}/finish`, TIARA memproses semua audio yang direkam melalui langkah-langkah berikut:

1. **Dekripsi** - Berkas `.webm.enc` didekripsi di memori menggunakan Fernet.
2. **Transkripsi** - Audio setiap jawaban ditranskripsi dengan faster-whisper (model `base`, bahasa Indonesia, CPU int8, word timestamps, VAD filter).
3. **Ekstraksi fitur suara** - per jawaban: kata per menit (dari word timestamps), jeda antar kata >= 0,5 detik, kata ragu (`eh`, `ehm`, `hmm`, `anu`, `apa ya`, dll.), pengulangan kata berurutan, dan jeda respons (timestamp kata pertama). Fitur digabungkan dari semua jawaban.
4. **Pemilihan baseline** - jika pasien memiliki >= 3 sesi nyata sebelumnya, median dari 14 sesi terakhir digunakan sebagai baseline pribadi. Jika tidak, nilai acuan umum digunakan (100 wpm, jeda 0,8 detik, 2,0 keraguan/menit, jeda respons 2,0 detik).
5. **Penilaian risiko** - skor = clamp(1,5 + 7,5 * weighted_deviation, 0, 10). Bobot: laju bicara 0,3, jeda 0,3, jeda respons 0,3, keraguan 0,1. Tingkat: Rendah (< 4), Sedang (4-6,9), Tinggi (>= 7).
6. **Peringatan** - peringatan WARNING dibuat jika skor Tinggi; peringatan INFO dibuat jika kurang dari 5 kata terdeteksi.

**Yang tidak ada di pipeline nyata:** tidak ada analisis audio librosa, tidak ada analisis wajah OpenCV, dan tidak ada analisis bahasa (orientasi, memori, koherensi) pada sesi nyata. Field `language_component`, `facial_component`, dan `memory_component` di `risk_scores` bernilai null untuk semua sesi check-in nyata. Field-field ini hanya terisi pada data simulasi demo.

Semua hasil hanya merupakan indikator informatif, bukan diagnosis.

---

## Perintah Seed

```bash
# Dari direktori backend/:

# Seed biasa (idempoten - aman dijalankan berkali-kali)
python -m app.scripts.seed

# Reset dan bangun ulang semua riwayat simulasi
python -m app.scripts.seed --reset-demo
```

---

## Perintah Evaluasi RAG

```bash
# Dari direktori backend/:
python -m app.scripts.evaluasi_rag ..\docs\evaluasi-rag\pertanyaan_uji_dokumen.csv
python -m app.scripts.evaluasi_rag ..\docs\evaluasi-rag\pertanyaan_uji_awam.csv
```

Hasil disimpan ke `evaluasi_rag_hasil.csv` di direktori saat ini.

---

## Dokumentasi

Dokumentasi proyek tambahan ada di [`docs/`](docs/):

- [Persyaratan produk](docs/01-product-requirements.md)
- [Cakupan MVP](docs/02-mvp-scope.md)
- [Arsitektur sistem](docs/03-system-architecture.md)
- [Desain database](docs/04-database-design.md)
- [Spesifikasi API](docs/05-api-specification.md)
- [Pipeline AI](docs/06-ai-pipeline.md)
- [Keamanan dan privasi](docs/07-security-and-privacy.md)
- [Peta jalan pengembangan](docs/08-development-roadmap.md)
- [Skrip demo](docs/09-demo-script.md)
- [Berkas evaluasi RAG](docs/evaluasi-rag/)

---

## Keterbatasan yang Diketahui

- Data dashboard untuk pasien demo (Nenek Ladya) merupakan campuran 60 hari riwayat simulasi dan sesi nyata dari check-in suara. Tidak ada pemisahan visual antara data simulasi dan nyata dalam grafik.
- Skor suara adalah indikator informatif berdasarkan penyimpangan pola bicara. Belum divalidasi secara klinis dan bukan pengganti penilaian profesional.
- faster-whisper sering menghapus kata ragu (`eh`, `hmm`, dll.) selama transkripsi, sehingga hitungan keraguan cenderung rendah.
- Teks transkrip di tabel `transcripts` disimpan tanpa enkripsi di database.
- Jurnal suasana hati tersimpan di database tetapi belum ditampilkan ke caregiver atau tenaga kesehatan.
- Kartu ringkasan di dashboard caregiver (Memory Consistency, Response Delay, Speech Hesitation) mungkin menampilkan nilai statis atau simulasi untuk sesi tanpa analisis nyata lengkap. Verifikasi secara visual saat demo.
- Kualitas analisis AI bergantung pada kualitas mikrofon dan kebisingan lingkungan.
- Respons Dementia Guidance AI hanya seakurat dokumen yang dimuat.
- Evaluasi retrieval hanya mengukur apakah halaman sumber ditemukan. Faithfulness hanya dievaluasi pada 10 pertanyaan, dinilai anggota tim (bukan tenaga kesehatan), dan hanya mengukur kesesuaian dengan potongan dokumen.
- Sampel evaluasi RAG berbahasa awam kecil (10 pertanyaan); hasilnya bersifat indikatif.
- TIARA tidak boleh digunakan sebagai pengganti evaluasi medis profesional.

---

## Meet the Team

<table>
<tr>
<td align="center" width="50%">
<img src="https://drive.google.com/uc?export=view&id=17JzgCaF45gCTXnlIglXVKpq05sTQq5Vx" width="144" height="180"/>
<br/>
<a href="https://github.com/Arieslana01">
<b>Muhammad Aris Maulana</b>
</a>
<br/>
<i>Universitas Diponegoro</i>
</td>
<td align="center" width="50%">
<img src="https://drive.google.com/uc?export=view&id=1rPzNkUuXtFebZFcrLa7c-ZtZlSnxa0jX" width="144" height="180"/>
<br/>
<a href="https://github.com/narazla">
<b>Nazla Azzahra Hermana</b>
</a>
<br/>
<i>Universitas Diponegoro</i>
</td>
</tr>
</table>

---

Dibuat untuk **IBM SkillsBuild University Education National Hackathon 2026**  
**Hacktiv8 x IBM x Komdigi**
