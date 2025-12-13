"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ShoppingBag,
  BarChart3,
  Bell,
  Settings,
  LogOut,
  TrendingUp,
  Shield,
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
    label: "Parametres",
    href: "/dashboard/settings",
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();

  // Check if user is admin based on plan (PRO/AGENCY have admin access)
  const isAdmin = user?.plan?.toLowerCase() === "pro" || user?.plan?.toLowerCase() === "agency";

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-screen fixed left-0 top-0">
      {/* Logo */}
      <div className="p-6 border-b border-gray-800">
        <Link href="/dashboard" className="flex items-center gap-2">
          <TrendingUp className="text-primary-400" size={28} />
          <span className="text-xl font-bold">FlipRadar</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
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
            "w-10 h-10 rounded-full flex items-center justify-center",
            isAdmin ? "bg-red-600" : "bg-primary-600"
          )}>
            {user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">
              {user?.full_name || user?.username || user?.email}
            </p>
            <p className="text-xs text-gray-400 capitalize">
              {isAdmin ? "Admin" : user?.plan || "free"}
            </p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 w-full px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          <LogOut size={18} />
          <span>Deconnexion</span>
        </button>
      </div>
    </aside>
  );
}
