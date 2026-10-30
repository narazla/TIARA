"""
Evaluasi retrieval RAG TIARA terhadap daftar pertanyaan uji.

Memakai index dan chunk yang sama dengan layanan Guidance (TOP_K yang sama, tanpa LLM).
Untuk tiap pertanyaan dicek apakah halaman acuan muncul di chunk yang terambil dari
dokumen yang benar. Skrip juga menghitung selisih (halaman acuan - 'halaman' di chunk)
untuk mengetahui apakah 'halaman' berupa indeks mulai 0.

Cara pakai (dari folder backend):
    python -m app.scripts.evaluasi_rag "C:\\path\\pertanyaan_uji_final.csv"
Hasil per pertanyaan disimpan ke evaluasi_rag_hasil.csv di folder tempat skrip dijalankan.

Kolom CSV: no, pertanyaan, halaman_sumber, dokumen_sumber (kolom lain diabaikan).
"""
import csv
import sys
from collections import Counter, defaultdict

import numpy as np

from app.services import rag_guidance_service as svc


def muat_pertanyaan(jalur: str) -> list:
    with open(jalur, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if (r.get("pertanyaan") or "").strip()]


def ambil_chunk(pertanyaan: str, k: int) -> list:
    kueri = "query: " + svc._perluas_pertanyaan(pertanyaan)
    vektor = svc._model.encode([kueri], normalize_embeddings=True)
    _, indeks = svc._index.search(np.array(vektor, dtype=np.float32), k=k)
    return [svc._chunks[i] for i in indeks[0]]


def nilai_satu(baris: dict, chunk_terambil: list) -> dict:
    acuan = int(baris["halaman_sumber"])
    dokumen = baris["dokumen_sumber"].strip()
    benar = [c for c in chunk_terambil if c["dokumen"] == dokumen]
    g = 1 if dokumen.startswith("PNPK") else 0  # offset halaman per dokumen
    halaman = [int(c["halaman"]) for c in benar]

    def kena(fungsi, daftar):
        return any(fungsi(h) for h in daftar)

    pertama = [int(chunk_terambil[0]["halaman"])] if chunk_terambil and chunk_terambil[0]["dokumen"] == dokumen else []
    selisih = None
    if halaman:
        selisih = acuan - min(halaman, key=lambda h: abs(acuan - h))
    return {
        "no": baris.get("no", ""),
        "dokumen": dokumen,
        "acuan": acuan,
        "halaman_terambil": sorted(set(halaman)),
        "selisih_terdekat": selisih,
        "persis_label_lama": kena(lambda h: h == acuan, halaman),
        "persis_label_plus1": kena(lambda h: h + g == acuan, halaman),
        "dalam_rentang_h1_h2": kena(lambda h: acuan in (h + g, h + g + 1), halaman),
        "toleransi_1_dari_plus1": kena(lambda h: abs(acuan - (h + g)) <= 1, halaman),
        "top1_plus1_toleransi_1": kena(lambda h: abs(acuan - (h + g)) <= 1, pertama),
        "dokumen_benar_terambil": bool(benar),
    }


def persen(n: int, total: int) -> str:
    return f"{100.0 * n / total:.1f}% ({n}/{total})" if total else "-"


def ringkas(hasil: list, judul: str) -> None:
    n = len(hasil)
    print(f"\n== {judul} (n={n}) ==")
    print("Dokumen benar ikut terambil        :", persen(sum(h["dokumen_benar_terambil"] for h in hasil), n))
    print("Halaman acuan = tanpa offset          :", persen(sum(h["persis_label_lama"] for h in hasil), n))
    print("Halaman acuan = label yang tampil   :", persen(sum(h["persis_label_plus1"] for h in hasil), n))
    print("Halaman acuan di h+1 atau h+2      :", persen(sum(h["dalam_rentang_h1_h2"] for h in hasil), n))
    print("Toleransi 1 halaman dari h+1, top-k:", persen(sum(h["toleransi_1_dari_plus1"] for h in hasil), n))
    print("Toleransi 1 halaman dari h+1, top-1:", persen(sum(h["top1_plus1_toleransi_1"] for h in hasil), n))
    selisih = Counter(h["selisih_terdekat"] for h in hasil if h["selisih_terdekat"] is not None)
    print("Selisih (acuan - halaman) terdekat :", dict(sorted(selisih.items())))


def main() -> None:
    if len(sys.argv) < 2:
        print("Pemakaian: python -m app.scripts.evaluasi_rag <jalur_csv>")
        sys.exit(1)
    baris = muat_pertanyaan(sys.argv[1])
    print(f"{len(baris)} pertanyaan dimuat. Memuat model dan index (butuh beberapa detik)...")
    svc._load_resources()

    hasil = []
    for b in baris:
        hasil.append(nilai_satu(b, ambil_chunk(b["pertanyaan"], svc.TOP_K)))

    ringkas(hasil, f"Semua dokumen, TOP_K={svc.TOP_K}")
    per_dokumen = defaultdict(list)
    for h in hasil:
        per_dokumen[h["dokumen"]].append(h)
    for dokumen, daftar in per_dokumen.items():
        ringkas(daftar, dokumen)

    with open("evaluasi_rag_hasil.csv", "w", encoding="utf-8-sig", newline="") as f:
        penulis = csv.DictWriter(f, fieldnames=list(hasil[0].keys()))
        penulis.writeheader()
        for h in hasil:
            h = dict(h)
            h["halaman_terambil"] = " ".join(str(x) for x in h["halaman_terambil"])
            penulis.writerow(h)
    print("\nHasil per pertanyaan disimpan di evaluasi_rag_hasil.csv")


if __name__ == "__main__":
    main()
