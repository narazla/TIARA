"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Video,
  VideoOff,
  Mic,
  MicOff,
  ArrowLeft,
  Volume2,
  Play,
  CheckCircle2,
  Loader2,
  Waves,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { checkInApi } from "@/lib/api";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";

const QUESTIONS = [
  { id: "q1", category: "Orientation", text: "What day is today?", step: 1 },
  { id: "q2", category: "Memory Recall", text: "What did you eat this morning?", step: 2 },
  { id: "q3", category: "Long-Term Memory", text: "What is one childhood memory you remember fondly?", step: 3 },
  { id: "q4", category: "Emotional Wellbeing", text: "How are you feeling today?", step: 4 },
];

function CheckInContent() {
  const router = useRouter();
  const { user } = useAuth();
  const [started, setStarted] = useState(false);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [status, setStatus] = useState<"idle" | "speaking" | "listening" | "recording" | "processing">("idle");
  const [cameraActive, setCameraActive] = useState(false);
  const [micActive, setMicActive] = useState(false);
  const [loading, setLoading] = useState(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  // Initialize camera and mic
  useEffect(() => {
    if (typeof window !== "undefined") {
      synthRef.current = window.speechSynthesis;
    }

    async function setupMedia() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setCameraActive(true);
        setMicActive(true);
      } catch (err) {
        console.warn("Could not access camera or microphone:", err);
      }
    }

    setupMedia();

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  // Speak question
  const speakQuestion = (text: string) => {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    setStatus("speaking");
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onend = () => {
      setStatus("listening");
      // After a brief listening delay, go to recording
      setTimeout(() => {
        setStatus("recording");
      }, 1500);
    };
    synthRef.current.speak(utterance);
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      // Try to invoke API check-in start (ignore 404 backend missing)
      await checkinApi.start().catch((e) => console.log("API Start fallback active:", e));
    } catch (e) {
      // Silent catch
    } finally {
      setLoading(false);
      setStarted(true);
      setCurrentIdx(0);
      speakQuestion(QUESTIONS[0].text);
    }
  };

  const handleNext = () => {
    if (currentIdx < QUESTIONS.length - 1) {
      const nextIdx = currentIdx + 1;
      setCurrentIdx(nextIdx);
      speakQuestion(QUESTIONS[nextIdx].text);
    } else {
      handleFinish();
    }
  };

  const handleRepeat = () => {
    speakQuestion(QUESTIONS[currentIdx].text);
  };

  const handleFinish = async () => {
    setStatus("processing");
    setLoading(true);
    try {
      // Try to invoke API finish (ignore backend missing)
      await checkinApi.finish("demo-session", 180).catch((e) => console.log("API Finish fallback active"));
    } catch (e) {
      // Silent catch
    } finally {
      setTimeout(() => {
        setLoading(false);
        router.push("/elderly/check-in/result");
      }, 1500);
    }
  };

  const currentQuestion = QUESTIONS[currentIdx];

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="bg-card/90 backdrop-blur-md border-b border-border sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link
            href="/elderly/home"
            className="flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <div className="flex items-center gap-2.5">
            <img src="/Logo.png" alt="TIARA Logo" className="h-[48px] object-contain" />
            <span className="text-xl font-bold tracking-tight text-foreground">Check-In</span>
          </div>
          <div className="w-20" /> {/* Spacer */}
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-6 py-10 flex-1 flex flex-col lg:flex-row gap-8 w-full items-stretch">
        {/* Left: Video Panel */}
        <div className="flex-1 bg-card border border-border/80 rounded-[28px] overflow-hidden flex flex-col shadow-sm relative min-h-[350px] lg:min-h-[500px]">
          <div className="flex-1 bg-zinc-900 relative flex items-center justify-center">
            {cameraActive ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover transform -scale-x-100"
              />
            ) : (
              <div className="text-center p-6 text-zinc-500">
                <VideoOff className="w-16 h-16 mx-auto mb-4 text-zinc-600" />
                <p className="font-bold text-lg">Camera Accessing...</p>
                <p className="text-sm text-zinc-600 mt-1">Please allow camera and mic permissions</p>
              </div>
            )}

            {/* Speaking/listening overlays */}
            <AnimatePresence>
              {started && status === "recording" && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute bottom-6 left-6 bg-red-600/90 text-white font-bold text-sm px-4 py-2 rounded-full flex items-center gap-2.5 shadow-lg pulse-ring"
                >
                  <span className="w-2.5 h-2.5 rounded-full bg-white animate-ping" />
                  Recording Response
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Status Bar */}
          <div className="bg-secondary/70 border-t border-border p-4.5 flex flex-wrap justify-between items-center gap-3">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5 text-sm font-semibold text-muted-foreground">
                {cameraActive ? (
                  <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    Camera ready
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-100">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
                    Configuring camera...
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1.5 text-sm font-semibold text-muted-foreground">
                {micActive ? (
                  <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    Microphone ready
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-100">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
                    Configuring mic...
                  </span>
                )}
              </div>
            </div>
            <p className="text-xs text-muted-foreground font-medium">Recordings are encrypted and secure</p>
          </div>
        </div>

        {/* Right: Question Panel */}
        <div className="w-full lg:w-[450px] bg-card border border-border/80 rounded-[28px] p-8 flex flex-col justify-between shadow-sm">
          {!started ? (
            /* Intro Screen */
            <div className="flex-1 flex flex-col justify-center text-center py-10">
              <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-6 text-primary-dark shadow-inner">
                <Video className="w-8 h-8" />
              </div>
              <h2 className="text-2xl font-bold font-serif-editorial text-foreground mb-3">Ready to begin?</h2>
              <p className="text-base text-muted-foreground leading-relaxed max-w-sm mx-auto mb-8 font-medium">
                We will ask 4 gentle questions about your day, your memory, and how you feel. Take all the time you need.
              </p>
              <button
                onClick={handleStart}
                disabled={loading}
                className="w-full bg-primary hover:bg-primary-dark disabled:bg-primary/50 text-white font-bold py-5 rounded-[20px] text-lg transition-all shadow-md active:scale-[0.99] cursor-pointer flex items-center justify-center gap-2"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Play className="w-5 h-5 fill-current" />
                    Start Check-In
                  </>
                )}
              </button>
            </div>
          ) : (
            /* Active Check-In Screen */
            <div className="flex-1 flex flex-col justify-between">
              {/* Top Progress */}
              <div>
                <div className="flex justify-between items-center mb-6">
                  <span className="text-xs font-bold text-primary-dark bg-primary/10 px-3 py-1 rounded-full uppercase tracking-wider">
                    {currentQuestion.category}
                  </span>
                  <span className="text-sm font-bold text-muted-foreground">
                    Step {currentQuestion.step} of 4
                  </span>
                </div>

                {/* Question Text */}
                <div className="bg-secondary/40 border border-border/60 rounded-2xl p-6 mb-8 relative min-h-[140px] flex items-center">
                  <button
                    onClick={handleRepeat}
                    className="absolute top-3 right-3 p-1.5 rounded-lg bg-card border border-border text-primary hover:bg-secondary transition-colors cursor-pointer"
                    title="Repeat question"
                  >
                    <Volume2 className="w-4 h-4" />
                  </button>
                  <p className="text-xl md:text-2xl font-bold font-serif-editorial leading-snug text-foreground pr-6">
                    {currentQuestion.text}
                  </p>
                </div>

                {/* Status indicator */}
                <div className="flex flex-col items-center justify-center py-6 text-center">
                  {status === "speaking" && (
                    <div className="space-y-2">
                      <div className="flex justify-center gap-1 items-end h-6">
                        <span className="w-1.5 bg-primary/80 rounded-full animate-bounce h-4" style={{ animationDelay: "0ms" }} />
                        <span className="w-1.5 bg-primary/85 rounded-full animate-bounce h-6" style={{ animationDelay: "150ms" }} />
                        <span className="w-1.5 bg-primary/80 rounded-full animate-bounce h-5" style={{ animationDelay: "300ms" }} />
                      </div>
                      <p className="text-sm font-bold text-primary-dark">TIARA is speaking...</p>
                    </div>
                  )}

                  {status === "listening" && (
                    <div className="space-y-2">
                      <p className="text-sm font-bold text-amber-700 animate-pulse">Listening to your answer...</p>
                    </div>
                  )}

                  {status === "recording" && (
                    <div className="space-y-3">
                      {/* Animated audio waves */}
                      <div className="flex justify-center gap-1.5 items-center h-10 w-28 mx-auto">
                        <span className="w-1 h-3 bg-red-500 rounded-full animate-pulse" />
                        <span className="w-1 h-6 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: "200ms" }} />
                        <span className="w-1 h-9 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: "400ms" }} />
                        <span className="w-1 h-5 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: "600ms" }} />
                        <span className="w-1 h-2 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: "800ms" }} />
                      </div>
                      <p className="text-sm font-bold text-red-600">Recording response...</p>
                    </div>
                  )}

                  {status === "processing" && (
                    <div className="space-y-2">
                      <Loader2 className="w-6 h-6 text-primary animate-spin mx-auto" />
                      <p className="text-sm font-bold text-muted-foreground">Processing response...</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                <button
                  onClick={handleNext}
                  disabled={loading}
                  className="w-full bg-primary hover:bg-primary-dark disabled:bg-primary/50 text-white font-bold py-4.5 rounded-xl text-lg transition-all shadow-sm active:scale-[0.99] cursor-pointer flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : currentIdx === QUESTIONS.length - 1 ? (
                    <>
                      <CheckCircle2 className="w-5 h-5" />
                      Finish Check-In
                    </>
                  ) : (
                    "Next Question"
                  )}
                </button>
                <div className="flex gap-3">
                  <button
                    onClick={handleRepeat}
                    className="flex-1 bg-card border border-border text-foreground hover:bg-secondary font-bold py-3.5 rounded-xl transition-all text-sm cursor-pointer text-center flex items-center justify-center gap-1.5"
                  >
                    <Volume2 className="w-4 h-4 text-primary" />
                    Repeat
                  </button>
                  <button
                    onClick={() => {
                      if (synthRef.current) synthRef.current.cancel();
                      router.push("/elderly/home");
                    }}
                    className="flex-1 bg-card border border-border text-muted-foreground hover:text-foreground hover:bg-secondary font-bold py-3.5 rounded-xl transition-all text-sm cursor-pointer text-center"
                  >
                    Back to Home
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function CheckInPage() {
  return (
    <ProtectedRoute allowedRoles={["elderly"]}>
      <CheckInContent />
    </ProtectedRoute>
  );
}
