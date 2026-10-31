# Hasil evaluasi faithfulness RAG

- Pertanyaan yang dijawab dari dokumen (n=7):
  - Didukung penuh (D): 85.7% (6/7)
  - Didukung penuh atau sebagian (D+S): 100.0% (7/7)
  - Tidak didukung (T): 0.0% (0/7)
- Uji guardrail (n=3): menolak dengan benar 100.0% (3/3)

## Batas evaluasi ini

- Sampel kecil (10 pertanyaan: 7 dijawab dari dokumen, 3 guardrail); angka bersifat indikatif.
- Pertanyaan dipilih acak dengan benih tetap dari set uji; tiga pertanyaan guardrail ditulis tim.
- Penilai adalah anggota tim, bukan tenaga kesehatan. Penilaian hanya mengukur kesesuaian jawaban dengan potongan dokumen yang diambil, bukan kebenaran klinisnya.
- Lembar penilaian lengkap: `faithfulness_penilaian.csv` dan `faithfulness_lembar.md`.
