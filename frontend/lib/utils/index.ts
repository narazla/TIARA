import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { RiskLevel, AlertSeverity } from "@/lib/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getRiskColor(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    low: "text-emerald-600",
    medium: "text-amber-600",
    high: "text-rose-600",
  };
  return colors[level] || "text-gray-600";
}

export function getRiskBgColor(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    low: "bg-emerald-50 text-emerald-700 border-emerald-200",
    medium: "bg-amber-50 text-amber-700 border-amber-200",
    high: "bg-rose-50 text-rose-700 border-rose-200",
  };
  return colors[level] || "bg-gray-50 text-gray-700 border-gray-200";
}

export function getAlertColor(severity: AlertSeverity): string {
  const colors: Record<AlertSeverity, string> = {
    info: "bg-blue-50 text-blue-700 border-blue-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    critical: "bg-rose-50 text-rose-700 border-rose-200",
  };
  return colors[severity] || "bg-gray-50 text-gray-700";
}

export function formatRiskLevel(level: RiskLevel): string {
  const labels: Record<RiskLevel, string> = {
    low: "Low",
    medium: "Medium",
    high: "High",
  };
  return labels[level] || level;
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function categoryLabel(category: string): string {
  const labels: Record<string, string> = {
    orientation: "Orientation",
    memory_recall: "Memory Recall",
    long_term_memory: "Long-Term Memory",
    emotional_wellbeing: "Emotional Wellbeing",
  };
  return labels[category] || category;
}
