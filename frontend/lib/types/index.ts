// TypeScript types matching backend schemas

export type UserRole = "elderly" | "caregiver" | "healthcare" | "admin";
export type RiskLevel = "low" | "medium" | "high";
export type AlertSeverity = "info" | "warning" | "critical";
export type SessionStatus = "in_progress" | "completed" | "abandoned";
export type ProcessingStatus = "pending" | "processing" | "completed" | "failed";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ElderlyHomeData {
  user: {
    full_name: string;
    greeting: string;
  };
  todays_checkin: {
    completed: boolean;
    session_id: string | null;
    completed_at: string | null;
  };
  streak_days: number;
}

export interface CheckinQuestion {
  id: string;
  category: string;
  question_text: string;
  order_index: number;
}

export interface CheckinSession {
  session_id: string;
  questions: CheckinQuestion[];
  started_at: string;
}

export interface RiskScore {
  risk_score: number;
  risk_level: RiskLevel;
  voice_component: number | null;
  language_component: number | null;
  facial_component: number | null;
  memory_component: number | null;
  summary: string | null;
  main_indicators: string[] | null;
}

export interface Alert {
  id: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  suggested_action: string | null;
  created_at: string;
  is_read: boolean;
}

export interface CareRecommendation {
  id: string;
  category: string;
  title: string;
  description: string;
  priority: number;
}

export interface TrendDataPoint {
  date: string;
  risk_score: number;
  risk_level: RiskLevel;
}

export interface CaregiverDashboard {
  patient: {
    id: string;
    full_name: string;
    age: number | null;
  };
  latest_session: {
    session_id: string;
    completed_at: string;
    risk_score: number;
    risk_level: RiskLevel;
  } | null;
  trend_data: TrendDataPoint[];
  memory_consistency: number | null;
  avg_response_delay: number | null;
  speech_hesitation_rate: number | null;
  unread_alerts: number;
}

export interface GuidanceMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Report {
  id: string;
  title: string;
  report_month: string;
  checkin_count: number | null;
  avg_risk_score: number | null;
  created_at: string;
}

export interface ApiError {
  detail: string;
  code?: string;
}
