# Langflow - TIARA Dementia Guidance (IBM Bob MCP)

Folder ini berisi flow Langflow yang mengekspos kemampuan Dementia Guidance TIARA sebagai alat MCP untuk IBM Bob.

---

## Isi Folder

| Berkas | Keterangan |
|---|---|
| `answer_from_dementia_guideline.json` | Flow Langflow yang sudah diekspor, tanpa kunci API |
| `dokumen_chunks_256_bagian1.txt` – `bagian4.txt` | Chunk dokumen (output skrip ekspor) untuk diingest ke Chroma via node File di Langflow |

---

## Cara Mengimpor ke Langflow Desktop

1. Buka Langflow Desktop (`http://localhost:7860`).
2. Klik "New Flow" lalu pilih "Import".
3. Pilih berkas `answer_from_dementia_guideline.json` dari folder ini.
4. Flow bernama "TIARA" akan muncul di workspace.

---

## Variabel Global yang Diperlukan

Flow ini membutuhkan kunci Gemini API yang diatur sebagai variabel global Langflow:

1. Di Langflow, buka **Settings** (ikon roda gigi) → **Global Variables**.
2. Tambahkan variabel baru:
   - Nama: `GOOGLE_API_KEY`
   - Nilai: kunci Gemini API Anda (`AIza...`)
3. Simpan. Kunci ini dipakai oleh komponen embedding (`models/gemini-embedding-001`) dan komponen agen (`gemini-flash-lite-latest`) di dalam flow.

Kunci API tidak tersimpan di dalam berkas JSON yang diekspor.

---

## Cara Kerja Flow Ini

Flow menggunakan pencarian vektor (Chroma) — bukan teks dokumen penuh di prompt. Dokumen dipecah menjadi chunk 256 token menggunakan skrip `export_chunks_langflow.py`, lalu diindeks di Chroma dengan embedding Google (`models/gemini-embedding-001`). Agen (`gemini-flash-lite-latest`) menjawab hanya dari potongan yang diambil, disertai sitasi dokumen dan halaman.

**Dua pemakaian flow ini:**

1. **Backend TIARA (jalur utama in-app):** backend memanggil Langflow lebih dulu bila `LANGFLOW_URL` dan `LANGFLOW_FLOW_ID` diisi. Bila Langflow tidak tersedia atau gagal, backend otomatis beralih ke jalur cadangan FAISS (multilingual-e5-large).
2. **Alat MCP IBM Bob:** IBM Bob memanggil flow ini melalui server MCP Langflow via `mcp-proxy`.

**Waktu respons (sampel kecil — tiga pertanyaan uji):**
- Sekitar 2–4 detik di Playground Langflow.
- Sekitar 7–12 detik lewat IBM Bob.
- Versi sebelumnya yang memasukkan seluruh dokumen ke prompt memakan sekitar 46 detik per pertanyaan.

**Catatan evaluasi:** angka evaluasi retrieval dan faithfulness di README utama berlaku untuk jalur FAISS (jalur cadangan). Jalur Langflow ini belum dievaluasi dengan cara yang sama.

---

## Membangun Ulang Indeks Chroma

Indeks Chroma **tidak tersimpan di berkas JSON** dan harus dibangun di mesin lokal sebelum flow dapat menjawab pertanyaan.

**Langkah 1 — ekspor chunk:**

Jalankan dari direktori `backend/`:

```bash
python -m app.scripts.export_chunks_langflow
```

Perintah ini membaca `backend/app/services/rag_data/chunks_256token.pkl` dan menulis empat berkas teks ke folder `langflow/`:
- `dokumen_chunks_256_bagian1.txt`
- `dokumen_chunks_256_bagian2.txt`
- `dokumen_chunks_256_bagian3.txt`
- `dokumen_chunks_256_bagian4.txt`

Setiap berkas berisi chunk dengan separator `<<<CHUNK>>>` dan label `[Dokumen, Halaman N]` per chunk.

**Langkah 2 — ingest ke Chroma via Langflow:**

Di dalam flow terdapat node `File` dan `SplitText` yang terhubung ke node Chroma. Muat keempat berkas `.txt` ke node File di Langflow dan jalankan flow dalam mode ingest untuk membangun koleksi `tiara_guideline_v4` di direktori penyimpanan Chroma. Berkas JSON asli menunjuk ke folder lokal pengembang, jadi ubah path di node Chroma ke folder di komputer Anda sebelum menjalankan ingest.

---

## Perbedaan Nomor Halaman

Instruksi di prompt agen mengatur koreksi nomor halaman:

| Jalur | Dokumen PNPK | Panduan Caregiver |
|---|---|---|
| In-app RAG (FAISS) | label = indeks tersimpan + 1 (misal: indeks 86 → hal 87) | nomor halaman PDF (misal: hal 24) |
| Langflow (jalur ini) | agen menambahkan 1 pada nomor konteks (sesuai instruksi prompt) | nomor apa adanya dari konteks chunk |

Sitasi halaman ditulis agen di dalam jawaban (format: Dokumen, hal N), sehingga penomorannya dapat berbeda dari jalur FAISS.

---

## Guardrail Agen

Agen dikonfigurasi lewat instruksi prompt untuk:
- Menjawab hanya dari konteks dokumen yang dimuat.
- Mengakui dengan jujur jika pertanyaan di luar cakupan dokumen.
- Tidak memberikan diagnosis medis.
- Tidak menyebutkan dosis atau nama obat spesifik; mengarahkan ke tenaga kesehatan.
- Merespons tanda bahaya (kejang, pingsan, cedera) dengan arahan ke layanan darurat.
- Mengakhiri setiap jawaban dengan pengingat bahwa informasi ini bukan pengganti pemeriksaan dokter.

Ini adalah konfigurasi via prompt, bukan jaminan teknis yang tidak bisa dilewati.

---

## Nama Alat MCP

Nama alat yang benar: **`answer_from_dementia_guideline`** (tanpa "s" di akhir "guideline").

---

## Konfigurasi IBM Bob

Tambahkan ke `~/.bob/settings/mcp.json`:

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

Ganti `<your-project-id>` dengan UUID yang terlihat di tab "MCP Server" di proyek Langflow Anda.

Respons lewat Bob sekitar 7–12 detik; timeout 300000 ms (5 menit) dipertahankan sebagai batas aman.

---

## Catatan Kuota

Setiap pertanyaan hanya mengirim potongan relevan ke agen, bukan seluruh dokumen, sehingga konsumsi token per pertanyaan jauh lebih kecil daripada versi sebelumnya. Batas kuota kunci Gemini Anda tetap berlaku.
