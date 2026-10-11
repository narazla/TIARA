import { apiClient } from "./client";

// --- AUTH API ---
export const authApi = {
  login: async (credentials: any) => {
    const response = await apiClient.post("/api/v1/auth/login", credentials);
    return response.data;
  },
  register: async (userData: any) => {
    const response = await apiClient.post("/api/v1/auth/register", userData);
    return response.data;
  },
  getMe: async () => {
    const response = await apiClient.get("/api/v1/auth/me");
    return response.data;
  },
  logout: async () => {
    const response = await apiClient.post("/api/v1/auth/logout");
    return response.data;
  },
};

// --- ELDERLY API ---
export const elderlyApi = {
  getHome: async () => {
    const response = await apiClient.get("/api/v1/elderly/home");
    return response.data;
  },
  getProfile: async () => {
    const response = await apiClient.get("/api/v1/elderly/profile");
    return response.data;
  },
};

// --- CAREGIVER API ---
export const caregiverApi = {
  verifyPin: async (pin: string) => {
    const response = await apiClient.post("/api/v1/caregiver/verify-pin", { pin });
    return response.data;
  },
  getDashboard: async () => {
    const response = await apiClient.get("/api/v1/caregiver/dashboard");
    return response.data;
  },
  getAlerts: async () => {
    const response = await apiClient.get("/api/v1/caregiver/alerts");
    return response.data;
  },
  getRecommendations: async () => {
    const response = await apiClient.get("/api/v1/caregiver/recommendations");
    return response.data;
  },
  getReports: async () => {
    const response = await apiClient.get("/api/v1/caregiver/reports");
    return response.data;
  },
};

// --- DEMENTIA GUIDANCE (RAG AI) API ---
export const guidanceApi = {
  ask: async (message: string, sessionContextId?: string) => {
    const response = await apiClient.post("/api/v1/caregiver/guidance/ask", {
      question: message,
      session_context_id: sessionContextId,
    });
    return response.data;
  },
};

// --- CHECK-IN API ---
export const checkinApi = {
  submitCheckIn: async (data: any) => {
    const response = await apiClient.post("/api/v1/elderly/check-in", data);
    return response.data;
  },
};