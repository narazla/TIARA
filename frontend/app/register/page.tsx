"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Mail, Lock, Eye, EyeOff, User, Users, AlertCircle, Loader2, Waves, Stethoscope } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuth, getRoleHomePath } from "@/lib/auth/AuthContext";
import { getErrorMessage } from "@/lib/api/client";

const registerSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  role: z.enum(["elderly", "caregiver", "healthcare"]),
});

type RegisterFormData = z.infer<typeof registerSchema>;

const roles = [
  { 
    value: "elderly", 
    label: "Person in Care", 
    desc: "For older adults using daily check-ins and TIARA Companion." 
  },
  { 
    value: "caregiver", 
    label: "Caregiver", 
    desc: "For family members who monitor care insights and recommendations." 
  },
  { 
    value: "healthcare", 
    label: "Healthcare Worker", 
    desc: "For professionals reviewing reports and longitudinal summaries." 
  },
] as const;

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: "elderly" },
  });

  const selectedRole = watch("role");

  const onSubmit = async (data: RegisterFormData) => {
    setError(null);
    try {
      await authApi.register(data);
      const loginResponse = await authApi.login({ email: data.email, password: data.password });
      login(loginResponse.access_token, loginResponse.user);
      router.push(getRoleHomePath(loginResponse.user.role));
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
          <h1 className="text-xl font-bold text-foreground font-serif-editorial mb-1">Get started</h1>
          <p className="text-muted-foreground text-xs mb-4">Join TIARA&apos;s cognitive care platform</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Full name */}
            <div>
              <label htmlFor="full_name" className="block text-xs font-semibold text-foreground mb-1">
                Full name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/60" />
                <input
                  id="full_name"
                  placeholder="Your full name"
                  {...register("full_name")}
                  className={`w-full pl-9 pr-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all ${
                    errors.full_name ? "border-destructive bg-destructive/5" : "border-input bg-card/50 hover:border-input/80 focus:bg-card"
                  }`}
                />
              </div>
              {errors.full_name && (
                <p className="mt-1 text-xs text-destructive flex items-center gap-1 font-semibold">
                  <AlertCircle className="w-3 h-3" /> {errors.full_name.message}
                </p>
              )}
            </div>

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
                  placeholder="Min. 8 characters"
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
                <><Loader2 className="w-4 h-4 animate-spin" /> Creating account...</>
              ) : (
                "Create account"
              )}
            </button>
          </form>

          <p className="text-center text-xs text-muted-foreground mt-4 font-medium">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:text-primary-dark font-bold underline underline-offset-4">
              Sign in
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
