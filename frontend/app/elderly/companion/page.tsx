"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  BookOpen,
  Sparkles,
  Heart,
  Image,
  X,
  Volume2,
  Trophy,
} from "lucide-react";
import { moodApi } from "@/lib/api";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";

const ACTIVITIES = [
  {
    id: "story",
    icon: BookOpen,
    title: "Waktu Bercerita",
    desc: "Dengarkan kisah yang menenangkan, dibacakan oleh TIARA.",
    color: "text-terracotta bg-terracotta/10",
  },
  {
    id: "memory",
    icon: Trophy,
    title: "Latihan Memori",
    desc: "Latihan daya ingat sederhana dengan pertanyaan pilihan.",
    color: "text-primary-dark bg-primary/15",
  },
  {
    id: "mood",
    icon: Heart,
    title: "Jurnal Suasana Hati",
    desc: "Pilih suasana hati Bapak/Ibu hari ini. Pilihan Bapak/Ibu akan tersimpan.",
    color: "text-rose-500 bg-rose-500/10",
  },
  {
    id: "family",
    icon: Image,
    title: "Album Keluarga",
    desc: "Album foto keluarga. Fitur ini sedang dikembangkan.",
    color: "text-accent bg-accent/10",
  },
];

const MOODS = [
  { value: "tenang_bahagia", emoji: "😊", text: "Tenang dan Bahagia" },
  { value: "biasa", emoji: "😐", text: "Biasa Saja" },
  { value: "sedikit_kesepian", emoji: "😔", text: "Sedikit Kesepian" },
] as const;

type MoodStatus = "idle" | "saving" | "saved" | "error";

function CompanionContent() {
  const [activeActivity, setActiveActivity] = useState<string | null>(null);

  // Latihan memori
  const [matches, setMatches] = useState(0);
  const [wrongAnswer, setWrongAnswer] = useState(false);

  // Jurnal suasana hati
  const [moodStatus, setMoodStatus] = useState<MoodStatus>("idle");
  const [savedMoodLabel, setSavedMoodLabel] = useState<string | null>(null);

  const handleSelectMood = async (value: string, label: string) => {
    setMoodStatus("saving");
    try {
      await moodApi.save(value);
      setSavedMoodLabel(label);
      setMoodStatus("saved");
    } catch (err) {
      console.error("Gagal menyimpan suasana hati", err);
      setMoodStatus("error");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="bg-card/90 backdrop-blur-md border-b border-border sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link
            href="/elderly/home"
            className="flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            Kembali ke Beranda
          </Link>
          <div className="flex items-center gap-2.5">
            <img src="/Logo.png" alt="Logo TIARA" className="h-[32px] object-contain" />
            
          </div>
          <div className="w-20" />
        </div>
      </header>

      {/* Main Grid */}
      <main className="max-w-4xl mx-auto px-6 py-12 flex-1 w-full">
        <div className="text-center mb-10">
          <h1 className="text-3xl md:text-4xl font-bold font-serif-editorial text-foreground leading-tight mb-3">
            Aktivitas TIARA Companion
          </h1>
          <p className="text-base md:text-lg text-muted-foreground max-w-lg mx-auto leading-relaxed">
            Pilih aktivitas di bawah ini untuk memulai sesi companion yang menyenangkan.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {ACTIVITIES.map(({ id, icon: Icon, title, desc, color }) => (
            <button
              key={id}
              onClick={() => {
                setActiveActivity(id);
                if (id === "memory") {
                  setMatches(0);
                  setWrongAnswer(false);
                }
                if (id === "mood") {
                  setMoodStatus("idle");
                  setSavedMoodLabel(null);
                }
              }}
              className="warm-card p-6 text-left hover:shadow-md transition-all active:scale-[0.99] duration-200 cursor-pointer flex gap-4.5 items-start"
            >
              <div className={`p-4.5 rounded-2xl flex-shrink-0 ${color}`}>
                <Icon className="w-8 h-8" />
              </div>
              <div>
                <h3 className="font-bold text-xl text-foreground leading-snug mb-1.5">{title}</h3>
                <p className="text-sm md:text-base text-muted-foreground leading-relaxed font-medium">{desc}</p>
              </div>
            </button>
          ))}
        </div>
      </main>

      {/* Jendela aktivitas */}
      <AnimatePresence>
        {activeActivity && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-foreground/20 backdrop-blur-sm z-50 flex items-center justify-center p-6"
          >
            <motion.div
              initial={{ scale: 0.95, y: 12 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 12 }}
              className="bg-card border border-border rounded-[28px] p-8 max-w-lg w-full relative shadow-xl"
            >
              <button
                onClick={() => setActiveActivity(null)}
                className="absolute top-4 right-4 p-2 rounded-full hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>

              {/* Waktu Bercerita */}
              {activeActivity === "story" && (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-xl bg-terracotta/10 text-terracotta">
                      <BookOpen className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold font-serif-editorial">Waktu Bercerita</h2>
                  </div>
                  <p className="text-muted-foreground leading-relaxed mb-6 font-medium">
                    TIARA dapat membacakan cerita yang menenangkan untuk Bapak/Ibu.
                  </p>
                  <div className="bg-secondary/40 border border-border/60 rounded-2xl p-5 mb-6 text-center">
                    <p className="italic text-base text-foreground font-medium mb-3">
                      &ldquo;Dahulu kala, di sebuah desa kecil di antara bukit-bukit yang tenang, terdapat sebuah taman yang bermekaran dengan bunga liar berwarna emas...&rdquo;
                    </p>
                    <button
                      onClick={() => {
                        const synth = window.speechSynthesis;
                        if (synth) {
                          synth.cancel();
                          const utt = new SpeechSynthesisUtterance(
                            "Dahulu kala, di sebuah desa kecil di antara bukit-bukit yang tenang, terdapat sebuah taman yang bermekaran dengan bunga liar berwarna emas"
                          );
                          utt.lang = "id-ID";
                          synth.speak(utt);
                        }
                      }}
                      className="inline-flex items-center gap-1.5 text-sm font-bold text-primary hover:text-primary-dark"
                    >
                      <Volume2 className="w-4.5 h-4.5" /> Bacakan keras
                    </button>
                  </div>
                  <button
                    onClick={() => setActiveActivity(null)}
                    className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3.5 rounded-xl transition-colors cursor-pointer"
                  >
                    Selesai Bercerita
                  </button>
                </div>
              )}

              {/* Latihan Memori */}
              {activeActivity === "memory" && (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-xl bg-primary/10 text-primary-dark">
                      <Trophy className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold font-serif-editorial">Latihan Memori</h2>
                  </div>
                  <p className="text-muted-foreground leading-relaxed mb-6 font-medium">
                    Pilih jawaban yang tepat. Apa lawan dari:
                  </p>
                  <div className="bg-secondary/40 border border-border/60 rounded-2xl p-5 mb-6 text-center space-y-4">
                    <p className="font-bold text-xl text-foreground">Hari Cerah ☀️</p>
                    {matches === 0 ? (
                      <>
                        <div className="grid grid-cols-2 gap-2.5">
                          <button
                            onClick={() => setMatches(1)}
                            className="bg-card hover:bg-primary/10 hover:border-primary border border-border text-sm font-bold py-3 rounded-xl transition-all cursor-pointer"
                          >
                            Hari Hujan 🌧️
                          </button>
                          <button
                            onClick={() => setWrongAnswer(true)}
                            className="bg-card hover:bg-primary/10 hover:border-primary border border-border text-sm font-bold py-3 rounded-xl transition-all cursor-pointer"
                          >
                            Hari Dingin ❄️
                          </button>
                        </div>
                        {wrongAnswer && (
                          <p className="text-sm font-semibold text-muted-foreground">
                            Belum tepat. Silakan coba lagi.
                          </p>
                        )}
                      </>
                    ) : (
                      <div className="text-emerald-700 font-bold flex flex-col items-center justify-center gap-1.5 py-4">
                        <Sparkles className="w-6 h-6" /> Benar. Bapak/Ibu berhasil menjawab.
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setActiveActivity(null)}
                    className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3.5 rounded-xl transition-colors cursor-pointer"
                  >
                    Tutup
                  </button>
                </div>
              )}

              {/* Jurnal Suasana Hati */}
              {activeActivity === "mood" && (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-xl bg-rose-500/10 text-rose-500">
                      <Heart className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold font-serif-editorial">Catatan Suasana Hati</h2>
                  </div>

                  {moodStatus === "saved" ? (
                    <div className="bg-secondary/40 border border-border/60 rounded-2xl p-6 mb-6 text-center">
                      <p className="font-bold text-lg text-foreground mb-1">Terima kasih sudah berbagi.</p>
                      <p className="text-muted-foreground font-medium">
                        Suasana hati Bapak/Ibu tercatat: {savedMoodLabel}
                      </p>
                    </div>
                  ) : (
                    <>
                      <p className="text-muted-foreground leading-relaxed mb-6 font-medium">
                        Bagaimana suasana hati Bapak/Ibu beberapa jam terakhir? Berbagi perasaan sangat membantu.
                      </p>
                      <div className="grid grid-cols-3 gap-2.5 mb-4">
                        {MOODS.map(({ value, emoji, text }) => (
                          <button
                            key={value}
                            disabled={moodStatus === "saving"}
                            onClick={() => handleSelectMood(value, text)}
                            className="bg-card hover:bg-rose-50 disabled:opacity-60 border border-border hover:border-rose-300 p-4 rounded-2xl flex flex-col items-center justify-center transition-all cursor-pointer"
                          >
                            <span className="text-2xl mb-1.5">{emoji}</span>
                            <span className="text-xs font-bold text-foreground">{text}</span>
                          </button>
                        ))}
                      </div>
                      {moodStatus === "saving" && (
                        <p className="text-sm font-semibold text-muted-foreground mb-4 text-center">Menyimpan...</p>
                      )}
                      {moodStatus === "error" && (
                        <p className="text-sm font-semibold text-destructive mb-4 text-center">
                          Suasana hati belum dapat disimpan. Silakan coba lagi.
                        </p>
                      )}
                    </>
                  )}

                  <button
                    onClick={() => setActiveActivity(null)}
                    className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3.5 rounded-xl transition-colors cursor-pointer"
                  >
                    Selesai
                  </button>
                </div>
              )}

              {/* Album Keluarga */}
              {activeActivity === "family" && (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-xl bg-accent/10 text-accent">
                      <Image className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold font-serif-editorial">Album Keluarga</h2>
                  </div>
                  <div className="bg-secondary/40 border border-border/60 rounded-2xl p-5 mb-6 text-center py-8">
                    <Image className="w-10 h-10 text-muted-foreground/60 mx-auto mb-2" />
                    <p className="text-sm font-semibold text-muted-foreground">Fitur album keluarga sedang dikembangkan</p>
                    <p className="text-xs text-muted-foreground/60 mt-1">Belum tersedia pada versi ini</p>
                  </div>
                  <button
                    onClick={() => setActiveActivity(null)}
                    className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3.5 rounded-xl transition-colors cursor-pointer"
                  >
                    Tutup
                  </button>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer disclaimer */}
      <footer className="text-center text-xs text-muted-foreground/60 py-6 leading-relaxed">
        ⚕️ TIARA bukan alat diagnosis medis. Hanya untuk dukungan Companion dan rutinitas perawatan harian.
      </footer>
    </div>
  );
}

export default function CompanionPage() {
  return (
    <ProtectedRoute allowedRoles={["elderly"]}>
      <CompanionContent />
    </ProtectedRoute>
  );
}
