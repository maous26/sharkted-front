"use client";

import { useState, useEffect } from "react";
import { Save, Bell, User, Info, TrendingUp, Clock, BarChart3, AlertTriangle, ShoppingBag, Check, Lock } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { authApi } from "@/lib/api";

// Product categories with labels
const PRODUCT_CATEGORIES = [
  { id: "sneakers", label: "Sneakers", icon: "👟" },
  { id: "sacs", label: "Sacs", icon: "👜" },
  { id: "doudounes", label: "Doudounes", icon: "🧥" },
  { id: "vestes", label: "Vestes", icon: "🧥" },
  { id: "t-shirts", label: "T-shirts", icon: "👕" },
  { id: "sweats", label: "Sweats & Hoodies", icon: "👔" },
  { id: "pantalons", label: "Pantalons", icon: "👖" },
  { id: "robes", label: "Robes", icon: "👗" },
  { id: "accessoires", label: "Accessoires", icon: "🎒" },
  { id: "montres", label: "Montres", icon: "⌚" },
  { id: "lunettes", label: "Lunettes", icon: "🕶️" },
  { id: "chaussures", label: "Chaussures", icon: "👞" },
];

// Max categories by plan (champ libre compte comme 1)
const MAX_CATEGORIES_BY_PLAN: Record<string, number> = {
  basic: 1, // Seulement sneakers
  premium: 3,
  pro: 3,
  owner: 99,
};

// Check if user has basic plan (sneakers only)
const isBasicPlan = (plan: string | undefined) => {
  return !plan || plan === "free" || plan === "freemium" || plan === "basic";
};

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const [saving, setSaving] = useState(false);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefsSuccess, setPrefsSuccess] = useState(false);

  const [profileData, setProfileData] = useState({
    name: user?.full_name || user?.username || "",
  });

  const [alertData, setAlertData] = useState({
    email_alerts: user?.email_alerts ?? true,
    alert_threshold: user?.alert_threshold || 70,
  });

  // Category preferences
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [otherCategories, setOtherCategories] = useState("");
  const [showOtherInput, setShowOtherInput] = useState(false);

  // Load preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const { data } = await authApi.getPreferences();
        setSelectedCategories(data.categories || []);
        setOtherCategories(data.other_categories || "");
        setShowOtherInput(data.categories?.includes("autre") || !!data.other_categories);
      } catch (err) {
        console.error("Failed to load preferences:", err);
      }
    };
    loadPreferences();
  }, []);

  // Get max categories for current plan
  const userPlan = user?.plan?.toLowerCase() || "basic";
  const maxCategories = MAX_CATEGORIES_BY_PLAN[userPlan] || 3;
  const isBasic = isBasicPlan(user?.plan);

  // Count current selections (champ libre compte comme 1)
  const currentCount = selectedCategories.filter(c => c !== "autre").length + (showOtherInput ? 1 : 0);
  const canAddMore = currentCount < maxCategories;

  const toggleCategory = (categoryId: string) => {
    // Basic plan: only sneakers allowed
    if (isBasic && categoryId !== "sneakers") {
      return;
    }

    setSelectedCategories((prev) => {
      if (prev.includes(categoryId)) {
        return prev.filter((c) => c !== categoryId);
      } else {
        // Check if can add more
        const newCount = prev.filter(c => c !== "autre").length + 1 + (showOtherInput ? 1 : 0);
        if (newCount > maxCategories) {
          return prev;
        }
        return [...prev, categoryId];
      }
    });
  };

  const toggleOther = () => {
    // Basic plan: no custom categories
    if (isBasic) {
      return;
    }

    if (showOtherInput) {
      setShowOtherInput(false);
      setSelectedCategories((prev) => prev.filter((c) => c !== "autre"));
      setOtherCategories("");
    } else {
      // Check if can add more
      const newCount = selectedCategories.filter(c => c !== "autre").length + 1;
      if (newCount > maxCategories) {
        return;
      }
      setShowOtherInput(true);
      setSelectedCategories((prev) => [...prev, "autre"]);
    }
  };

  const handleSavePreferences = async () => {
    setSavingPrefs(true);
    setPrefsSuccess(false);
    try {
      await authApi.updatePreferences({
        categories: selectedCategories,
        other_categories: otherCategories,
      });
      setPrefsSuccess(true);
      setTimeout(() => setPrefsSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save preferences:", err);
    } finally {
      setSavingPrefs(false);
    }
  };

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

        {/* Product Categories Preferences */}
        <Card className="mb-6 border-purple-200 bg-gradient-to-br from-purple-50 to-white">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <ShoppingBag className="text-purple-600" size={20} />
              </div>
              <div>
                <CardTitle>Categories de produits</CardTitle>
                <p className="text-sm text-gray-500 mt-1">
                  {isBasic ? (
                    <>Abonnement Basic : uniquement les <strong>Sneakers</strong></>
                  ) : (
                    <>Selectionnez jusqu'a <strong>{maxCategories} categories</strong> (champ libre inclus)</>
                  )}
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Category count indicator */}
            {!isBasic && (
              <div className="mb-4 flex items-center gap-2">
                <div className={`text-sm font-medium ${currentCount >= maxCategories ? 'text-orange-600' : 'text-gray-600'}`}>
                  {currentCount} / {maxCategories} categories selectionnees
                </div>
                {currentCount >= maxCategories && (
                  <span className="text-xs text-orange-500">(limite atteinte)</span>
                )}
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-4">
              {PRODUCT_CATEGORIES.map((category) => {
                const isSelected = selectedCategories.includes(category.id);
                const isLocked = isBasic && category.id !== "sneakers";
                const isDisabled = isLocked || (!isSelected && !canAddMore);

                return (
                  <button
                    key={category.id}
                    onClick={() => toggleCategory(category.id)}
                    disabled={isDisabled && !isSelected}
                    className={`relative flex items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                      isSelected
                        ? "border-purple-500 bg-purple-50 text-purple-700"
                        : isLocked
                        ? "border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed opacity-60"
                        : isDisabled
                        ? "border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed"
                        : "border-gray-200 bg-white hover:border-purple-300 hover:bg-purple-50/50"
                    }`}
                  >
                    <span className="text-xl">{category.icon}</span>
                    <span className="text-sm font-medium">{category.label}</span>
                    {isSelected && (
                      <Check className="absolute top-1 right-1 text-purple-500" size={14} />
                    )}
                    {isLocked && (
                      <Lock className="absolute top-1 right-1 text-gray-400" size={12} />
                    )}
                  </button>
                );
              })}

              {/* Other category button */}
              <button
                onClick={toggleOther}
                disabled={isBasic || (!showOtherInput && !canAddMore)}
                className={`relative flex items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                  showOtherInput
                    ? "border-purple-500 bg-purple-50 text-purple-700"
                    : isBasic
                    ? "border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed opacity-60"
                    : !canAddMore
                    ? "border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed"
                    : "border-gray-200 bg-white hover:border-purple-300 hover:bg-purple-50/50"
                }`}
              >
                <span className="text-xl">✨</span>
                <span className="text-sm font-medium">Autre</span>
                {showOtherInput && (
                  <Check className="absolute top-1 right-1 text-purple-500" size={14} />
                )}
                {isBasic && (
                  <Lock className="absolute top-1 right-1 text-gray-400" size={12} />
                )}
              </button>
            </div>

            {/* Other categories text input */}
            {showOtherInput && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Precisez les autres categories
                </label>
                <input
                  type="text"
                  value={otherCategories}
                  onChange={(e) => setOtherCategories(e.target.value)}
                  placeholder="Ex: casquettes, ceintures, bijoux..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Separez les categories par des virgules
                </p>
              </div>
            )}

            {/* Selected summary */}
            {selectedCategories.length > 0 && (
              <div className="mb-4 p-3 bg-purple-100 rounded-lg">
                <p className="text-sm text-purple-700">
                  <strong>{selectedCategories.filter(c => c !== "autre").length}</strong> categorie(s) selectionnee(s)
                  {otherCategories && ` + autres: ${otherCategories}`}
                </p>
              </div>
            )}

            {/* Upgrade message for basic users */}
            {isBasic && (
              <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                <Lock className="text-amber-500 flex-shrink-0 mt-0.5" size={16} />
                <div>
                  <p className="text-sm text-amber-700">
                    <strong>Passez a Premium</strong> pour acceder a toutes les categories (sacs, montres, vetements...) et choisir jusqu'a 3 categories.
                  </p>
                </div>
              </div>
            )}

            <div className="flex items-center gap-3">
              <Button onClick={handleSavePreferences} disabled={savingPrefs}>
                <Save size={16} className="mr-2" />
                {savingPrefs ? "Enregistrement..." : "Enregistrer les preferences"}
              </Button>
              {prefsSuccess && (
                <span className="text-sm text-green-600 flex items-center gap-1">
                  <Check size={16} /> Preferences enregistrees!
                </span>
              )}
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
