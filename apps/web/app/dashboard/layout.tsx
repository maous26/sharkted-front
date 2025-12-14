"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Menu } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, hasHydrated } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Redirect to login if not authenticated (after hydration)
  useEffect(() => {
    if (hasHydrated && !isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, hasHydrated, router]);

  // Show loading while hydrating auth state
  if (!hasHydrated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  // Don't render dashboard if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar - handles both desktop (fixed) and mobile (drawer) */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Mobile Header with Menu Button */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-30 bg-gray-900 text-white px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          aria-label="Ouvrir le menu"
          aria-expanded={sidebarOpen}
          aria-controls="mobile-sidebar"
        >
          <Menu size={24} />
        </button>
        <span className="text-lg font-semibold">Sharkted</span>
      </div>

      {/* Main Content */}
      {/* Desktop: ml-64 for fixed sidebar | Mobile: pt-14 for fixed header, no ml */}
      <main className="lg:ml-64 pt-14 lg:pt-0">
        {children}
      </main>
    </div>
  );
}
