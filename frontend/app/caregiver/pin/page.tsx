"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Shield, Loader2, AlertCircle, ArrowLeft, Waves } from "lucide-react";
import Link from "next/link";
import { caregiverApi } from "@/lib/api";
import { getErrorMessage } from "@/lib/api/client";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";

function CaregiverPinContent() {
  const router = useRouter();
  const [pin, setPin] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handlePinChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;

    const newPin = [...pin];
    newPin[index] = value.slice(-1);
    setPin(newPin);
    setError(null);

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    if (newPin.every((d) => d !== "") && value) {
      submitPin(newPin.join(""));
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !pin[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const submitPin = async (pinValue: string) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await caregiverApi.verifyPin(pinValue);
      localStorage.setItem("tiara_caregiver_token", response.dashboard_token);
      router.push("/caregiver/dashboard");
    } catch (err) {
      const message = getErrorMessage(err);
      setError(
        message.includes("Incorrect") || message.includes("Invalid")
          ? "Incorrect PIN. Please try again."
          : message
      );
      setPin(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const pinValue = pin.join("");
    if (pinValue.length === 6) {
      submitPin(pinValue);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 relative">
      {/* Background decoration */}
      <div className="absolute top-20 right-20 w-80 h-80 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-64 h-64 bg-terracotta/5 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md z-10"
      >
        {/* Logo */}
        <div className="text-center mb-2">
          <Link href="/" className="inline-flex items-center justify-center group">
            <img src="/Logo.png" alt="TIARA Logo" className="h-[120px] object-contain mx-auto transition-transform group-hover:scale-105" />
          </Link>
        </div>

        {/* Card */}
        <div className="bg-card rounded-[24px] border border-border/80 shadow-md p-6">
          <div className="text-center mb-5">
            <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-2.5">
              <Shield className="w-5 h-5 text-primary-dark" />
            </div>
            <h1 className="text-xl font-bold font-serif-editorial text-foreground">Caregiver Dashboard PIN</h1>
            <p className="text-muted-foreground text-xs mt-1 leading-normal max-w-[280px] mx-auto font-medium">
              This dashboard contains care insights and is protected for caregiver access.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-center text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wider">
                Enter your 6-digit PIN
              </label>
              <div className="flex justify-center gap-2">
                {pin.map((digit, index) => (
                  <input
                    key={index}
                    id={`pin-${index}`}
                    ref={(el) => { inputRefs.current[index] = el; }}
                    type="password"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handlePinChange(index, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    className={`w-10 h-12 text-center text-xl font-bold rounded-xl border-2 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                      error
                        ? "border-destructive bg-destructive/5 text-destructive"
                        : digit
                        ? "border-primary bg-primary/5 text-primary-dark"
                        : "border-input bg-card/60 text-foreground"
                    }`}
                    disabled={isSubmitting}
                  />
                ))}
              </div>
            </div>

            {/* Error box */}
            {error && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-2.5 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
                <p className="text-xs text-destructive font-medium">{error}</p>
              </div>
            )}

            {/* Demo PIN */}
            <div className="bg-secondary rounded-2xl p-3 border border-border/60">
              <p className="text-[10px] font-bold text-muted-foreground text-center">
                Demo PIN: <span className="font-mono font-bold text-foreground bg-card/70 px-2 py-0.5 rounded border border-border/50">123456</span>
              </p>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting || pin.some((d) => d === "")}
              className="w-full bg-primary hover:bg-primary-dark disabled:bg-primary/50 text-white font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2 shadow-sm cursor-pointer text-sm"
            >
              {isSubmitting ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Verifying...</>
              ) : (
                "Access Dashboard"
              )}
            </button>
          </form>

          <div className="mt-4 text-center">
            <Link
              href="/elderly/home"
              className="inline-flex items-center gap-1.5 text-xs font-bold text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to home
            </Link>
          </div>
        </div>

        {/* Disclaimer */}
        <p className="text-center text-[10px] text-muted-foreground/60 mt-4 px-4 leading-relaxed">
          ⚕️ TIARA is not a medical diagnosis tool. Informational support only.
        </p>
      </motion.div>
    </div>
  );
}

export default function CaregiverPinPage() {
  return (
    <ProtectedRoute>
      <CaregiverPinContent />
    </ProtectedRoute>
  );
}
