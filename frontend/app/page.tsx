"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { ConnectWallet } from "@/components/shared/ConnectWallet";
import { LiveOnChainStatus } from "@/components/shared/LiveOnChainStatus";
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
            <img src="/Logo.png" alt="TIARA Logo" className="h-[72px] object-contain brightness-0 invert" />
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm font-semibold text-white/80">
            <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
            <a href="#for-caregivers" className="hover:text-white transition-colors">For caregivers</a>
            <a href="#trust" className="hover:text-white transition-colors">Trust & safety</a>
          </div>

          <div className="flex items-center gap-4">
            <ConnectWallet />
            <Link
              href="/login"
              className="text-sm font-semibold text-white/80 hover:text-white transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="bg-primary hover:bg-primary-dark text-white text-sm font-bold px-4 py-2 rounded-xl transition-colors shadow-sm cursor-pointer"
            >
              Get started
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
              Immutable cognitive insights, <span className="font-serif italic block lg:inline text-foreground/95">secured on-chain.</span>
            </motion.h1>

            <motion.p variants={fadeIn} className="text-lg text-muted-foreground leading-relaxed mb-10 max-w-lg">
              TIARA — BOT Chain Care DApp helps families notice early cognitive changes through
              AI-guided check-ins, longitudinal analysis, and secure care checkpoints anchored on BOT Chain.
            </motion.p>

            {/* Main Action Button */}
            <motion.div variants={fadeIn} className="pt-2">
              <Link
                href="/login"
                className="inline-flex items-center justify-center bg-primary hover:bg-primary-dark text-white font-bold text-base px-12 py-3 rounded-xl transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
              >
                Get started
              </Link>
            </motion.div>

            <motion.div variants={fadeIn} className="mt-8 max-w-lg">
              <LiveOnChainStatus />
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
                  alt={`TIARA Companion Visual ${activeIdx + 1}`}
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
              How TIARA works
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              A gentle daily check-in creates a longitudinal record of cognitive health — surfacing patterns that matter, when they matter.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-6">
            {[
              {
                step: "01",
                icon: Video,
                title: "Daily Check-In",
                desc: "TIARA asks gentle spoken questions while observing voice and facial responses through the device camera.",
              },
              {
                step: "02",
                icon: Sparkles,
                title: "AI Analysis",
                desc: "Voice patterns, language coherence, and memory recall are analyzed by our AI pipeline.",
              },
              {
                step: "03",
                icon: Activity,
                title: "Trend Monitoring",
                desc: "Cognitive indicators are tracked over time and cryptographically recorded to surface meaningful changes with tamper-proof historical logs.",
              },
              {
                step: "04",
                icon: Users,
                title: "Caregiver Support",
                desc: "Caregivers receive insights, alerts, and care recommendations on a protected dashboard accessed securely through Web3 wallet authentication.",
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
              Two experiences, one connected care system.
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Designed for the person receiving care, their family, and their clinical team.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Heart,
                audience: "For Older Adults",
                bg: "bg-secondary/40 border border-border/80",
                features: [
                  "Warm, simple daily check-in",
                  "Spoken AI questions",
                  "TIARA Companion activities",
                  "Memory games & mood check",
                  "Encouraging, non-clinical results",
                ],
              },
              {
                icon: Users,
                audience: "For Caregivers",
                bg: "bg-card border border-border/80 shadow-sm",
                features: [
                  "PIN-protected dashboard",
                  "Cognitive risk trend charts",
                  "Smart alerts & notifications",
                  "AI care recommendations",
                  "Dementia Guidance AI chat",
                ],
              },
              {
                icon: Stethoscope,
                audience: "For Healthcare Workers",
                bg: "bg-primary/5 border border-primary/20",
                features: [
                  "Patient monitoring dashboard",
                  "Longitudinal session trends",
                  "Risk-level patient filters",
                  "Clinical notes",
                  "Monthly report access",
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
                Trust & Safety
              </div>
              <h2 className="text-4xl font-bold font-serif-editorial text-foreground mb-6">
                Designed with safety at its core.
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-8">
                TIARA is not a medical diagnosis tool. We use clear, honest language about what our system can and cannot tell you — and we always encourage timely clinical assessment.
              </p>

              <div className="space-y-4">
                {[
                  {
                    title: "Consent-based recordings",
                    desc: "Camera and microphone access requires explicit consent at every session.",
                  },
                  {
                    title: "Cognitive trend indicator only",
                    desc: "TIARA surfaces patterns over time — it does not diagnose conditions.",
                  },
                  {
                    title: "PIN-protected caregiver access",
                    desc: "Clinical indicators are only visible to caregivers through a secure PIN.",
                  },
                  {
                    title: "Web3-secured patient privacy",
                    desc: "Sensitive cognitive logs stay off-chain while cryptographic hashes and authorized wallet access protect the longitudinal care record.",
                  },
                  {
                    title: "Always encourages clinical consultation",
                    desc: "Every report and alert points toward professional assessment when warranted.",
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
                <h3 className="font-bold font-serif-editorial text-amber-800 text-lg">Medical Disclaimer</h3>
              </div>
              <p className="text-muted-foreground leading-relaxed">
                TIARA&apos;s analysis is <strong className="text-foreground">not a medical diagnosis</strong>. Cognitive risk indicators are informational only and are not intended to replace professional clinical assessment. If you have concerns about a loved one&apos;s cognitive health, please consult a qualified healthcare professional.
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
            Start supporting your loved one today.
          </h2>
          <p className="text-primary-foreground/80 mb-10 text-lg">
            Join families who are taking a proactive approach to cognitive wellness.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              href="/register"
              className="flex items-center gap-2 bg-white text-primary-dark hover:bg-secondary font-bold px-8 py-4 rounded-xl transition-all shadow-md cursor-pointer"
            >
              Get started free
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/login"
              className="flex items-center gap-2 bg-primary-dark/30 border border-white/20 text-white hover:bg-primary-dark/50 font-bold px-8 py-4 rounded-xl transition-all cursor-pointer"
            >
              Sign in
            </Link>
          </div>
        </motion.div>
      </section>

    </div>
  );
}
