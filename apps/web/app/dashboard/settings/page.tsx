"use client";

import { useState } from "react";
import { Save, Bell, User, Info, TrendingUp, Tag, Award, AlertTriangle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const [saving, setSaving] = useState(false);

  const [profileData, setProfileData] = useState({
    name: user?.full_name || user?.username || "",
  });

  const [alertData, setAlertData] = useState({
    email_alerts: user?.email_alerts ?? true,
    alert_threshold: user?.alert_threshold || 70,
  });

  const handleSaveProfile = async () => {
    setSaving(true);
    // TODO: Call API
    setTimeout(() => {
      updateUser({ full_name: profileData.name });
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

  return (
    <div>
      <Header
        title="Parametres"
        subtitle="Configurez votre compte et vos preferences"
      />

      <div className="p-8 max-w-3xl">
        {/* SharkScore Explanation */}
        <Card className="mb-6 border-primary-200 bg-gradient-to-br from-primary-50 to-white">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                <Info className="text-primary-600" size={20} />
              </div>
              <CardTitle>Comprendre le SharkScore</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              Le <strong>SharkScore</strong> est notre indicateur de 0 a 100 qui evalue le potentiel de profit d'un deal. Il est calcule automatiquement a partir de plusieurs criteres.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="p-4 bg-white rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <Tag className="text-green-500" size={18} />
                  <span className="font-medium text-gray-900">Remise (30%)</span>
                </div>
                <p className="text-sm text-gray-500">
                  Pourcentage de reduction par rapport au prix original. Plus la remise est importante, plus le score augmente.
                </p>
              </div>

              <div className="p-4 bg-white rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <Award className="text-blue-500" size={18} />
                  <span className="font-medium text-gray-900">Marque (25%)</span>
                </div>
                <p className="text-sm text-gray-500">
                  Notoriete et facilite de revente. Tier S (Nike, Jordan), Tier A (Adidas, New Balance), Tier B (Puma, Reebok).
                </p>
              </div>

              <div className="p-4 bg-white rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="text-orange-500" size={18} />
                  <span className="font-medium text-gray-900">Contexte (20%)</span>
                </div>
                <p className="text-sm text-gray-500">
                  Tailles disponibles (39-45 ideales), couleurs (noir/blanc = safe), et urgence promo.
                </p>
              </div>

              <div className="p-4 bg-white rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="text-purple-500" size={18} />
                  <span className="font-medium text-gray-900">Marge (25%)</span>
                </div>
                <p className="text-sm text-gray-500">
                  Profit potentiel apres revente sur Vinted. Calcule avec les frais (13%) et l'envoi (~5€).
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Interpretation du score :</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-red-50">
                  <div className="w-12 h-12 min-w-12 rounded-full bg-red-500 flex items-center justify-center text-white text-xs font-bold">
                    0-50
                  </div>
                  <div>
                    <p className="font-medium text-red-700">A eviter</p>
                    <p className="text-xs text-red-600">Marge insuffisante ou marque peu demandee</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-yellow-50">
                  <div className="w-12 h-12 min-w-12 rounded-full bg-yellow-500 flex items-center justify-center text-white text-xs font-bold">
                    50-65
                  </div>
                  <div>
                    <p className="font-medium text-yellow-700">Moyen</p>
                    <p className="text-xs text-yellow-600">Opportunite a etudier, marge limitee</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-green-50">
                  <div className="w-12 h-12 min-w-12 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold">
                    65-80
                  </div>
                  <div>
                    <p className="font-medium text-green-700">Bon deal</p>
                    <p className="text-xs text-green-600">Bonne marge sur une marque recherchee</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-primary-50">
                  <div className="w-12 h-12 min-w-12 rounded-full bg-primary-600 flex items-center justify-center text-white text-xs font-bold">
                    80+
                  </div>
                  <div>
                    <p className="font-medium text-primary-700">Excellent</p>
                    <p className="text-xs text-primary-600">Forte marge, agissez vite!</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2">
              <Info className="text-green-600 flex-shrink-0 mt-0.5" size={18} />
              <div className="text-sm text-green-700">
                <strong>Badge VINTED :</strong> Les deals avec ce badge ont une marge calculee a partir des prix reels sur Vinted (produits "neuf avec etiquette"). Les autres ont une marge estimee algorithmiquement.
              </div>
            </div>

            <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
              <AlertTriangle className="text-amber-500 flex-shrink-0 mt-0.5" size={18} />
              <p className="text-sm text-amber-700">
                <strong>Conseil :</strong> Privilegiez les deals avec le badge VINTED et un SharkScore 70+. Ces opportunites ont une marge verifiee sur le marche reel.
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
                SharkScore minimum pour alerte
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
                    ? "Passez a Pro pour debloquer toutes les fonctionnalites"
                    : "Merci pour votre soutien!"}
                </p>
              </div>
              {user?.plan === "free" && (
                <Button>Passer a Pro</Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
