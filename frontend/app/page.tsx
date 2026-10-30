"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  Heart,
  Users,
  CheckCircle2,
  Activity,
  Video,
  Stethoscope,
  ArrowRight,
  Sparkles,
} from "lucide-react";

const fadeIn = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

const stagger = {
  visible: { transition: { staggerChildren: 0.1 } },
};

const CAROUSEL_IMAGES = [
  "/Asset1.webp",
  "/Asset2.jpg",
  "/Asset3.png"
];

export default function LandingPage() {
  const [activeIdx, setActiveIdx] = useState(0);

  // Auto-play interval for carousel: every 3.5 seconds (3500ms)
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIdx((prev) => (prev + 1) % CAROUSEL_IMAGES.length);
    }, 3500);
    return () => clearInterval(timer);
  }, []);

  // Force scroll to top on mount/refresh to bypass browser auto-scroll on hash URLs
  useEffect(() => {
    if (typeof window !== "undefined") {
      if ("scrollRestoration" in window.history) {
        window.history.scrollRestoration = "manual";
      }
      window.scrollTo(0, 0);
    }
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-primary/30">
      {/* ── Navigation ─────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#2F3432]/90 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-[60px] flex items-center justify-between">
          <div className="flex items-center">
            <img src="/Logo.png" alt="Logo TIARA" className="h-[72px] object-contain brightness-0 invert" />
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm font-semibold text-white/80">
            <a href="#how-it-works" className="hover:text-white transition-colors">Cara kerja</a>
            <a href="#for-caregivers" className="hover:text-white transition-colors">Untuk caregiver</a>
            <a href="#trust" className="hover:text-white transition-colors">Kepercayaan &amp; keamanan</a>
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-semibold text-white/80 hover:text-white transition-colors"
            >
              Masuk
            </Link>
            <Link
              href="/register"
              className="bg-primary hover:bg-primary-dark text-white text-sm font-bold px-4 py-2 rounded-xl transition-colors shadow-sm cursor-pointer"
            >
              Mulai sekarang
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="min-h-screen lg:min-h-[calc(100vh-60px)] pt-[60px] pb-12 relative overflow-hidden bg-secondary flex items-center">
        {/* Soft background orbs */}
        <div className="absolute top-20 left-20 w-[450px] h-[450px] bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 left-10 w-96 h-96 bg-terracotta/5 rounded-full blur-3xl pointer-events-none" />

        {/* Content Container */}
        <div className="max-w-7xl mx-auto px-6 w-full grid lg:grid-cols-12 gap-12 items-center relative z-20">
          {/* Left: Copy */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={stagger}
            className="flex flex-col lg:col-span-6 py-12 lg:py-20"
          >
            <motion.h1
              variants={fadeIn}
              className="text-5xl lg:text-[56px] font-bold font-serif-editorial leading-[1.12] mb-6 text-foreground tracking-tight"
            >
              Perawatan kognitif penuh kasih, <span className="font-serif italic block lg:inline text-foreground/95">dipandu oleh AI.</span>
            </motion.h1>

            <motion.p variants={fadeIn} className="text-lg text-muted-foreground leading-relaxed mb-10 max-w-lg">
              TIARA dirancang untuk membantu keluarga memantau perubahan kognitif melalui
              check-in harian, catatan longitudinal, dan panduan demensia untuk caregiver.
            </motion.p>

            {/* Main Action Button */}
            <motion.div variants={fadeIn} className="pt-2">
              <Link
                href="/login"
                className="inline-flex items-center justify-center bg-primary hover:bg-primary-dark text-white font-bold text-base px-12 py-3 rounded-xl transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
              >
                Mulai sekarang
              </Link>
            </motion.div>

          </motion.div>
        </div>

        {/* Right: Full Height / Page Carousel Visual with Left Gradient Blending */}
        <div className="absolute inset-y-0 right-0 w-1/2 hidden lg:block z-10">
          <div className="w-full h-full relative">
            {/* Fade blending overlay on the left of the image (widened to 44 untuk transisi yang lebih halus) */}
            <div className="absolute inset-y-0 left-0 w-44 bg-gradient-to-r from-secondary to-transparent z-20 pointer-events-none" />

            <div className="w-full h-full">
              <AnimatePresence mode="wait">
                <motion.img
                  key={activeIdx}
                  src={CAROUSEL_IMAGES[activeIdx]}
                  alt={`Visual TIARA Companion ${activeIdx + 1}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.8 }}
                  className="w-full h-full object-cover"
                />
              </AnimatePresence>
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────── */}
      <section id="how-it-works" className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold font-serif-editorial text-foreground mb-4">
              Cara kerja TIARA
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Check-in harian membuat catatan berkala tentang kesehatan kognitif, yang dirancang untuk menampilkan pola bermakna dari waktu ke waktu.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-6">
            {[
              {
                step: "01",
                icon: Video,
                title: "Check-In Harian",
                desc: "TIARA mengajukan pertanyaan lisan yang ramah dan merekam jawaban lansia lewat kamera dan mikrofon perangkat.",
              },
              {
                step: "02",
                icon: Sparkles,
                title: "Analisis AI",
                desc: "Pola suara, koherensi bahasa, dan daya ingat dirancang untuk dianalisis oleh pipeline AI TIARA (dalam pengembangan).",
              },
              {
                step: "03",
                icon: Activity,
                title: "Pemantauan Tren",
                desc: "Indikator kognitif dirancang untuk dipantau dari waktu ke waktu agar perubahan yang berarti dapat terlihat.",
              },
              {
                step: "04",
                icon: Users,
                title: "Dukungan Caregiver",
                desc: "Caregiver menerima wawasan, peringatan, dan rekomendasi perawatan di dashboard yang dilindungi PIN.",
              },
            ].map(({ step, icon: Icon, title, desc }) => (
              <motion.div
                key={step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="bg-card rounded-2xl p-6 shadow-sm border border-border/70 hover:shadow-md transition-all duration-300"
              >
                <div className="text-xs font-bold text-primary mb-4 tracking-widest">{step}</div>
                <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-primary-dark" />
                </div>
                <h3 className="font-bold text-foreground mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Two experiences section ───────────────────────────── */}
      <section id="for-caregivers" className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold font-serif-editorial text-foreground mb-4">
              Dua pengalaman, satu sistem perawatan terhubung.
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Dirancang untuk lansia penerima perawatan, keluarga mereka, dan tim klinis.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Heart,
                audience: "Untuk Lansia",
                bg: "bg-secondary/40 border border-border/80",
                features: [
                  "Check-in harian yang hangat dan sederhana",
                  "Pertanyaan AI berbasis suara",
                  "Aktivitas TIARA Companion",
                  "Permainan memori dan pemantauan suasana hati",
                  "Hasil yang mendukung, bukan klinis",
                ],
              },
              {
                icon: Users,
                audience: "Untuk Caregiver",
                bg: "bg-card border border-border/80 shadow-sm",
                features: [
                  "Dashboard dilindungi PIN",
                  "Grafik tren risiko kognitif",
                  "Peringatan dan notifikasi cerdas",
                  "Rekomendasi perawatan berbasis AI",
                  "Chat Panduan Demensia AI",
                ],
              },
              {
                icon: Stethoscope,
                audience: "Untuk Tenaga Kesehatan",
                bg: "bg-primary/5 border border-primary/20",
                features: [
                  "Dashboard pemantauan pasien",
                  "Tren sesi longitudinal",
                  "Filter pasien berdasarkan tingkat risiko",
                  "Catatan klinis",
                  "Akses laporan bulanan",
                ],
              },
            ].map(({ icon: Icon, audience, bg, features }) => (
              <motion.div
                key={audience}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className={`rounded-[24px] p-8 ${bg} hover:shadow-md transition-shadow duration-300`}
              >
                <div className="w-12 h-12 rounded-2xl bg-secondary flex items-center justify-center mb-6">
                  <Icon className="w-6 h-6 text-primary-dark" />
                </div>
                <h3 className="text-xl font-bold font-serif-editorial text-foreground mb-6">{audience}</h3>
                <ul className="space-y-3.5">
                  {features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm text-muted-foreground font-medium">
                      <CheckCircle2 className="w-4.5 h-4.5 text-primary mt-0.5 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trust & Safety ────────────────────────────────────── */}
      <section id="trust" className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="inline-flex items-center gap-2 text-xs font-bold tracking-wider uppercase text-primary mb-6">
                <Shield className="w-4 h-4" />
                Kepercayaan &amp; Keamanan
              </div>
              <h2 className="text-4xl font-bold font-serif-editorial text-foreground mb-6">
                Dirancang dengan keamanan sebagai pondasi.
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-8">
                TIARA bukan alat diagnosis medis. Kami menggunakan bahasa yang jelas dan jujur tentang apa yang dapat dan tidak dapat disampaikan sistem kami, dan selalu mendorong penilaian klinis tepat waktu.
              </p>

              <div className="space-y-4">
                {[
                  {
                    title: "Perekaman berbasis persetujuan",
                    desc: "Akses kamera dan mikrofon memerlukan persetujuan eksplisit di setiap sesi.",
                  },
                  {
                    title: "Hanya indikator tren kognitif",
                    desc: "TIARA menampilkan pola dari waktu ke waktu. Sistem ini tidak mendiagnosis kondisi medis.",
                  },
                  {
                    title: "Akses caregiver dilindungi PIN",
                    desc: "Indikator klinis hanya terlihat oleh caregiver melalui PIN yang aman.",
                  },
                  {
                    title: "Selalu mendorong konsultasi klinis",
                    desc: "Setiap laporan dan peringatan mengarahkan ke penilaian profesional bila diperlukan.",
                  },
                ].map(({ title, desc }) => (
                  <div key={title} className="flex gap-4">
                    <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-bold text-foreground text-sm">{title}</p>
                      <p className="text-sm text-muted-foreground mt-0.5">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="bg-card border border-warning/30 rounded-[24px] p-8 shadow-sm"
            >
              <div className="flex items-start gap-3.5 mb-6">
                <Shield className="w-6 h-6 text-amber-600 mt-1 flex-shrink-0" />
                <h3 className="font-bold font-serif-editorial text-amber-800 text-lg">Pernyataan Medis</h3>
              </div>
              <p className="text-muted-foreground leading-relaxed">
                Analisis TIARA <strong className="text-foreground">bukan diagnosis medis</strong>. Indikator risiko kognitif bersifat informatif dan tidak dimaksudkan untuk menggantikan penilaian klinis profesional. Jika Anda khawatir tentang kesehatan kognitif anggota keluarga, silakan berkonsultasi dengan tenaga kesehatan yang berkualifikasi.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────── */}
      <section className="py-24 bg-primary text-white text-center relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-white/5 rounded-full blur-3xl pointer-events-none" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-2xl mx-auto px-6 relative z-10"
        >
          <h2 className="text-4xl font-bold font-serif-editorial mb-4">
            Mulai mendampingi orang terkasih Anda hari ini.
          </h2>
          <p className="text-primary-foreground/80 mb-10 text-lg">
            Bergabunglah dengan keluarga yang mengambil pendekatan proaktif terhadap kesehatan kognitif.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              href="/register"
              className="flex items-center gap-2 bg-white text-primary-dark hover:bg-secondary font-bold px-8 py-4 rounded-xl transition-all shadow-md cursor-pointer"
            >
              Daftar gratis
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/login"
              className="flex items-center gap-2 bg-primary-dark/30 border border-white/20 text-white hover:bg-primary-dark/50 font-bold px-8 py-4 rounded-xl transition-all cursor-pointer"
            >
              Masuk
            </Link>
          </div>
        </motion.div>
      </section>

    </div>
  );
}
