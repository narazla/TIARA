"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  AlertTriangle,
  Heart,
  Brain,
  FileText,
  LogOut,
  ChevronRight,
  ShieldAlert,
  ShieldCheck,
  Send,
  Loader2,
  Waves,
  Calendar,
  CheckSquare,
  Activity,
  Bot,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { caregiverApi, guidanceApi } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthContext";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
import ReactMarkdown from 'react-markdown';
import { isAxiosError } from "axios";

interface TrendPoint {
  date: string;
  risk_score: number;
  risk_level: string;
}

interface AlertData {
  id: string;
  // Nilai dari model: "info" | "warning" | "critical"
  severity: "info" | "warning" | "critical" | "low" | "medium" | "high";
  title: string;
  description: string;
  suggested_action: string;
  created_at: string;
  is_read: boolean;
}

interface LatestSession {
  session_id: string;
  completed_at: string;
  risk_score: number;
  risk_level: string;
}

interface DashboardData {
  patient: { id: string; full_name: string; age: number | null };
  latest_session: LatestSession | null;
  trend_data: TrendPoint[];
  memory_consistency: number | null;
  memory_consistency_delta: number | null;
  avg_response_delay: number | null;
  avg_response_delay_delta: number | null;
  speech_hesitation_rate: number | null;
  speech_hesitation_rate_delta: number | null;
  unread_alerts: number;
  is_simulated: boolean;
}

interface RecommendationData {
  id: string;
  title: string;
  description: string;
  priority: number;
}

interface RecommendationsGroup {
  today_plan: RecommendationData[];
  cognitive_activities: RecommendationData[];
  social_suggestions: RecommendationData[];
  medical_notes: RecommendationData[];
  when_to_seek_help: RecommendationData[];
}

interface ContentJson {
  jumlah_sesi?: number;
  jumlah_tanpa_suara?: number;
  avg_skor_risiko?: number | null;
  skor_tertinggi?: number | null;
  skor_terendah?: number | null;
  sebaran_level?: { Tinggi: number; Sedang: number; Rendah: number };
  perbandingan_bulan_lalu?: string;
  jumlah_peringatan?: number;
  ringkasan?: string;
  catatan_tetap?: string;
  catatan?: string;
}

interface ReportData {
  id: string;
  title: string;
  report_month: string;
  checkin_count: number | null;
  avg_risk_score: number | null;
  content_json?: ContentJson | null;
  created_at: string;
}

interface ChatMessage {
  id: string;
  sender: "user" | "bot";
  text: string;
}

const GUIDANCE_PROMPTS = [
  "Apa yang sebaiknya dilakukan caregiver saat penderita demensia gelisah di malam hari?",
  "Bagaimana menjaga kebiasaan tidur lansia dengan demensia?",
  "Bagaimana cara mengelola stres bagi caregiver?",
  "Bagaimana caregiver membantu lansia berpindah tempat dengan aman?",
];

const SEVERITY_LABEL: Record<string, string> = {
  critical: "Kritis",
  warning: "Peringatan",
  info: "Info",
  high: "Tinggi",
  medium: "Sedang",
  low: "Rendah",
};

const severityStyle = (s: string): string =>
  s === "critical" || s === "high"
    ? "bg-destructive/15 text-destructive"
    : s === "warning" || s === "medium"
    ? "bg-warning/15 text-amber-700"
    : "bg-primary/15 text-primary-dark";

function cetakLaporan(printId: string, judul: string) {
  const sumber = document.getElementById(printId);
  if (!sumber) return;

  const rootId = "tiara-print-root";
  const styleId = "tiara-print-style";
  document.getElementById(rootId)?.remove();

  const root = document.createElement("div");
  root.id = rootId;

  const kepala = document.createElement("div");
  const nama = document.createElement("div");
  nama.textContent = "TIARA";
  nama.style.cssText = "font-size:22px;font-weight:bold;margin-bottom:4px;";
  const sub = document.createElement("div");
  sub.textContent = judul;
  sub.style.cssText =
    "font-size:14px;color:#555;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #ccc;";
  kepala.appendChild(nama);
  kepala.appendChild(sub);

  const salinan = sumber.cloneNode(true) as HTMLElement;
  salinan.removeAttribute("id");
  salinan
    .querySelectorAll(".tiara-print-hide, .tiara-hc-print-hide")
    .forEach((n) => n.remove());

  root.appendChild(kepala);
  root.appendChild(salinan);
  document.body.appendChild(root);

  let el = document.getElementById(styleId) as HTMLStyleElement | null;
  if (!el) {
    el = document.createElement("style");
    el.id = styleId;
    document.head.appendChild(el);
  }
  el.textContent = `
    @media screen {
      #${rootId} { display: none !important; }
    }
    @media print {
      body > *:not(#${rootId}) { display: none !important; }
      #${rootId} { display: block !important; padding: 24px; color: #111; background: #fff; }
      #${rootId} * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
  `;

  const bersihkan = () => {
    document.getElementById(rootId)?.remove();
    window.removeEventListener("afterprint", bersihkan);
  };
  window.addEventListener("afterprint", bersihkan);
  window.print();
}

function ReportCard({ r }: { r: ReportData }) {
  const cj = r.content_json;
  const adaRingkasan = cj?.ringkasan;
  const adaSebaran = cj?.sebaran_level;
  const adaPerbandingan = cj?.perbandingan_bulan_lalu;
  const adaCatatan = cj?.catatan_tetap;
  const adaCatatanLama = cj?.catatan;
  const printId = `laporan-cetak-${r.id}`;

  return (
    <div id={printId} className="bg-card border border-border/70 rounded-2xl p-6 shadow-sm space-y-3">
      <div className="flex items-start gap-4">
        <div className="p-3 bg-primary/10 rounded-xl text-primary-dark flex-shrink-0 tiara-print-hide">
          <FileText className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg text-foreground">{r.title}</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {r.checkin_count != null ? `${r.checkin_count} sesi check-in.` : ""}
            {r.avg_risk_score != null ? ` Rata-rata Skor Risiko Kognitif: ${r.avg_risk_score.toFixed(1)}.` : ""}
          </p>
          <p className="text-[10px] text-muted-foreground mt-1">
            Dibuat: {new Date(r.created_at).toLocaleString("id-ID")}
          </p>
        </div>
        <button
          onClick={() => cetakLaporan(printId, r.title)}
          className="tiara-print-hide flex-shrink-0 flex items-center gap-1.5 border border-border hover:bg-secondary text-foreground font-bold px-3 py-1.5 rounded-xl text-xs transition-colors cursor-pointer"
          title="Cetak atau simpan sebagai PDF"
        >
          <FileText className="w-3.5 h-3.5" />
          Cetak / Simpan PDF
        </button>
      </div>

      {adaSebaran && (
        <div className="flex gap-2 flex-wrap">
          {(["Tinggi", "Sedang", "Rendah"] as const).map((label) => {
            const n = adaSebaran[label];
            if (n === undefined) return null;
            const style =
              label === "Tinggi"
                ? "bg-destructive/10 text-destructive"
                : label === "Sedang"
                ? "bg-warning/10 text-amber-700"
                : "bg-primary/10 text-primary-dark";
            return (
              <span
                key={label}
                className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border border-border/50 ${style}`}
              >
                {label}: {n}
              </span>
            );
          })}
        </div>
      )}

      {adaRingkasan && (
        <p className="text-sm text-foreground leading-relaxed">{adaRingkasan}</p>
      )}

      {adaPerbandingan && (
        <p className="text-xs text-muted-foreground italic">{adaPerbandingan}</p>
      )}

      {adaCatatanLama && (
        <p className="text-xs text-muted-foreground italic">{adaCatatanLama}</p>
      )}

      {adaCatatan && (
        <p className="text-[11px] text-muted-foreground border-t border-border/40 pt-2 mt-1 leading-relaxed">
          {adaCatatan}
        </p>
      )}
    </div>
  );
}

function CaregiverDashboardContent() {
  const router = useRouter();
  const { logout, user } = useAuth();
  const [activeTab, setActiveTab] = useState<"dashboard" | "alerts" | "recommendations" | "guidance" | "reports">("dashboard");
  const [mounted, setMounted] = useState(false);

  // Data States
  const [patient, setPatient] = useState<{ id: string; full_name: string; age: number | null } | null>(null);
  const [trendData, setTrendData] = useState<TrendPoint[]>([]);
  const [latestSession, setLatestSession] = useState<LatestSession | null>(null);
  const [isSimulated, setIsSimulated] = useState(false);
  const [memoryConsistency, setMemoryConsistency] = useState<number | null>(null);
  const [memoryDelta, setMemoryDelta] = useState<number | null>(null);
  const [avgResponseDelay, setAvgResponseDelay] = useState<number | null>(null);
  const [delayDelta, setDelayDelta] = useState<number | null>(null);
  const [speechHesitationRate, setSpeechHesitationRate] = useState<number | null>(null);
  const [hesitationDelta, setHesitationDelta] = useState<number | null>(null);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationsGroup>({
    today_plan: [],
    cognitive_activities: [],
    social_suggestions: [],
    medical_notes: [],
    when_to_seek_help: [],
  });
  const [reports, setReports] = useState<ReportData[]>([]);
  const [generateLoading, setGenerateLoading] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [generateSuccess, setGenerateSuccess] = useState<string | null>(null);
  const [selectedBulan, setSelectedBulan] = useState<string>(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });

  // AI Guidance Chat States
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "bot",
      text: "Halo, saya Asisten Panduan Demensia TIARA. Silakan tanyakan cara mendampingi keluarga Anda, mulai dari rutinitas harian sampai perilaku yang perlu diperhatikan.",
    },
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement | null>(null);

  // Loading state
  const [loading, setLoading] = useState(true);

  // Check caregiver PIN token
  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem("tiara_caregiver_token");
    if (!token) {
      router.push("/caregiver/pin");
    }
  }, [router]);

  // Load Dashboard Data
  useEffect(() => {
    const loadData = async () => {
      try {
        const dash: DashboardData = await caregiverApi.getDashboard();
        setPatient(dash.patient);
        setLatestSession(dash.latest_session);
        setTrendData(dash.trend_data || []);
        setIsSimulated(dash.is_simulated ?? false);
        setMemoryConsistency(dash.memory_consistency);
        setMemoryDelta(dash.memory_consistency_delta);
        setAvgResponseDelay(dash.avg_response_delay);
        setDelayDelta(dash.avg_response_delay_delta);
        setSpeechHesitationRate(dash.speech_hesitation_rate);
        setHesitationDelta(dash.speech_hesitation_rate_delta);

        const alertRes = await caregiverApi.getAlerts();
        setAlerts(alertRes.alerts || []);

        const recRes = await caregiverApi.getRecommendations();
        setRecommendations(recRes);

        const repRes = await caregiverApi.getReports();
        setReports(repRes.reports || []);
      } catch (err) {
        if (isAxiosError(err) && err.response?.status === 401) {
          localStorage.removeItem("tiara_caregiver_token");
          logout();
          return;
        }
        console.error("Error loading dashboard data", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  // Scroll chat to bottom
  useEffect(() => {
    const chatContainer = chatContainerRef.current;
    if (chatContainer) {
      chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: "smooth" });
    }
  }, [chatMessages]);

  const handleSendChat = async (textToSend?: string) => {
    const query = textToSend || chatInput;
    if (!query.trim()) return;

    if (!textToSend) setChatInput("");

    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      sender: "user",
      text: query,
    };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatLoading(true);

    try {
      const response = await guidanceApi.ask(query);
      const botMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: "bot",
        text: response.answer || "Maaf, tidak dapat mengambil jawaban saat ini. Silakan coba lagi.",
      };
      setChatMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      const botErrorMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: "bot",
        text: isAxiosError(e) && e.response?.status === 401 ? "Sesi Anda sudah berakhir. Silakan masuk kembali." : "Maaf, sistem panduan sedang tidak dapat dihubungi. Silakan coba lagi sebentar lagi.",
      };
      setChatMessages((prev) => [...prev, botErrorMsg]);
      if (isAxiosError(e) && e.response?.status === 401) {
        setTimeout(() => {
          localStorage.removeItem("tiara_caregiver_token");
          logout();
        }, 1500);
      }
    } finally {
      setChatLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("tiara_caregiver_token");
    logout();
    router.push("/login");
  };

  const currentRiskLevel = latestSession?.risk_level ?? null;

  // Helper: format a delta value for display
  const formatDelta = (delta: number | null, unit: string): string => {
    if (delta === null) return "";
    const sign = delta > 0 ? "+" : "";
    return `${sign}${delta.toLocaleString("id-ID")}${unit} dari pekan lalu`;
  };

  return (
    <div className="h-screen bg-background text-foreground flex overflow-hidden">
      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className="w-64 h-full bg-card border-r border-border flex flex-col justify-between flex-shrink-0">
        <div>
          {/* Logo */}
          <div className="h-20 border-b border-border flex items-center px-6">
            <img src="/Logo.png" alt="TIARA Logo" className="h-[40px] object-contain" />
          </div>

          {/* Navigation */}
          <nav className="p-4 space-y-1">
            {[
              { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
              { id: "alerts", label: "Peringatan", icon: AlertTriangle, count: alerts.filter(a => !a.is_read).length },
              { id: "recommendations", label: "Rekomendasi", icon: CheckSquare },
              { id: "guidance", label: "Panduan Demensia", icon: Bot },
              { id: "reports", label: "Laporan Bulanan", icon: FileText },
            ].map(({ id, label, icon: Icon, count }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`w-full sidebar-item ${
                  activeTab === id ? "sidebar-item-active" : "sidebar-item-inactive"
                }`}
              >
                <Icon className="w-4.5 h-4.5" />
                <span className="flex-1 text-left">{label}</span>
                {count !== undefined && count > 0 && (
                  <span className="text-[10px] font-bold bg-destructive text-white rounded-full px-2 py-0.5 ml-2">
                    {count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 mb-4.5">
            <div className="w-9 h-9 rounded-full bg-secondary flex items-center justify-center font-bold text-sm text-foreground">
              {(user?.full_name || "C")[0]}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-foreground truncate">{user?.full_name}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-destructive hover:bg-destructive/5 transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            Keluar
          </button>
        </div>
      </aside>

      {/* ── Main Workspace ──────────────────────────────────── */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Header */}
        <header className="h-20 min-h-20 bg-card border-b border-border flex items-center justify-between px-8 sticky top-0 z-30">
          <div className="flex items-center gap-3.5">
            <div className="w-9 h-9 rounded-full bg-secondary flex items-center justify-center font-bold text-primary-dark">
              {patient?.full_name ? patient.full_name[0] : "P"}
            </div>
            <div>
              <h1 className="font-bold text-base text-foreground font-serif-editorial">
                {patient?.full_name || "Profil Pasien Terhubung"}
              </h1>
              <p className="text-xs text-muted-foreground font-medium">Portal Pemantauan Caregiver</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {currentRiskLevel === null ? (
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full bg-muted/50 text-muted-foreground border border-border">
                ● Belum ada data
              </span>
            ) : currentRiskLevel === "high" ? (
              <span className="risk-badge-high">● Status Risiko Tinggi</span>
            ) : currentRiskLevel === "medium" ? (
              <span className="risk-badge-medium">● Status Risiko Sedang</span>
            ) : (
              <span className="risk-badge-low">● Status Risiko Rendah</span>
            )}
          </div>
        </header>

        {/* Workspace Content */}
        <div className="p-8 flex-1 max-w-5xl w-full mx-auto">

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
          ) : (
            <AnimatePresence mode="wait">
              {/* Tab 1: Dashboard */}
              {activeTab === "dashboard" && (
                <motion.div
                  key="dashboard"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className="space-y-8"
                >
                  {/* Stats Overview */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <div className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm">
                      <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Konsistensi Memori</p>
                      <p className="text-2xl font-bold font-serif-editorial text-foreground mt-2">
                        {memoryConsistency !== null ? `${memoryConsistency.toLocaleString("id-ID")}%` : "Belum ada data"}
                      </p>
                      <p className="text-xs text-muted-foreground font-semibold mt-1">
                        {formatDelta(memoryDelta, "%")}
                      </p>
                    </div>
                    <div className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm">
                      <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Jeda Respons</p>
                      <p className="text-2xl font-bold font-serif-editorial text-foreground mt-2">
                        {avgResponseDelay !== null ? `${avgResponseDelay.toLocaleString("id-ID")} dtk` : "Belum ada data"}
                      </p>
                      <p className="text-xs text-muted-foreground font-semibold mt-1">
                        {formatDelta(delayDelta, " dtk")}
                      </p>
                    </div>
                    <div className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm">
                      <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Keraguan Bicara</p>
                      <p className="text-2xl font-bold font-serif-editorial text-foreground mt-2">
                        {speechHesitationRate !== null ? `${speechHesitationRate.toLocaleString("id-ID")} kali/menit` : "Belum ada data"}
                      </p>
                      <p className="text-xs text-muted-foreground font-semibold mt-1">
                        {formatDelta(hesitationDelta, " kali/menit")}
                      </p>
                    </div>
                  </div>

                  {/* Chart and Alerts grid */}
                  <div className="grid lg:grid-cols-3 gap-8">
                    {/* Line Chart */}
                    <div className="lg:col-span-2 bg-card border border-border/70 rounded-[24px] p-6 shadow-sm">
                      <h2 className="text-lg font-bold font-serif-editorial text-foreground mb-1">Skor Risiko Kognitif (30 Hari)</h2>
                      <p className="text-xs text-muted-foreground mb-5">Indikator informatif, bukan diagnosis.</p>
                      <div className="h-64">
                        {mounted && trendData.length > 0 ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={trendData}>
                              <defs>
                                <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.2} />
                                  <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
                                </linearGradient>
                              </defs>
                              <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={11} tickLine={false} />
                              <YAxis domain={[0, 10]} stroke="var(--color-text-muted)" fontSize={11} tickLine={false} />
                              <Tooltip />
                              <Area type="monotone" dataKey="risk_score" stroke="var(--color-primary)" strokeWidth={2.5} fillOpacity={1} fill="url(#colorRisk)" />
                            </AreaChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="h-full flex items-center justify-center text-muted-foreground text-sm font-medium">
                            Belum ada sesi pemeriksaan dalam 30 hari terakhir.
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Quick Alerts */}
                    <div className="bg-card border border-border/70 rounded-[24px] p-6 shadow-sm flex flex-col">
                      <h2 className="text-lg font-bold font-serif-editorial text-foreground mb-4.5 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-terracotta" />
                        Peringatan Terbaru
                      </h2>
                      <div className="flex-1 space-y-3.5 overflow-y-auto max-h-64 pr-1">
                        {alerts.length === 0 ? (
                          <div className="text-center py-8 text-muted-foreground text-sm font-medium">
                            Belum ada peringatan
                          </div>
                        ) : (
                          alerts.slice(0, 3).map((a) => (
                            <div key={a.id} className="border border-border/60 rounded-xl p-3 bg-secondary/30">
                              <div className="flex justify-between items-start mb-1">
                                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${severityStyle(a.severity)}`}>
                                  {SEVERITY_LABEL[a.severity] ?? a.severity}
                                </span>
                                <span className="text-[10px] text-muted-foreground font-medium">
                                  {new Date(a.created_at).toLocaleDateString("id-ID")}
                                </span>
                              </div>
                              <h4 className="font-bold text-sm text-foreground">{a.title}</h4>
                              <p className="text-xs text-muted-foreground mt-0.5 leading-normal">{a.description}</p>
                            </div>
                          ))
                        )}
                      </div>
                      <button
                        onClick={() => setActiveTab("alerts")}
                        className="w-full text-center text-sm font-bold text-primary hover:text-primary-dark mt-4 border-t border-border/60 pt-3"
                      >
                        Lihat semua peringatan
                      </button>
                    </div>
                  </div>

                  {/* Care Recommendations Preview */}
                  <div className="bg-card border border-border/70 rounded-[24px] p-6 shadow-sm">
                    <h2 className="text-lg font-bold font-serif-editorial text-foreground mb-4.5">Tindakan yang Disarankan</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                      {recommendations.today_plan.slice(0, 2).map((r) => (
                        <div key={r.id} className="flex gap-3 border border-border/60 rounded-xl p-4 bg-secondary/20">
                          <CheckSquare className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                          <div>
                            <h4 className="font-bold text-sm text-foreground">{r.title}</h4>
                            <p className="text-xs text-muted-foreground mt-0.5 leading-normal">{r.description}</p>
                          </div>
                        </div>
                      ))}
                      {recommendations.cognitive_activities.slice(0, 2).map((r) => (
                        <div key={r.id} className="flex gap-3 border border-border/60 rounded-xl p-4 bg-secondary/20">
                          <Brain className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
                          <div>
                            <h4 className="font-bold text-sm text-foreground">{r.title}</h4>
                            <p className="text-xs text-muted-foreground mt-0.5 leading-normal">{r.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Tab 2: Alerts Feed */}
              {activeTab === "alerts" && (
                <motion.div
                  key="alerts"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className="space-y-6"
                >
                  <h2 className="text-2xl font-bold font-serif-editorial text-foreground">Daftar Peringatan</h2>
                  <div className="space-y-4">
                    {alerts.length === 0 ? (
                      <p className="text-muted-foreground text-sm font-medium">Belum ada peringatan untuk pasien ini.</p>
                    ) : (
                      alerts.map((a) => (
                        <div key={a.id} className="bg-card border border-border/70 rounded-2xl p-6 shadow-sm flex gap-4.5 items-start">
                          <div className={`p-3 rounded-xl flex-shrink-0 ${severityStyle(a.severity)}`}>
                            <AlertTriangle className="w-6 h-6" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-center mb-1">
                              <h3 className="font-bold text-lg text-foreground">{a.title}</h3>
                              <span className="text-xs text-muted-foreground font-medium">
                                {new Date(a.created_at).toLocaleString("id-ID")}
                              </span>
                            </div>
                            <p className="text-sm text-muted-foreground leading-relaxed mb-3">{a.description}</p>
                            {a.suggested_action && (
                              <div className="bg-secondary/40 border border-border/50 rounded-xl p-3 text-xs leading-relaxed text-foreground font-medium">
                                <span className="font-bold text-primary-dark block mb-0.5">Tindakan yang Disarankan:</span>
                                {a.suggested_action}
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </motion.div>
              )}

              {/* Tab 3: Recommendations */}
              {activeTab === "recommendations" && (
                <motion.div
                  key="recommendations"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className="space-y-8"
                >
                  <div>
                    <h2 className="text-2xl font-bold font-serif-editorial text-foreground">Rekomendasi Perawatan</h2>
                    <p className="text-xs text-muted-foreground font-medium mt-1.5">
                      Rekomendasi berbasis aturan dari hasil check-in terakhir. Bukan saran medis dan bukan pengganti tenaga kesehatan.
                    </p>
                  </div>

                  {/* Sectioned recommendations */}
                  {[
                    { title: "Rencana Rutinitas Hari Ini", data: recommendations.today_plan, icon: Calendar, color: "text-primary" },
                    { title: "Latihan Kognitif", data: recommendations.cognitive_activities, icon: Brain, color: "text-accent" },
                    { title: "Saran Sosial", data: recommendations.social_suggestions, icon: Heart, color: "text-terracotta" },
                    { title: "Catatan Kesehatan dan Medis", data: recommendations.medical_notes, icon: FileText, color: "text-amber-700" },
                    { title: "Konsultasi Tenaga Kesehatan", data: recommendations.when_to_seek_help, icon: ShieldAlert, color: "text-destructive" },
                  ].map(({ title, data, icon: Icon, color }) => (
                    <div key={title} className="bg-card border border-border/70 rounded-[24px] p-6 shadow-sm">
                      <h3 className="text-lg font-bold font-serif-editorial text-foreground mb-4.5 flex items-center gap-2.5">
                        <Icon className={`w-5.5 h-5.5 ${color}`} />
                        {title}
                      </h3>
                      {data.length === 0 ? (
                        <p className="text-sm text-muted-foreground italic font-medium pl-8">Belum ada rekomendasi untuk kategori ini.</p>
                      ) : (
                        <div className="space-y-3.5 pl-8">
                          {data.map((r) => (
                            <div key={r.id} className="border-b border-border/50 last:border-0 pb-3.5 last:pb-0">
                              <h4 className="font-bold text-base text-foreground mb-0.5">{r.title}</h4>
                              <p className="text-sm text-muted-foreground leading-relaxed">{r.description}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </motion.div>
              )}

              {/* Tab 4: Dementia Guidance AI Chat */}
              {activeTab === "guidance" && (
                <motion.div
                  key="guidance"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className="flex flex-col h-[600px] bg-card border border-border/80 rounded-[28px] overflow-hidden shadow-sm"
                >
                  {/* Chat Header */}
                  <div className="bg-secondary/40 border-b border-border px-6 py-4 flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-primary/20 flex items-center justify-center text-primary-dark">
                      <Bot className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="font-bold text-foreground">TIARA Companion Panduan Demensia</h2>
                      <p className="text-xs text-muted-foreground font-medium">Konseling AI untuk caregiver dan saran penanganan perilaku</p>
                    </div>
                  </div>

                  {/* Chat Area */}
                  <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4">
                    {chatMessages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-md rounded-2xl px-4.5 py-3 text-sm leading-relaxed ${
                            msg.sender === "user"
                              ? "bg-primary text-white font-semibold rounded-br-none"
                              : "bg-secondary text-foreground font-medium rounded-bl-none border border-border/60"
                          }`}
                        >
                          {msg.sender === "user" ? (
                            msg.text
                          ) : (
                            <div className="prose prose-sm max-w-none dark:prose-invert">
                              <ReactMarkdown>{msg.text}</ReactMarkdown>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="bg-secondary text-muted-foreground rounded-2xl rounded-bl-none border border-border/60 px-4.5 py-3 text-sm flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          Sedang berpikir...
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Suggested Prompts */}
                  <div className="bg-secondary/20 border-t border-border/60 px-6 py-3 flex gap-2 flex-wrap">
                    {GUIDANCE_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => handleSendChat(prompt)}
                        className="text-xs font-bold text-primary-dark bg-primary/10 hover:bg-primary/25 border border-primary/20 px-3 py-1.5 rounded-full transition-colors cursor-pointer"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>

                  {/* Input Form */}
                  <div className="p-4 bg-card border-t border-border flex gap-3">
                    <input
                      type="text"
                      placeholder="Tanyakan tentang perawatan demensia, aktivitas, rutinitas..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
                      className="flex-1 bg-secondary/40 border border-input rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                    />
                    <button
                      onClick={() => handleSendChat()}
                      disabled={!chatInput.trim() || chatLoading}
                      className="bg-primary hover:bg-primary-dark disabled:bg-primary/50 text-white p-2.5 rounded-xl transition-colors cursor-pointer flex items-center justify-center"
                    >
                      <Send className="w-4.5 h-4.5" />
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Tab 5: Monthly Reports */}
              {activeTab === "reports" && (
                <motion.div
                  key="reports"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className="space-y-6"
                >
                  <h2 className="text-2xl font-bold font-serif-editorial text-foreground">Laporan Bulanan</h2>

                  {/* Generator laporan */}
                  <div className="bg-card border border-border/70 rounded-2xl p-6 shadow-sm">
                    <h3 className="font-bold text-base text-foreground mb-4">Buat Laporan dari Data Check-in</h3>
                    <div className="flex flex-wrap items-end gap-3">
                      <div className="flex flex-col gap-1">
                        <label className="text-xs font-bold text-muted-foreground">Pilih Bulan</label>
                        <input
                          type="month"
                          value={selectedBulan}
                          onChange={(e) => {
                            setSelectedBulan(e.target.value);
                            setGenerateError(null);
                            setGenerateSuccess(null);
                          }}
                          max={`${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, "0")}`}
                          className="bg-secondary/40 border border-input rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                        />
                      </div>
                      <button
                        onClick={async () => {
                          if (!selectedBulan) return;
                          const [tahun, bulan] = selectedBulan.split("-").map(Number);
                          setGenerateLoading(true);
                          setGenerateError(null);
                          setGenerateSuccess(null);
                          try {
                            const res = await caregiverApi.generateReport(tahun, bulan);
                            if (res.status === "tidak_ada_data") {
                              setGenerateError(res.pesan || "Tidak ada data sesi pada bulan tersebut.");
                            } else {
                              setGenerateSuccess(
                                res.dibuat_baru
                                  ? "Laporan berhasil dibuat."
                                  : "Laporan berhasil diperbarui."
                              );
                              const repRes = await caregiverApi.getReports();
                              setReports(repRes.reports || []);
                            }
                          } catch (err) {
                            if (isAxiosError(err)) {
                              setGenerateError(
                                err.response?.data?.detail || "Gagal membuat laporan. Silakan coba lagi."
                              );
                            } else {
                              setGenerateError("Terjadi kesalahan. Silakan coba lagi.");
                            }
                          } finally {
                            setGenerateLoading(false);
                          }
                        }}
                        disabled={generateLoading || !selectedBulan}
                        className="flex items-center gap-2 bg-primary hover:bg-primary-dark disabled:bg-primary/50 text-white font-bold px-5 py-2 rounded-xl text-sm transition-colors cursor-pointer"
                      >
                        {generateLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <FileText className="w-4 h-4" />
                        )}
                        {generateLoading ? "Memproses..." : "Buat Laporan"}
                      </button>
                    </div>

                    {generateError && (
                      <p className="mt-3 text-sm text-destructive font-medium">{generateError}</p>
                    )}
                    {generateSuccess && (
                      <p className="mt-3 text-sm text-primary-dark font-medium">{generateSuccess}</p>
                    )}
                  </div>

                  {/* Daftar laporan */}
                  <div className="space-y-4">
                    {reports.length === 0 ? (
                      <p className="text-muted-foreground text-sm font-medium">
                        Belum ada laporan. Tekan tombol di atas untuk membuat laporan dari data check-in.
                      </p>
                    ) : (
                      reports.map((r) => (
                        <ReportCard key={r.id} r={r} />
                      ))
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          )}
        </div>
      </main>
    </div>
  );
}

export default function CaregiverDashboardPage() {
  return (
    <ProtectedRoute allowedRoles={["caregiver"]}>
      <CaregiverDashboardContent />
    </ProtectedRoute>
  );
}