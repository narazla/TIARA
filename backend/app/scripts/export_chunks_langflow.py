"""Ekspor chunk 256 token ke satu file teks untuk diingest Langflow.
Tiap chunk diawali label dokumen dan halaman, dipisah penanda <<<CHUNK>>>."""
import pickle
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "services" / "rag_data" / "chunks_256token.pkl"
OUT = Path(__file__).resolve().parents[3] / "langflow" / "dokumen_chunks_256.txt"


def halaman_cetak(c):
    h = int(c["halaman"])
    return h + 1 if c["dokumen"].startswith("PNPK") else h


with open(DATA, "rb") as f:
    chunks = pickle.load(f)

bagian = [
    f"[{c['dokumen']}, Halaman {halaman_cetak(c)}]\n{c['teks'].strip()}"
    for c in chunks
]
JUMLAH_BAGIAN = 4
ukuran = -(-len(bagian) // JUMLAH_BAGIAN)  # pembulatan ke atas
for i in range(JUMLAH_BAGIAN):
    potongan = bagian[i * ukuran:(i + 1) * ukuran]
    if not potongan:
        break
    out = OUT.with_name(f"dokumen_chunks_256_bagian{i + 1}.txt")
    out.write_text("\n<<<CHUNK>>>\n".join(potongan), encoding="utf-8")
    print(out.name, len(potongan), "chunk")