import axios, { AxiosInstance } from "axios";

const API_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://tiara-botchain-production.up.railway.app");

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Interceptor untuk otomatis tempel token
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token =
      localStorage.getItem("token") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("tiara_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  if (typeof window !== "undefined") {
    const dashboardToken = localStorage.getItem("tiara_caregiver_token");
    if (dashboardToken) {
      config.headers["X-Dashboard-Token"] = dashboardToken;
    }
  }
  return config;
});

// Token PIN habis atau tidak ada: kembali ke halaman PIN
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      typeof window !== "undefined" &&
      axios.isAxiosError(error) &&
      error.response?.status === 403 &&
      error.response?.data?.detail === "PIN_DIPERLUKAN"
    ) {
      localStorage.removeItem("tiara_caregiver_token");
      if (!window.location.pathname.startsWith("/caregiver/pin")) {
        window.location.href = "/caregiver/pin";
      }
    }
    return Promise.reject(error);
  }
);

export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    return (
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Terjadi kesalahan yang tidak terduga"
    );
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Terjadi kesalahan yang tidak terduga";
};