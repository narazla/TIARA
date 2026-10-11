import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/AuthContext";
import Footer from "@/components/shared/Footer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TIARA — AI-Powered Cognitive Care Platform",
  description:
    "TIARA helps families notice early cognitive changes through AI-guided daily check-ins, voice and language analysis, and caregiver support. Not a medical diagnosis tool.",
  keywords: [
    "cognitive screening",
    "caregiver support",
    "dementia awareness",
    "elderly care",
    "memory monitoring",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
      </head>
      <body className={inter.className}>
        <AuthProvider>
          {children}
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
