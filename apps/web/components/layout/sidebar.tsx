"use client";

import { useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  ShoppingBag,
  BarChart3,
  Bell,
  Heart,
  Settings,
  LogOut,
  TrendingUp,
  Shield,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";

const navItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Deals",
    href: "/dashboard/deals",
    icon: ShoppingBag,
  },
  {
    label: "Analytics",
    href: "/dashboard/analytics",
    icon: BarChart3,
  },
  {
    label: "Alertes",
    href: "/dashboard/alerts",
    icon: Bell,
  },
  {
    label: "Favoris",
    href: "/dashboard/favorites",
    icon: Heart,
  },
  {
    label: "Parametres",
    href: "/dashboard/settings",
    icon: Settings,
  },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, user } = useAuth();

  // Check if user is admin based on plan (PRO/AGENCY have admin access) or admin email
  const isAdmin = user?.plan?.toLowerCase() === "pro" || user?.plan?.toLowerCase() === "agency" || user?.email === "admin@sharkted.fr";

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  // Handle ESC key to close sidebar on mobile
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && onClose) {
        onClose();
      }
    },
    [onClose]
  );

  // Add ESC listener when sidebar is open on mobile
  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      // Prevent body scroll when drawer is open
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen, handleKeyDown]);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    if (onClose) {
      onClose();
    }
  }, [pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  // Sidebar content (shared between desktop and mobile)
  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="p-6 border-b border-gray-800 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2">
          <TrendingUp className="text-primary-400" size={28} />
          <span className="text-xl font-bold">Sharkted</span>
        </Link>
        {/* Close button - only visible on mobile */}
        {onClose && (
          <button
            onClick={onClose}
            className="lg:hidden p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="Fermer le menu"
          >
            <X size={20} />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1" role="navigation" aria-label="Menu principal">
        {navItems.map((item) => {
          // Dashboard should only be active on exact match
          const isActive = item.href === "/dashboard"
            ? pathname === "/dashboard"
            : pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                isActive
                  ? "bg-primary-600 text-white"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}

        {/* Admin Link - Only visible for admins */}
        {isAdmin && (
          <Link
            href="/admin"
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors mt-4 border-t border-gray-800 pt-4",
              pathname === "/admin"
                ? "bg-red-600 text-white"
                : "text-red-400 hover:bg-gray-800 hover:text-red-300"
            )}
            aria-current={pathname === "/admin" ? "page" : undefined}
          >
            <Shield size={20} />
            <span>Administration</span>
          </Link>
        )}
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center gap-3 mb-4">
          <div className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0",
            isAdmin ? "bg-red-600" : "bg-primary-600"
          )}>
            {user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">
              {user?.full_name || user?.username || user?.email || "Utilisateur"}
            </p>
            <p className="text-xs text-gray-400 capitalize">
              {isAdmin ? "Admin" : user?.plan || "free"}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          <LogOut size={18} />
          <span>Deconnexion</span>
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop Sidebar - Fixed, always visible on lg+ */}
      <aside
        className="hidden lg:flex w-64 bg-gray-900 text-white flex-col h-screen fixed left-0 top-0 z-40"
        aria-label="Navigation principale"
      >
        {sidebarContent}
      </aside>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40 transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Mobile Sidebar Drawer */}
      <aside
        className={cn(
          "lg:hidden fixed inset-y-0 left-0 w-64 bg-gray-900 text-white flex flex-col z-50 transform transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
        aria-label="Navigation principale"
        aria-hidden={!isOpen}
        role="dialog"
        aria-modal="true"
      >
        {sidebarContent}
      </aside>
    </>
  );
}
