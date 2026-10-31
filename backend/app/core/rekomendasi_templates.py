"""
Templat teks rekomendasi perawatan BERBASIS ATURAN.

Ini bukan AI. Teks dipilih dari tingkat Skor Risiko Kognitif sesi check-in
(Rendah, Sedang, Tinggi) dan tren sederhana dibanding sepekan terakhir.
Semua teks adalah saran umum untuk pendamping, bukan saran medis, tidak
menyebut obat atau dosis, dan tidak menyatakan diagnosis.

Berkas ini sengaja dipisah supaya mudah dibaca dan ditinjau oleh manusia.
Setiap butir: (kategori, judul, deskripsi).
"""
from app.core.constants import RecommendationCategory as K

CATATAN_UMUM = (
    "Saran umum berbasis aturan dari hasil check-in terakhir. "
    "Bukan saran medis dan bukan pengganti tenaga kesehatan."
)

TEMPLAT = {
    "rendah": [
        (K.ROUTINE, "Pertahankan rutinitas yang sudah berjalan",
         "Jaga jam makan, tidur, dan check-in tetap sama setiap hari agar lansia merasa tenang dan terbiasa."),
        (K.COGNITIVE, "Aktivitas mengenang ringan",
         "Ajak lansia melihat foto lama atau bercerita tentang masa mudanya selama 10 sampai 15 menit."),
        (K.SOCIAL, "Mengobrol santai bersama keluarga",
         "Luangkan waktu mengobrol atau makan bersama tanpa terburu-buru."),
    ],
    "sedang": [
        (K.ROUTINE, "Pastikan rutinitas harian teratur",
         "Tetapkan jam bangun, makan, dan tidur yang tetap. Rutinitas yang mudah ditebak membantu lansia merasa aman."),
        (K.COGNITIVE, "Latihan mengingat yang menyenangkan",
         "Ajak menyusun teka-teki sederhana, menyebutkan nama anggota keluarga di foto, atau bernyanyi lagu lama. "
         "Hentikan jika lansia tampak lelah atau kesal."),
        (K.SOCIAL, "Libatkan keluarga atau tetangga",
         "Atur kunjungan singkat atau telepon dari orang yang dikenal lansia agar ia tetap merasa terhubung."),
        (K.WELLBEING, "Perhatikan perubahan perilaku",
         "Catat hal yang tampak berbeda, misalnya lebih pendiam atau lebih sering lupa, "
         "untuk disampaikan kepada tenaga kesehatan jika berlanjut."),
    ],
    "tinggi": [
        (K.ROUTINE, "Jaga suasana tenang hari ini",
         "Kurangi hal yang membuat bingung atau terburu-buru, dan dampingi lansia saat kegiatan harian."),
        (K.COGNITIVE, "Pilih aktivitas ringan, jangan memaksa",
         "Pilih kegiatan yang disukai lansia dan hentikan jika ia lelah atau kesal. Hindari menguji ingatannya."),
        (K.SOCIAL, "Temani dan ajak bicara dengan tenang",
         "Duduk bersama, bicara pelan, dan beri waktu lansia untuk menjawab."),
        (K.MEDICAL, "Pertimbangkan berkonsultasi dengan tenaga kesehatan",
         "Skor hari ini berada pada kategori Tinggi. Ini indikator informatif, bukan diagnosis. "
         "Sampaikan pola bicara dan perubahan yang Anda amati kepada dokter atau tenaga kesehatan."),
        (K.WELLBEING, "Kapan perlu segera mencari bantuan",
         "Jika lansia mendadak sangat bingung, terjatuh, atau kondisinya memburuk dengan cepat, "
         "segera cari pertolongan medis. Jaga juga kondisi Anda sebagai pendamping dan bagi tugas dengan keluarga."),
    ],
}

# Ditambahkan jika skor hari ini lebih tinggi dari rata-rata sepekan terakhir.
TEMPLAT_TREN_NAIK = (
    K.WELLBEING,
    "Skor hari ini lebih tinggi dari biasanya",
    "Skor hari ini lebih tinggi dari rata-rata sepekan terakhir. Catat perubahan yang Anda lihat "
    "dan sampaikan pada kunjungan dokter berikutnya.",
)

# Prioritas lebih tinggi diurutkan lebih dulu. Dibuat di atas data seed.
PRIORITAS = {
    K.MEDICAL: 100,
    K.WELLBEING: 95,
    K.ROUTINE: 90,
    K.COGNITIVE: 85,
    K.SOCIAL: 80,
}
