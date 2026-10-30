import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/AuthContext";
import Footer from "@/components/shared/Footer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TIARA — Platform Perawatan Kognitif Berbasis AI",
  description:
    "TIARA dirancang untuk membantu keluarga memantau perubahan kognitif melalui check-in harian, catatan longitudinal, dan panduan demensia untuk caregiver. Bukan alat diagnosis medis.",
  keywords: [
    "skrining kognitif",
    "dukungan caregiver",
    "kesadaran demensia",
    "perawatan lansia",
    "pemantauan memori",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id" className="scroll-smooth">
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
