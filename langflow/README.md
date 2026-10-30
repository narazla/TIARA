# Langflow - TIARA Dementia Guidance (IBM Bob MCP)

Folder ini berisi flow Langflow yang mengekspos kemampuan Dementia Guidance TIARA sebagai alat MCP untuk IBM Bob.

---

## Isi Folder

| Berkas | Keterangan |
|---|---|
| `answer_from_dementia_guideline.json` | Flow Langflow yang sudah diekspor, tanpa kunci API |

---

## Cara Mengimpor ke Langflow Desktop

1. Buka Langflow Desktop (`http://localhost:7860`).
2. Klik "New Flow" lalu pilih "Import".
3. Pilih berkas `answer_from_dementia_guideline.json` dari folder ini.
4. Flow bernama "TIARA" akan muncul di workspace.

---

## Variabel Global yang Diperlukan

Flow ini membutuhkan kunci Gemini API yang diatur sebagai variabel global Langflow:

1. Di Langflow, buka **Settings** (ikon roda gigi) - **Global Variables**.
2. Tambahkan variabel baru:
   - Nama: `GOOGLE_API_KEY`
   - Nilai: kunci Gemini API Anda (`AIza...`)
3. Simpan. Kunci ini dipakai oleh komponen Gemini di dalam flow.

Kunci API tidak tersimpan di dalam berkas JSON yang diekspor.

---

## Cara Kerja Flow Ini

Flow memasukkan **seluruh teks** kedua dokumen resmi Kemenkes langsung ke dalam prompt agen Gemini:

- Pedoman Nasional Pelayanan Klinis Tata Laksana Demensia (PNPK Demensia)
- Panduan Praktis Caregiver dalam Perawatan Jangka Panjang bagi Lanjut Usia

Agen tidak menggunakan pencarian vektor. Seluruh konteks dokumen dikirim ke Gemini dalam setiap permintaan.

**Konsekuensi:**
- Setiap pertanyaan mengonsumsi sekitar 250 ribu token input.
- Pada kuota gratis Gemini (250 ribu token input per menit), throughput sekitar satu pertanyaan per menit.
- Waktu respons sekitar 46 detik per pertanyaan.

**Perbedaan dengan jalur in-app RAG:**
- Jalur in-app menggunakan FAISS + multilingual-e5-large (pencarian vektor, TOP_K=6).
- Jalur Langflow ini memasukkan seluruh teks dokumen tanpa pencarian vektor.

**Rencana perbaikan:** beralih ke pencarian vektor (Chroma dengan embedding Google) untuk jalur ini. Belum diimplementasikan; jika folder ini diperbarui, dokumen ini harus diperbarui pula.

---

## Perbedaan Nomor Halaman

| Jalur | Dokumen PNPK | Panduan Caregiver |
|---|---|---|
| In-app RAG (FAISS) | label = indeks tersimpan + 1 (misal: indeks 86 -> hal 87) | nomor halaman PDF (misal: hal 24) |
| Langflow (jalur ini) | dikoreksi via instruksi agen | nomor cetak dalam buku (misal: hal 14) |

Nomor halaman berbeda antar jalur untuk Panduan Caregiver karena perbedaan penomoran PDF vs buku cetak.

---

## Guardrail Agen

Agen dikonfigurasi lewat instruksi prompt untuk:
- Menjawab hanya dari konteks dokumen yang dimuat.
- Mengakui dengan jujur jika pertanyaan di luar cakupan dokumen.
- Tidak memberikan diagnosis medis.
- Tidak menyebutkan dosis atau nama obat spesifik; mengarahkan ke tenaga kesehatan.

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

Nilai `timeout` diatur ke 300000 ms (5 menit) karena respons bisa memakan waktu hingga 46 detik.

---

## Catatan Kuota

Pada kuota gratis Gemini:
- Batas: 250 ribu token input per menit.
- Setiap pertanyaan mengonsumsi sekitar 250 ribu token (seluruh teks dokumen).
- Jeda minimal satu menit antar pertanyaan untuk menghindari error batas kuota.
- Untuk penggunaan yang lebih sering, pertimbangkan migrasi ke pencarian vektor (rencana ke depan).
