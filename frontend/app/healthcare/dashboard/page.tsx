"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { isAxiosError } from "axios";
import { AlertTriangle, FileText, Loader2, LogOut, Users } from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { healthcareApi } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthContext";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";

interface PatientCard {
  id: string;
  full_name: string;
  age: number | null;
  latest_risk_score: number | null;
  latest_risk_level: string | null;
  last_checkin_at: string | null;
  days_since_last_checkin: number | null;
  unread_alerts: number;
  needs_attention: boolean;
}

interface TrendPoint {
  date: string;
  risk_score: number;
  risk_level: string;
}

interface AlertItem {
  id: string;
  severity: string;
  title: string;
  description: string;
  suggested_action: string;
  created_at: string;
  is_read: boolean;
}

interface ReportItem {
  id: string;
  title: string;
  report_month: string;
  checkin_count: number;
  avg_risk_score: number;
  created_at: string;
}

interface PatientSummary {
  patient: { id: string; full_name: string; age: number | null; gender: string | null };
  latest_session: {
    session_id: string;
    completed_at: string;
    risk_score: number;
    risk_level: string;
  } | null;
  trend_data: TrendPoint[];
  memory_consistency: number | null;
  memory_consistency_delta: number | null;
  avg_response_delay: number | null;
  avg_response_delay_delta: number | null;
  speech_hesitation_rate: number | null;
  speech_hesitation_rate_delta: number | null;
  checkin_count_30d: number;
  days_since_last_checkin: number | null;
  alerts: AlertItem[];
  reports: ReportItem[];
}

const RISK_LABEL: Record<string, string> = {
  high: "Tinggi",
  medium: "Sedang",
  low: "Rendah",
};

const SEVERITY_LABEL: Record<string, string> = {
  critical: "Kritis",
  warning: "Peringatan",
  info: "Info",
};

const severityStyle = (s: string): string =>
  s === "critical"
    ? "bg-destructive/15 text-destructive"
    : s === "warning"
    ? "bg-warning/15 text-amber-700"
    : "bg-primary/15 text-primary-dark";

const GENDER_LABEL: Record<string, string> = { M: "Laki-laki", F: "Perempuan" };

function RiskBadge({ level }: { level: string | null }) {
  if (level === null) {
    return (
      <span className="inline-flex items-center text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-muted/50 text-muted-foreground border border-border">
        Belum ada data
      </span>
    );
  }
  const cls =
    level === "high" ? "risk-badge-high" : level === "medium" ? "risk-badge-medium" : "risk-badge-low";
  return <span className={cls}>● Risiko {RISK_LABEL[level] ?? level}</span>;
}

function textCheckin(days: number | null): string {
  if (days === null) return "Belum ada check-in";
  if (days === 0) return "Check-in terakhir: hari ini";
  return `Check-in terakhir: ${days} hari lalu`;
}

function formatDelta(delta: number | null, unit: string): string {
  if (delta === null) return "";
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toLocaleString("id-ID")}${unit} dari pekan lalu`;
}

function HealthcareDashboardContent() {
  const { logout, user } = useAuth();

  const [patients, setPatients] = useState<PatientCard[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleError = (err: unknown, fallback: string) => {
    if (isAxiosError(err) && err.response?.status === 401) {
      logout();
      return;
    }
    console.error(fallback, err);
    setErrorMessage(fallback);
  };

  // Daftar pasien
  useEffect(() => {
    const loadPatients = async () => {
      try {
        const res = await healthcareApi.getPatients();
        const list: PatientCard[] = res.patients || [];
        setPatients(list);
        if (list.length > 0) setSelectedId(list[0].id);
      } catch (err) {
        handleError(err, "Daftar pasien tidak dapat dimuat. Silakan muat ulang halaman.");
      } finally {
        setLoadingList(false);
      }
    };
    loadPatients();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Ringkasan pasien terpilih
  useEffect(() => {
    if (!selectedId) return;
    let dibatalkan = false;
    const loadSummary = async () => {
      setLoadingDetail(true);
      setErrorMessage(null);
      try {
        const res: PatientSummary = await healthcareApi.getPatientSummary(selectedId);
        if (!dibatalkan) setSummary(res);
      } catch (err) {
        if (!dibatalkan) handleError(err, "Ringkasan pasien tidak dapat dimuat.");
      } finally {
        if (!dibatalkan) setLoadingDetail(false);
      }
    };
    loadSummary();
    return () => {
      dibatalkan = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const perluPerhatian = patients.filter((p) => p.needs_attention).length;

  return (
    <div className="h-screen bg-background text-foreground flex flex-col overflow-hidden">
      {/* Header */}
      <header className="h-20 min-h-20 bg-card border-b border-border flex items-center justify-between px-8">
        <div className="flex items-center gap-4">
          <img src="/Logo.png" alt="TIARA Logo" className="h-[40px] object-contain" />
          <div className="border-l border-border pl-4">
            <h1 className="font-bold text-base text-foreground font-serif-editorial">
              Portal Tenaga Kesehatan
            </h1>
            <p className="text-xs text-muted-foreground font-medium">
              Ringkasan longitudinal pasien yang terhubung
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right min-w-0">
            <p className="text-sm font-bold text-foreground truncate">{user?.full_name}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
          <button
            onClick={() => logout()}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-destructive hover:bg-destructive/5 transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            Keluar
          </button>
        </div>
      </header>

      <div className="flex-1 flex min-h-0">
        {/* Daftar pasien */}
        <aside className="w-80 flex-shrink-0 bg-card border-r border-border overflow-y-auto">
          <div className="p-5 border-b border-border">
            <h2 className="flex items-center gap-2 text-sm font-bold text-foreground">
              <Users className="w-4 h-4 text-primary-dark" />
              Daftar Pasien ({patients.length})
            </h2>
            {patients.length > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                {perluPerhatian > 0
                  ? `${perluPerhatian} pasien perlu perhatian`
                  : "Tidak ada pasien yang perlu perhatian khusus"}
              </p>
            )}
          </div>

          {loadingList ? (
            <div className="flex justify-center py-10">
              <Loader2 className="w-6 h-6 text-primary animate-spin" />
            </div>
          ) : patients.length === 0 ? (
            <p className="p-5 text-sm text-muted-foreground font-medium">
              Belum ada pasien yang terhubung dengan akun Anda.
            </p>
          ) : (
            <ul className="p-3 space-y-2">
              {patients.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => setSelectedId(p.id)}
                    className={`w-full text-left rounded-2xl border p-4 transition-colors cursor-pointer ${
                      selectedId === p.id
                        ? "border-primary bg-primary/5"
                        : "border-border/70 bg-card hover:bg-secondary/40"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-bold text-sm text-foreground truncate">{p.full_name}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {p.age !== null ? `${p.age} tahun` : "Usia belum tercatat"}
                        </p>
                      </div>
                      {p.unread_alerts > 0 && (
                        <span className="text-[10px] font-bold bg-destructive text-white rounded-full px-2 py-0.5">
                          {p.unread_alerts}
                        </span>
                      )}
                    </div>
                    <div className="mt-2.5 flex items-center justify-between gap-2">
                      <RiskBadge level={p.latest_risk_level} />
                      <span className="text-xs font-bold text-foreground">
                        {p.latest_risk_score !== null
                          ? `Skor ${p.latest_risk_score.toLocaleString("id-ID")}`
                          : ""}
                      </span>
                    </div>
                    <p
                      className={`text-xs mt-2 font-medium ${
                        p.days_since_last_checkin !== null && p.days_since_last_checkin >= 3
                          ? "text-amber-700"
                          : "text-muted-foreground"
                      }`}
                    >
                      {textCheckin(p.days_since_last_checkin)}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        {/* Detail pasien */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-8 max-w-5xl mx-auto w-full">
            {errorMessage && (
              <div className="mb-6 bg-destructive/10 border border-destructive/20 rounded-xl p-3 text-sm text-destructive font-medium">
                {errorMessage}
              </div>
            )}

            {!selectedId && !loadingList ? null : loadingDetail && !summary ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              </div>
            ) : summary ? (
              <motion.div
                key={summary.patient.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className={`space-y-8 transition-opacity ${loadingDetail ? "opacity-60" : "opacity-100"}`}
              >
                {/* Identitas */}
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center font-bold text-lg text-primary-dark">
                      {summary.patient.full_name[0]}
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold font-serif-editorial text-foreground">
                        {summary.patient.full_name}
                      </h2>
                      <p className="text-sm text-muted-foreground font-medium">
                        {[
                          summary.patient.age !== null ? `${summary.patient.age} tahun` : null,
                          summary.patient.gender ? GENDER_LABEL[summary.patient.gender] ?? null : null,
                        ]
                          .filter(Boolean)
                          .join(", ") || "Data demografi belum tercatat"}
                      </p>
                    </div>
                  </div>
                  <RiskBadge level={summary.latest_session?.risk_level ?? null} />
                </div>

                {/* Indikator */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
                  <div className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm">
                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Konsistensi Memori</p>
                    <p className="text-2xl font-bold font-serif-editorial text-foreground mt-2">
                      {summary.memory_consistency !== null
                        ? `${summary.memory_consistency.toLocaleString("id-ID")}%`
                        : "Belum ada data"}
                    </p>
                    <p className="text-xs text-muted-foreground font-semibold mt-1">
                      {formatDelta(summary.memory_consistency_delta, "%")}
                    </p>
                  </div>
                  <div className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm">
                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Jeda Respons</p>
                    <p className="text-2xl font-bold font-serif-editorial text-foreground mt-2">
                      {summary.avg_response_delay !== null
                        ? `${summary.avg_response_delay.toLocaleString("id-ID")} dtk`
                        : "Belum ada data"}
                    </p>
                    <p className="text-xs text-muted-foreground font-semibold mt-1">
                      {formatDelta(summary.avg_response_delay_delta, " dtk")}
                    </p>
                  </div>
                  <div className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm">
                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Keraguan Bicara</p>
                    <p className="text-2xl font-bold font-serif-editorial text-foreground mt-2">
                      {summary.speech_hesitation_rate !== null
                        ? `${summary.speech_hesitation_rate.toLocaleString("id-ID")} kali/menit`
                        : "Belum ada data"}
                    </p>
                    <p className="text-xs text-muted-foreground font-semibold mt-1">
                      {formatDelta(summary.speech_hesitation_rate_delta, " kali/menit")}
                    </p>
                  </div>
                  <div className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm">
                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Check-in 30 Hari</p>
                    <p className="text-2xl font-bold font-serif-editorial text-foreground mt-2">
                      {summary.checkin_count_30d} kali
                    </p>
                    <p className="text-xs text-muted-foreground font-semibold mt-1">
                      {textCheckin(summary.days_since_last_checkin)}
                    </p>
                  </div>
                </div>

                {/* Tren */}
                <div className="bg-card border border-border/70 rounded-[24px] p-6 shadow-sm">
                  <h3 className="text-lg font-bold font-serif-editorial text-foreground mb-1">
                    Skor Risiko Kognitif (30 Hari)
                  </h3>
                  <p className="text-xs text-muted-foreground mb-5">
                    Garis putus-putus menandai batas Sedang (4) dan Tinggi (7). Indikator informatif, bukan diagnosis.
                  </p>
                  <div className="h-64">
                    {summary.trend_data.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={summary.trend_data}>
                          <defs>
                            <linearGradient id="hcRisk" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.2} />
                              <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <XAxis
                            dataKey="date"
                            stroke="var(--color-text-muted)"
                            fontSize={11}
                            tickLine={false}
                            tickFormatter={(v: string) => `${v.slice(8, 10)}/${v.slice(5, 7)}`}
                          />
                          <YAxis domain={[0, 10]} stroke="var(--color-text-muted)" fontSize={11} tickLine={false} />
                          <Tooltip />
                          <ReferenceLine y={4} stroke="#b7791f" strokeDasharray="4 4" />
                          <ReferenceLine y={7} stroke="#c0564a" strokeDasharray="4 4" />
                          <Area
                            type="monotone"
                            dataKey="risk_score"
                            stroke="var(--color-primary)"
                            strokeWidth={2.5}
                            fillOpacity={1}
                            fill="url(#hcRisk)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-muted-foreground text-sm font-medium">
                        Belum ada sesi pemeriksaan dalam 30 hari terakhir.
                      </div>
                    )}
                  </div>
                </div>

                {/* Peringatan */}
                <div className="bg-card border border-border/70 rounded-[24px] p-6 shadow-sm">
                  <h3 className="text-lg font-bold font-serif-editorial text-foreground mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-terracotta" />
                    Peringatan
                  </h3>
                  {summary.alerts.length === 0 ? (
                    <p className="text-sm text-muted-foreground font-medium">Belum ada peringatan untuk pasien ini.</p>
                  ) : (
                    <div className="space-y-3.5">
                      {summary.alerts.map((a) => (
                        <div key={a.id} className="border border-border/60 rounded-xl p-4 bg-secondary/30">
                          <div className="flex justify-between items-start mb-1.5">
                            <span
                              className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${severityStyle(a.severity)}`}
                            >
                              {SEVERITY_LABEL[a.severity] ?? a.severity}
                            </span>
                            <span className="text-[11px] text-muted-foreground font-medium">
                              {new Date(a.created_at).toLocaleDateString("id-ID")}
                            </span>
                          </div>
                          <h4 className="font-bold text-sm text-foreground">{a.title}</h4>
                          <p className="text-xs text-muted-foreground mt-0.5 leading-normal">{a.description}</p>
                          {a.suggested_action && (
                            <p className="text-xs text-foreground mt-2 leading-normal">
                              <span className="font-bold text-primary-dark">Tindakan yang disarankan: </span>
                              {a.suggested_action}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Laporan */}
                <div className="bg-card border border-border/70 rounded-[24px] p-6 shadow-sm">
                  <h3 className="text-lg font-bold font-serif-editorial text-foreground mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary-dark" />
                    Laporan Bulanan
                  </h3>
                  {summary.reports.length === 0 ? (
                    <p className="text-sm text-muted-foreground font-medium">Belum ada laporan untuk pasien ini.</p>
                  ) : (
                    <div className="divide-y divide-border/60">
                      {summary.reports.map((r) => (
                        <div key={r.id} className="py-3 flex items-center justify-between gap-4">
                          <p className="font-bold text-sm text-foreground">{r.title}</p>
                          <p className="text-xs text-muted-foreground">
                            {r.checkin_count} check-in. Rata-rata Skor Risiko: {r.avg_risk_score.toFixed(1)}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <p className="text-xs text-muted-foreground leading-relaxed pb-4">
                  TIARA bukan alat diagnosis medis. Seluruh angka pada halaman ini adalah indikator informatif untuk
                  membantu pemantauan. Keputusan klinis tetap berada pada tenaga kesehatan.
                </p>
              </motion.div>
            ) : null}
          </div>
        </main>
      </div>
    </div>
  );
}

export default function HealthcareDashboardPage() {
  return (
    <ProtectedRoute allowedRoles={["healthcare"]}>
      <HealthcareDashboardContent />
    </ProtectedRoute>
  );
}
