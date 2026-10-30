"""
Enkripsi rekaman suara saat disimpan (Fernet, kunci dari MEDIA_ENCRYPTION_KEY di .env).

Berkas berakhiran .enc dienkripsi. Berkas lama tanpa akhiran itu dibaca apa adanya.
Kalau kunci hilang, rekaman terenkripsi tidak bisa dibuka lagi, jadi simpan salinan kunci.
"""
from pathlib import Path

from cryptography.fernet import Fernet

from app.core.config import settings


class KunciTidakAda(Exception):
    """MEDIA_ENCRYPTION_KEY belum diatur."""


def _fernet() -> Fernet:
    kunci = settings.MEDIA_ENCRYPTION_KEY
    if not kunci:
        raise KunciTidakAda("MEDIA_ENCRYPTION_KEY belum diatur")
    return Fernet(kunci.encode())


def enkripsi(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def baca_rekaman(jalur: str) -> bytes:
    """Baca rekaman dari disk. Bila terenkripsi, dekripsi di memori (tidak ditulis ulang ke disk)."""
    isi = Path(jalur).read_bytes()
    if jalur.endswith(".enc"):
        return _fernet().decrypt(isi)
    return isi
