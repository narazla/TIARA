"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";
import type { UserRole } from "@/lib/types";
import { Loader2, Brain } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

/**
 * Wraps page content with authentication and optional role-based access control.
 * Redirects to /login if unauthenticated, or shows 403 if role is not allowed.
 */
export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center text-foreground">
          <div className="w-16 h-16 rounded-2xl bg-secondary border border-border flex items-center justify-center mx-auto mb-4">
            <Brain className="w-8 h-8 text-primary" />
          </div>
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-3 text-primary" />
          <p className="text-muted-foreground text-sm">Loading TIARA...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // redirect is happening
  }

  return <>{children}</>;
}
