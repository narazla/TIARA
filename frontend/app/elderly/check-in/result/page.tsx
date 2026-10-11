"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { CheckCircle2, Heart, Calendar, ShieldCheck, Waves } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";

function CheckInResultContent() {
  const { user } = useAuth();
  const displayName = user?.full_name || "Friend";

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between p-6">
      {/* Background decoration */}
      <div className="absolute top-10 right-10 w-80 h-80 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-20 left-10 w-72 h-72 bg-terracotta/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="max-w-xl mx-auto w-full flex justify-between items-center py-4 z-10">
        <div className="flex items-center">
          <img src="/Logo.png" alt="TIARA Logo" className="h-[48px] object-contain" />
        </div>
      </header>

      {/* Main card */}
      <main className="max-w-md mx-auto w-full z-10 my-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="bg-card border border-border/80 rounded-[28px] p-8 shadow-sm text-center"
        >
          {/* Success Icon */}
          <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-6 text-primary-dark shadow-inner">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          {/* Heading */}
          <h1 className="text-3xl font-bold font-serif-editorial text-foreground leading-tight mb-2">
            Congratulations,
          </h1>
          <p className="text-xl font-semibold text-primary-dark font-serif-editorial mb-6">
            {displayName}
          </p>

          <div className="bg-secondary/40 border border-border/55 rounded-2xl p-5 mb-8 text-left space-y-4">
            <div className="flex gap-3">
              <Heart className="w-5 h-5 text-terracotta flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-sm text-foreground">Overall, you&apos;re doing good.</p>
                <p className="text-xs text-muted-foreground mt-0.5">Thank you for sharing your thoughts and memory with us today.</p>
              </div>
            </div>

            <div className="h-px bg-border/60" />

            <div className="flex gap-3">
              <Calendar className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-sm text-foreground">Next check-in tomorrow</p>
                <p className="text-xs text-muted-foreground mt-0.5">We will notify you when it is ready. A daily routine supports cognitive health.</p>
              </div>
            </div>

            <div className="h-px bg-border/60" />

            <div className="flex gap-3">
              <ShieldCheck className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-sm text-foreground">Secure & private</p>
                <p className="text-xs text-muted-foreground mt-0.5">Your responses have been securely stored and shared with your caregiver.</p>
              </div>
            </div>
          </div>

          <Link
            href="/elderly/home"
            className="w-full bg-primary hover:bg-primary-dark text-white font-bold py-4.5 rounded-xl text-lg transition-all shadow-sm active:scale-[0.99] cursor-pointer flex items-center justify-center gap-1.5"
          >
            Return to Home
          </Link>
        </motion.div>
      </main>

      {/* Footer disclaimer */}
      <footer className="text-center text-xs text-muted-foreground/60 max-w-sm mx-auto z-10 mt-6 leading-relaxed">
        ⚕️ TIARA is not a medical diagnosis tool. Informational support and daily care routines only.
      </footer>
    </div>
  );
}

export default function CheckInResultPage() {
  return (
    <ProtectedRoute allowedRoles={["elderly"]}>
      <CheckInResultContent />
    </ProtectedRoute>
  );
}
