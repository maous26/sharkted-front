"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  RefreshCw,
  Users,
  Crown,
  Star,
  User,
  Shield,
  Mail,
  Trash2,
  Check,
  X,
  Search,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { adminApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface UserData {
  id: number;
  email: string;
  plan: string;
  tier: string;
  is_admin: boolean;
}

const PLAN_OPTIONS = [
  { value: "freemium", label: "Freemium", color: "bg-gray-100 text-gray-700", icon: User },
  { value: "basic", label: "Basic", color: "bg-blue-100 text-blue-700", icon: Star },
  { value: "premium", label: "Premium", color: "bg-purple-100 text-purple-700", icon: Crown },
  { value: "pro", label: "Pro", color: "bg-orange-100 text-orange-700", icon: Crown },
  { value: "owner", label: "Owner", color: "bg-red-100 text-red-700", icon: Shield },
];

function getPlanConfig(plan: string) {
  const planLower = plan.toLowerCase();
  return PLAN_OPTIONS.find(p => p.value === planLower) || PLAN_OPTIONS[0];
}

export function UserManager() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [editingUser, setEditingUser] = useState<number | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<string>("");
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  // Fetch users
  const { data: users, isLoading, refetch } = useQuery<UserData[]>({
    queryKey: ["admin", "users"],
    queryFn: async () => {
      const { data } = await adminApi.users();
      return data;
    },
  });

  // Update plan mutation
  const updatePlanMutation = useMutation({
    mutationFn: async ({ userId, plan }: { userId: number; plan: string }) => {
      return adminApi.updateUserPlan(userId, plan);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
      setEditingUser(null);
      setSelectedPlan("");
    },
  });

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: async (userId: number) => {
      return adminApi.deleteUser(userId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
      setConfirmDelete(null);
    },
  });

  // Filter users
  const filteredUsers = users?.filter(user =>
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  // Stats
  const stats = {
    total: users?.length || 0,
    premium: users?.filter(u => ["premium", "pro", "agency", "owner"].includes(u.plan.toLowerCase())).length || 0,
    basic: users?.filter(u => u.plan.toLowerCase() === "basic").length || 0,
    freemium: users?.filter(u => !["premium", "pro", "agency", "owner", "basic"].includes(u.plan.toLowerCase())).length || 0,
  };

  const handleStartEdit = (user: UserData) => {
    setEditingUser(user.id);
    setSelectedPlan(user.plan.toLowerCase());
  };

  const handleSavePlan = (userId: number) => {
    if (selectedPlan) {
      updatePlanMutation.mutate({ userId, plan: selectedPlan });
    }
  };

  const handleCancelEdit = () => {
    setEditingUser(null);
    setSelectedPlan("");
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Users size={20} className="text-gray-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total</p>
                <p className="text-xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Crown size={20} className="text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Premium</p>
                <p className="text-xl font-bold text-purple-600">{stats.premium}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Star size={20} className="text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Basic</p>
                <p className="text-xl font-bold text-blue-600">{stats.basic}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-100 rounded-lg">
                <User size={20} className="text-gray-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Freemium</p>
                <p className="text-xl font-bold">{stats.freemium}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Users List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Users size={20} />
            Gestion des Utilisateurs
          </CardTitle>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
          </Button>
        </CardHeader>
        <CardContent>
          {/* Search */}
          <div className="relative mb-4">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Rechercher par email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Users Table */}
          {isLoading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="animate-spin text-gray-400" />
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Users size={48} className="mx-auto mb-4 opacity-50" />
              <p>Aucun utilisateur trouve</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">Email</th>
                    <th className="pb-3 font-medium">Plan</th>
                    <th className="pb-3 font-medium">Admin</th>
                    <th className="pb-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => {
                    const planConfig = getPlanConfig(user.plan);
                    const PlanIcon = planConfig.icon;
                    const isEditing = editingUser === user.id;
                    const isDeleting = confirmDelete === user.id;

                    return (
                      <tr key={user.id} className="border-b last:border-0 hover:bg-gray-50">
                        {/* Email */}
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <Mail size={14} className="text-gray-400" />
                            <span className="font-medium">{user.email}</span>
                          </div>
                        </td>

                        {/* Plan */}
                        <td className="py-3">
                          {isEditing ? (
                            <select
                              value={selectedPlan}
                              onChange={(e) => setSelectedPlan(e.target.value)}
                              className="px-2 py-1 border rounded text-sm"
                            >
                              {PLAN_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <span className={cn(
                              "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium",
                              planConfig.color
                            )}>
                              <PlanIcon size={12} />
                              {planConfig.label}
                            </span>
                          )}
                        </td>

                        {/* Admin */}
                        <td className="py-3">
                          {user.is_admin ? (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                              <Shield size={12} />
                              Admin
                            </span>
                          ) : (
                            <span className="text-gray-400 text-sm">-</span>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="py-3">
                          <div className="flex items-center justify-end gap-2">
                            {isEditing ? (
                              <>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleSavePlan(user.id)}
                                  disabled={updatePlanMutation.isPending}
                                  className="text-green-600 hover:bg-green-50"
                                >
                                  {updatePlanMutation.isPending ? (
                                    <RefreshCw size={14} className="animate-spin" />
                                  ) : (
                                    <Check size={14} />
                                  )}
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={handleCancelEdit}
                                  className="text-gray-600 hover:bg-gray-100"
                                >
                                  <X size={14} />
                                </Button>
                              </>
                            ) : isDeleting ? (
                              <>
                                <span className="text-xs text-red-600 mr-2">Confirmer ?</span>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => deleteUserMutation.mutate(user.id)}
                                  disabled={deleteUserMutation.isPending}
                                  className="text-red-600 hover:bg-red-50"
                                >
                                  {deleteUserMutation.isPending ? (
                                    <RefreshCw size={14} className="animate-spin" />
                                  ) : (
                                    <Check size={14} />
                                  )}
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setConfirmDelete(null)}
                                  className="text-gray-600 hover:bg-gray-100"
                                >
                                  <X size={14} />
                                </Button>
                              </>
                            ) : (
                              <>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleStartEdit(user)}
                                  className="text-xs"
                                >
                                  Changer plan
                                </Button>
                                {!user.is_admin && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setConfirmDelete(user.id)}
                                    className="text-red-500 hover:bg-red-50"
                                  >
                                    <Trash2 size={14} />
                                  </Button>
                                )}
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
