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
  Waves,
  X,
  Volume2,
  Trophy,
} from "lucide-react";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";

const ACTIVITIES = [
  {
    id: "story",
    icon: BookOpen,
    title: "Story Time",
    desc: "Tell or read comforting stories together. We will listen and converse with you.",
    color: "text-terracotta bg-terracotta/10",
  },
  {
    id: "memory",
    icon: Trophy,
    title: "Memory Matching",
    desc: "A simple, stimulating memory card matching game to exercise your recall.",
    color: "text-primary-dark bg-primary/15",
  },
  {
    id: "mood",
    icon: Heart,
    title: "Mood Journal",
    desc: "Express how you feel today through recording a voice message or drawing.",
    color: "text-rose-500 bg-rose-500/10",
  },
  {
    id: "family",
    icon: Image,
    title: "Family Album",
    desc: "Recall memories of family and look at past photos together.",
    color: "text-accent bg-accent/10",
  },
];

function CompanionContent() {
  const [activeActivity, setActiveActivity] = useState<string | null>(null);

  // Memory game simple state
  const [matches, setMatches] = useState(0);

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
            Back to Home
          </Link>
          <div className="flex items-center gap-2.5">
            <img src="/Logo.png" alt="TIARA Logo" className="h-[48px] object-contain" />
            <span className="text-xl font-bold tracking-tight text-foreground">Companion</span>
          </div>
          <div className="w-20" />
        </div>
      </header>

      {/* Main Grid */}
      <main className="max-w-4xl mx-auto px-6 py-12 flex-1 w-full">
        <div className="text-center mb-10">
          <h1 className="text-3xl md:text-4xl font-bold font-serif-editorial text-foreground leading-tight mb-3">
            TIARA Companion Activities
          </h1>
          <p className="text-base md:text-lg text-muted-foreground max-w-lg mx-auto leading-relaxed">
            Select any activity below to start a relaxing, engaging companion session.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {ACTIVITIES.map(({ id, icon: Icon, title, desc, color }) => (
            <button
              key={id}
              onClick={() => {
                setActiveActivity(id);
                if (id === "memory") setMatches(0);
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

      {/* Overlay modal for mock activities */}
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

              {/* Story activity */}
              {activeActivity === "story" && (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-xl bg-terracotta/10 text-terracotta">
                      <BookOpen className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold font-serif-editorial">Comforting Story Time</h2>
                  </div>
                  <p className="text-muted-foreground leading-relaxed mb-6 font-medium">
                    TIARA will read you a comforting story about a calm forest lake, or you can record and share your own stories.
                  </p>
                  <div className="bg-secondary/40 border border-border/60 rounded-2xl p-5 mb-6 text-center">
                    <p className="italic text-base text-foreground font-medium mb-3">
                      &ldquo;Once upon a time, in a small village nestled among gentle hills, there was a garden that bloomed with gold wildflowers...&rdquo;
                    </p>
                    <button
                      onClick={() => {
                        const synth = window.speechSynthesis;
                        if (synth) {
                          synth.cancel();
                          synth.speak(new SpeechSynthesisUtterance("Once upon a time, in a small village nestled among gentle hills, there was a garden that bloomed with gold wildflowers"));
                        }
                      }}
                      className="inline-flex items-center gap-1.5 text-sm font-bold text-primary hover:text-primary-dark"
                    >
                      <Volume2 className="w-4.5 h-4.5" /> Speak Out loud
                    </button>
                  </div>
                  <button
                    onClick={() => setActiveActivity(null)}
                    className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3.5 rounded-xl transition-colors cursor-pointer"
                  >
                    Done Story Time
                  </button>
                </div>
              )}

              {/* Memory Matching Game */}
              {activeActivity === "memory" && (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-xl bg-primary/10 text-primary-dark">
                      <Trophy className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold font-serif-editorial">Memory Exercise</h2>
                  </div>
                  <p className="text-muted-foreground leading-relaxed mb-6 font-medium">
                    Stimulate memory by completing the match! What is the opposite of:
                  </p>
                  <div className="bg-secondary/40 border border-border/60 rounded-2xl p-5 mb-6 text-center space-y-4">
                    <p className="font-bold text-xl text-foreground">Sunny Day ☀️</p>
                    {matches === 0 ? (
                      <div className="grid grid-cols-2 gap-2.5">
                        <button
                          onClick={() => setMatches(1)}
                          className="bg-card hover:bg-primary/10 hover:border-primary border border-border text-sm font-bold py-3 rounded-xl transition-all cursor-pointer"
                        >
                          Rainy Day 🌧️
                        </button>
                        <button
                          onClick={() => alert("Try again!")}
                          className="bg-card hover:bg-primary/10 hover:border-primary border border-border text-sm font-bold py-3 rounded-xl transition-all cursor-pointer"
                        >
                          Winter Day ❄️
                        </button>
                      </div>
                    ) : (
                      <div className="text-emerald-700 font-bold flex flex-col items-center justify-center gap-1.5 py-4">
                        <Sparkles className="w-6 h-6" /> Correct! You matched it!
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setActiveActivity(null)}
                    className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3.5 rounded-xl transition-colors cursor-pointer"
                  >
                    Close Game
                  </button>
                </div>
              )}

              {/* Mood Journal */}
              {activeActivity === "mood" && (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-xl bg-rose-500/10 text-rose-500">
                      <Heart className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold font-serif-editorial">Mood Check-In</h2>
                  </div>
                  <p className="text-muted-foreground leading-relaxed mb-6 font-medium">
                    How has your mood been in the last few hours? Sharing is a helpful emotional outlet.
                  </p>
                  <div className="grid grid-cols-3 gap-2.5 mb-6">
                    {[
                      { emoji: "😊", text: "Calm & Happy" },
                      { emoji: "😐", text: "Just Fine" },
                      { emoji: "😔", text: "A Bit Lonely" },
                    ].map(({ emoji, text }) => (
                      <button
                        key={text}
                        onClick={() => {
                          alert(`Thank you for sharing. We saved your mood: ${text}`);
                          setActiveActivity(null);
                        }}
                        className="bg-card hover:bg-rose-50 border border-border hover:border-rose-300 p-4 rounded-2xl flex flex-col items-center justify-center transition-all cursor-pointer"
                      >
                        <span className="text-2xl mb-1.5">{emoji}</span>
                        <span className="text-xs font-bold text-foreground">{text}</span>
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setActiveActivity(null)}
                    className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3.5 rounded-xl transition-colors cursor-pointer"
                  >
                    Done
                  </button>
                </div>
              )}

              {/* Family Album */}
              {activeActivity === "family" && (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-xl bg-accent/10 text-accent">
                      <Image className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold font-serif-editorial">Family Albums</h2>
                  </div>
                  <p className="text-muted-foreground leading-relaxed mb-6 font-medium">
                    Caregivers can upload pictures for you. Relive these happy memories.
                  </p>
                  <div className="bg-secondary/40 border border-border/60 rounded-2xl p-5 mb-6 text-center py-8">
                    <Image className="w-10 h-10 text-muted-foreground/60 mx-auto mb-2" />
                    <p className="text-sm font-semibold text-muted-foreground">No photos uploaded yet</p>
                    <p className="text-xs text-muted-foreground/50 mt-1">Caregivers can add family memories in their portal</p>
                  </div>
                  <button
                    onClick={() => setActiveActivity(null)}
                    className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3.5 rounded-xl transition-colors cursor-pointer"
                  >
                    Close Album
                  </button>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer disclaimer */}
      <footer className="text-center text-xs text-muted-foreground/60 py-6 leading-relaxed">
        ⚕️ TIARA is not a medical diagnosis tool. Companion support and daily care routines only.
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
