"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Video,
  Sparkles,
  CheckCircle2,
  ChevronDown,
  LogOut,
  LayoutDashboard,
  Flame,
  Clock,
  Heart,
  Waves,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { elderlyApi } from "@/lib/api";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
import { getGreeting } from "@/lib/utils";

interface HomeData {
  user: { full_name: string; greeting: string };
  todays_checkin: { completed: boolean; session_id: string | null; completed_at: string | null };
  streak_days: number;
}

function ElderlyHomeContent() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [homeData, setHomeData] = useState<HomeData | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const greeting = getGreeting();

  useEffect(() => {
    const fetchHome = async () => {
      try {
        const data = await elderlyApi.getHome();
        setHomeData(data);
      } catch {
        setHomeData({
          user: { full_name: user?.full_name || "Friend", greeting },
          todays_checkin: { completed: false, session_id: null, completed_at: null },
          streak_days: 0,
        });
      } finally {
        setIsLoading(false);
      }
    };
    fetchHome();
  }, [user, greeting]);

  const displayName = homeData?.user.full_name || user?.full_name || "Friend";
  const checkinCompleted = homeData?.todays_checkin.completed || false;
  const streakDays = homeData?.streak_days || 0;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="bg-card/90 backdrop-blur-md border-b border-border sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center">
            <img src="/Logo.png" alt="TIARA Logo" className="h-[48px] object-contain" />
          </div>

          {/* Profile dropdown */}
          <div className="relative">
            <button
              id="profile-menu-btn"
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 bg-secondary/80 hover:bg-secondary rounded-xl px-4 py-2 transition-colors cursor-pointer"
            >
              <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center font-bold text-white text-xs">
                {(user?.full_name || "U")[0].toUpperCase()}
              </div>
              <span className="text-sm font-semibold text-foreground max-w-[120px] truncate">
                {user?.full_name}
              </span>
              <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {dropdownOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -4 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="absolute right-0 top-full mt-2 w-52 bg-card rounded-2xl shadow-md border border-border overflow-hidden z-50 animate-fade-in"
              >
                <button
                  id="dashboard-btn"
                  onClick={() => {
                    setDropdownOpen(false);
                    router.push("/caregiver/pin");
                  }}
                  className="w-full flex items-center gap-3 px-4 py-3.5 text-sm font-bold text-foreground hover:bg-secondary transition-colors cursor-pointer text-left"
                >
                  <LayoutDashboard className="w-4.5 h-4.5 text-primary" />
                  Dashboard
                </button>
                <div className="h-px bg-border" />
                <button
                  id="logout-btn"
                  onClick={() => { setDropdownOpen(false); logout(); }}
                  className="w-full flex items-center gap-3 px-4 py-3.5 text-sm font-bold text-destructive hover:bg-destructive/5 transition-colors cursor-pointer text-left"
                >
                  <LogOut className="w-4.5 h-4.5" />
                  Logout
                </button>
              </motion.div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-16 flex-grow flex flex-col items-center justify-center w-full">
        {/* Welcome Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-2xl mx-auto space-y-6"
        >
          <h1 className="text-4xl md:text-5xl font-bold font-serif-editorial text-foreground leading-tight">
            Welcome, {displayName}
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            How are you feeling today? Let&apos;s do a gentle check-in or spend some time with TIARA.
          </p>

          {/* Simple side-by-side buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6">
            <Link
              id="daily-checkin-btn"
              href="/elderly/check-in"
              className="w-full sm:w-auto inline-flex items-center justify-center bg-primary hover:bg-primary-dark text-white font-bold text-lg px-8 py-3.5 rounded-xl transition-all shadow-md hover:shadow-lg cursor-pointer"
            >
              Daily Checkin
            </Link>
            <Link
              id="companion-btn"
              href="/elderly/companion"
              className="w-full sm:w-auto inline-flex items-center justify-center bg-card border border-border text-foreground hover:bg-secondary font-bold text-lg px-8 py-3.5 rounded-xl transition-all shadow-sm cursor-pointer"
            >
              Tiara Companion
            </Link>
          </div>
        </motion.div>
      </main>
    </div>
  );
}

export default function ElderlyHomePage() {
  return (
    <ProtectedRoute allowedRoles={["elderly"]}>
      <ElderlyHomeContent />
    </ProtectedRoute>
  );
}
