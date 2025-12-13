"use client";

import { useState } from "react";
import { Save, Bell, User, Shield, Info, TrendingUp, Clock, BarChart3, AlertTriangle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const [saving, setSaving] = useState(false);

  const [profileData, setProfileData] = useState({
    name: user?.name || "",
  });

  const [alertData, setAlertData] = useState({
    email_alerts: user?.email_alerts ?? true,
    alert_threshold: user?.alert_threshold || 70,
  });

  const [preferencesData, setPreferencesData] = useState({
    min_margin: user?.preferences?.min_margin || 20,
    categories: user?.preferences?.categories?.join(", ") || "sneakers, textile",
    sizes: user?.preferences?.sizes?.join(", ") || "42, 43, M, L",
    risk_profile: user?.preferences?.risk_profile || "balanced",
  });

  const handleSaveProfile = async () => {
    setSaving(true);
    // TODO: Call API
    setTimeout(() => {
      updateUser(profileData);
      setSaving(false);
    }, 1000);
  };

  const handleSaveAlerts = async () => {
    setSaving(true);
    // TODO: Call API
    setTimeout(() => {
      updateUser(alertData);
      setSaving(false);
    }, 1000);
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    // TODO: Call API
    setTimeout(() => {
      setSaving(false);
    }, 1000);
  };

  return (
    <div>
      <Header
        title="Paramètres"
        subtitle="Configurez votre compte et vos préférences"
      />

      <div className="p-8 max-w-3xl">
        {/* FlipScore Explanation */}
        <Card className="mb-6 border-primary-200 bg-gradient-to-br from-primary-50 to-white">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                <Info className="text-primary-600" size={20} />
              </div>
              <CardTitle>Comprendre le FlipScore</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              Le <strong>FlipScore</strong> est notre indicateur de 0 a 100 qui mesure le potentiel de revente d'un deal. Plus le score est eleve, plus l'opportunite est interessante.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-white rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="text-green-500" size={18} />
                  <span className="font-medium text-gray-900">Marge potentielle</span>
                </div>
                <p className="text-sm text-gray-500">
                  Difference entre le prix d'achat et le prix de revente estime sur Vinted (40% du score)
                </p>
              </div>

              <div className="p-4 bg-white rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <BarChart3 className="text-blue-500" size={18} />
                  <span className="font-medium text-gray-900">Liquidite</span>
                </div>
                <p className="text-sm text-gray-500">
                  Nombre d'articles similaires vendus sur Vinted - plus il y en a, plus c'est facile a revendre (30% du score)
                </p>
              </div>

              <div className="p-4 bg-white rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="text-orange-500" size={18} />
                  <span className="font-medium text-gray-900">Popularite</span>
                </div>
                <p className="text-sm text-gray-500">
                  Demande pour cette marque/modele basee sur les tendances actuelles (30% du score)
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Interpretation du score :</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-red-50">
                  <div className="w-12 h-12 min-w-12 rounded-full bg-red-500 flex items-center justify-center text-white text-xs font-bold">
                    0-40
                  </div>
                  <div>
                    <p className="font-medium text-red-700">A eviter</p>
                    <p className="text-xs text-red-600">Marge trop faible ou revente difficile</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-yellow-50">
                  <div className="w-12 h-12 min-w-12 rounded-full bg-yellow-500 flex items-center justify-center text-white text-xs font-bold">
                    40-60
                  </div>
                  <div>
                    <p className="font-medium text-yellow-700">Moyen</p>
                    <p className="text-xs text-yellow-600">Opportunite moderee, a etudier</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-green-50">
                  <div className="w-12 h-12 min-w-12 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold">
                    60-80
                  </div>
                  <div>
                    <p className="font-medium text-green-700">Bon deal</p>
                    <p className="text-xs text-green-600">Bonne marge avec revente probable</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-primary-50">
                  <div className="w-12 h-12 min-w-12 rounded-full bg-primary-600 flex items-center justify-center text-white text-xs font-bold">
                    80+
                  </div>
                  <div>
                    <p className="font-medium text-primary-700">Excellent</p>
                    <p className="text-xs text-primary-600">Opportunite rare, agissez vite!</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
              <AlertTriangle className="text-amber-500 flex-shrink-0 mt-0.5" size={18} />
              <p className="text-sm text-amber-700">
                <strong>Conseil :</strong> Commencez avec un seuil d'alerte a 70+ pour recevoir uniquement les meilleures opportunites. Ajustez ensuite selon votre experience et votre capacite a traiter les deals.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Profile */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                <User className="text-gray-600" size={20} />
              </div>
              <CardTitle>Profil</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Email"
              value={user?.email || ""}
              disabled
            />
            <Input
              label="Nom"
              value={profileData.name}
              onChange={(e) =>
                setProfileData({ ...profileData, name: e.target.value })
              }
            />
            <Button onClick={handleSaveProfile} disabled={saving}>
              <Save size={16} className="mr-2" />
              Enregistrer
            </Button>
          </CardContent>
        </Card>

        {/* Alerts */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <Bell className="text-blue-600" size={20} />
              </div>
              <CardTitle>Alertes</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Score minimum pour alerte
              </label>
              <p className="text-xs text-gray-500 mb-2">
                Vous serez alerte uniquement pour les deals avec un score superieur a cette valeur
              </p>
              <input
                type="range"
                min={0}
                max={100}
                value={alertData.alert_threshold}
                onChange={(e) =>
                  setAlertData({ ...alertData, alert_threshold: Number(e.target.value) })
                }
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500">
                <span>0</span>
                <span className="font-medium text-primary-600">
                  {alertData.alert_threshold}/100
                </span>
                <span>100</span>
              </div>
            </div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={alertData.email_alerts}
                onChange={(e) =>
                  setAlertData({ ...alertData, email_alerts: e.target.checked })
                }
                className="rounded border-gray-300 text-primary-600"
              />
              <span className="text-sm">Recevoir les alertes par email</span>
            </label>
            <Button onClick={handleSaveAlerts} disabled={saving}>
              <Save size={16} className="mr-2" />
              Enregistrer
            </Button>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                <Shield className="text-green-600" size={20} />
              </div>
              <CardTitle>Préférences de recherche</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Marge minimum (%)"
              type="number"
              value={preferencesData.min_margin}
              onChange={(e) =>
                setPreferencesData({
                  ...preferencesData,
                  min_margin: Number(e.target.value),
                })
              }
            />
            <Input
              label="Catégories favorites"
              placeholder="sneakers, textile, accessoires"
              value={preferencesData.categories}
              onChange={(e) =>
                setPreferencesData({ ...preferencesData, categories: e.target.value })
              }
            />
            <Input
              label="Tailles préférées"
              placeholder="42, 43, M, L"
              value={preferencesData.sizes}
              onChange={(e) =>
                setPreferencesData({ ...preferencesData, sizes: e.target.value })
              }
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Profil de risque
              </label>
              <select
                value={preferencesData.risk_profile}
                onChange={(e) =>
                  setPreferencesData({ ...preferencesData, risk_profile: e.target.value })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="conservative">Conservateur (marge élevée, faible risque)</option>
                <option value="balanced">Équilibré</option>
                <option value="aggressive">Agressif (plus de deals, risque modéré)</option>
              </select>
            </div>
            <Button onClick={handleSavePreferences} disabled={saving}>
              <Save size={16} className="mr-2" />
              Enregistrer
            </Button>
          </CardContent>
        </Card>

        {/* Subscription */}
        <Card>
          <CardHeader>
            <CardTitle>Abonnement</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium">Plan actuel: {user?.plan || "Free"}</p>
                <p className="text-sm text-gray-500">
                  {user?.plan === "free"
                    ? "Passez à Pro pour débloquer toutes les fonctionnalités"
                    : "Merci pour votre soutien!"}
                </p>
              </div>
              {user?.plan === "free" && (
                <Button>Passer à Pro</Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
