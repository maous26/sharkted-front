"use client";

import { useState, useRef, useEffect } from "react";
import { Bell, Check, ExternalLink, X, Zap, TrendingUp, AlertCircle } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { alertsApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";

interface Notification {
  id: string;
  deal_id: string;
  deal_title: string;
  deal_brand?: string;
  deal_price?: number;
  flip_score?: number;
  margin_pct?: number;
  sent_at: string;
  clicked: boolean;
  channel: string;
  deal_url?: string;
}

export function NotificationDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Fetch notifications
  const { data: notifications = [], isLoading } = useQuery<Notification[]>({
    queryKey: ["notifications"],
    queryFn: async () => {
      try {
        const { data } = await alertsApi.list({ limit: 10 });
        // API returns { items: [...], total, page, per_page }
        return data?.items || [];
      } catch {
        // Return empty array if not authenticated or error
        return [];
      }
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: false, // Don't retry on auth errors
  });

  // Mark as clicked mutation
  const markClickedMutation = useMutation({
    mutationFn: (id: string) => alertsApi.markClicked(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = notifications?.filter((n) => !n.clicked).length || 0;

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.clicked) {
      markClickedMutation.mutate(notification.id);
    }
    if (notification.deal_url) {
      window.open(notification.deal_url, "_blank");
    }
  };

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-400";
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    return "text-orange-500";
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="ghost"
        size="sm"
        className="relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs text-white flex items-center justify-center font-medium animate-pulse">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </Button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden animate-fade-in-down">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50">
            <div className="flex items-center gap-2">
              <Bell size={18} className="text-gray-600" />
              <h3 className="font-semibold text-gray-900">Notifications</h3>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 bg-red-100 text-red-600 text-xs font-medium rounded-full">
                  {unreadCount} nouvelles
                </span>
              )}
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <X size={16} className="text-gray-500" />
            </button>
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex gap-3 animate-pulse">
                    <div className="w-10 h-10 bg-gray-200 rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : notifications && notifications.length > 0 ? (
              <div>
                {notifications.map((notification) => (
                  <button
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={cn(
                      "w-full flex items-start gap-3 p-4 hover:bg-gray-50 transition-colors text-left border-b border-gray-50 last:border-0",
                      !notification.clicked && "bg-blue-50/50"
                    )}
                  >
                    {/* Icon */}
                    <div
                      className={cn(
                        "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0",
                        notification.flip_score && notification.flip_score >= 70
                          ? "bg-green-100"
                          : "bg-gray-100"
                      )}
                    >
                      {notification.flip_score && notification.flip_score >= 70 ? (
                        <Zap size={18} className="text-green-600" />
                      ) : (
                        <TrendingUp size={18} className="text-gray-600" />
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p
                          className={cn(
                            "text-sm font-medium truncate",
                            notification.clicked ? "text-gray-600" : "text-gray-900"
                          )}
                        >
                          {notification.deal_title}
                        </p>
                        {!notification.clicked && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1.5" />
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {notification.deal_brand && (
                          <span className="text-xs text-gray-500 uppercase">
                            {notification.deal_brand}
                          </span>
                        )}
                        {notification.flip_score && (
                          <span
                            className={cn(
                              "text-xs font-semibold",
                              getScoreColor(notification.flip_score)
                            )}
                          >
                            Score: {notification.flip_score}
                          </span>
                        )}
                        {notification.margin_pct && (
                          <span className="text-xs text-green-600 font-medium">
                            +{notification.margin_pct.toFixed(0)}%
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        {formatDistanceToNow(new Date(notification.sent_at), {
                          addSuffix: true,
                          locale: fr,
                        })}
                      </p>
                    </div>

                    {/* External link icon */}
                    {notification.deal_url && (
                      <ExternalLink size={14} className="text-gray-400 flex-shrink-0 mt-1" />
                    )}
                  </button>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center">
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Bell size={24} className="text-gray-400" />
                </div>
                <p className="text-sm text-gray-500">Aucune notification</p>
                <p className="text-xs text-gray-400 mt-1">
                  Les alertes de deals apparaitront ici
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications && notifications.length > 0 && (
            <div className="px-4 py-3 border-t border-gray-100 bg-gray-50">
              <a
                href="/dashboard/alerts"
                className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center justify-center gap-1"
              >
                Voir toutes les alertes
                <ExternalLink size={14} />
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
