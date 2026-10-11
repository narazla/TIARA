"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Mail, Lock, Eye, EyeOff, AlertCircle, Loader2, Waves } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuth, getRoleHomePath } from "@/lib/auth/AuthContext";
import { getErrorMessage } from "@/lib/api/client";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    try {
      const response = await authApi.login(data);
      login(response.access_token, response.user);
      router.push(getRoleHomePath(response.user.role));
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 relative">
      {/* Background orbs */}
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
            <img src="/Logo.png" alt="TIARA Logo" className="h-[120px] object-contain transition-transform group-hover:scale-105" />
          </Link>
        </div>

        {/* Card */}
        <div className="bg-card rounded-[24px] border border-border/80 shadow-md p-6">
          <h1 className="text-xl font-bold text-foreground font-serif-editorial mb-1">Welcome back</h1>
          <p className="text-muted-foreground text-xs mb-4">Sign in to continue your care journey with TIARA.</p>

          {/* Demo credentials hint */}
          <div className="bg-secondary rounded-2xl p-3.5 mb-4 border border-border/60">
            <p className="text-[10px] font-bold text-primary-dark mb-1 uppercase tracking-wide">Demo Credentials</p>
            <div className="space-y-1 text-[11px] text-muted-foreground font-medium">
              <p>Elderly: <span className="font-mono text-foreground bg-card/60 px-1 py-0.5 rounded border border-border/40">elderly@tiara.app</span> / <span className="font-mono text-foreground bg-card/60 px-1 py-0.5 rounded border border-border/40">password123</span></p>
              <p>Caregiver: <span className="font-mono text-foreground bg-card/60 px-1 py-0.5 rounded border border-border/40">caregiver@tiara.app</span> / <span className="font-mono text-foreground bg-card/60 px-1 py-0.5 rounded border border-border/40">password123</span></p>
              <p>Doctor: <span className="font-mono text-foreground bg-card/60 px-1 py-0.5 rounded border border-border/40">doctor@tiara.app</span> / <span className="font-mono text-foreground bg-card/60 px-1 py-0.5 rounded border border-border/40">password123</span></p>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-foreground mb-1">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/60" />
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  {...register("email")}
                  className={`w-full pl-9 pr-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                    errors.email ? "border-destructive bg-destructive/5" : "border-input bg-card/50 hover:border-input/80 focus:bg-card"
                  }`}
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-xs text-destructive flex items-center gap-1 font-semibold">
                  <AlertCircle className="w-3 h-3" /> {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-foreground mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/60" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  {...register("password")}
                  className={`w-full pl-9 pr-10 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                    errors.password ? "border-destructive bg-destructive/5" : "border-input bg-card/50 hover:border-input/80 focus:bg-card"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/60 hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-destructive flex items-center gap-1 font-semibold">
                  <AlertCircle className="w-3 h-3" /> {errors.password.message}
                </p>
              )}
            </div>

            {/* General error */}
            {error && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-2.5 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
                <p className="text-xs text-destructive font-medium">{error}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-primary hover:bg-primary-dark disabled:bg-primary/50 text-white font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2 shadow-sm cursor-pointer text-sm"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <p className="text-center text-xs text-muted-foreground mt-4 font-medium">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-primary hover:text-primary-dark font-bold underline underline-offset-4">
              Create one
            </Link>
          </p>
        </div>

        {/* Disclaimer */}
        <p className="text-center text-[10px] text-muted-foreground/60 mt-4 px-4 leading-relaxed">
          ⚕️ TIARA is not a medical diagnosis tool. Informational support only.
        </p>
      </motion.div>
    </div>
  );
}
