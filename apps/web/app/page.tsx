import React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  TrendingUp,
  Zap,
  Shield,
  Bell,
  Target,
  BarChart3,
  CheckCircle,
  Star,
  ChevronRight,
  Play,
  Crown,
  Lock
} from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-hidden font-sans">
      {/* Animated Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-950 to-gray-950" />
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-primary-500/10 rounded-full blur-[100px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-[100px] animate-pulse delay-700" />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <header className="container mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <nav className="flex items-center justify-between backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl px-6 py-3">
            <div className="flex items-center">
              <span className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-blue-400 bg-clip-text text-transparent">
                SharkTed
              </span>
            </div>
            <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-300">
              <Link href="#features" className="hover:text-white transition">Fonctionnalités</Link>
              <Link href="#how-it-works" className="hover:text-white transition">Comment ça marche</Link>
              <Link href="#pricing" className="hover:text-white transition">Prix</Link>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/auth/login"
                className="text-sm font-medium text-gray-300 hover:text-white transition hidden sm:block"
              >
                Connexion
              </Link>
              <Link
                href="/auth/register"
                className="px-5 py-2.5 bg-white text-gray-900 rounded-xl text-sm font-bold hover:bg-gray-100 transition shadow-lg hover:shadow-xl hover:-translate-y-0.5"
              >
                Essai Gratuit
              </Link>
            </div>
          </nav>
        </header>

        {/* Hero Section */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-32">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-full text-primary-400 text-sm font-medium mb-8 animate-fade-in-up">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
              </span>
              Nouveau: Mode autonome v3 disponible
            </div>

            <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold mb-8 leading-tight tracking-tight">
              L'outil ultime pour <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-400 via-blue-400 to-primary-400 animate-gradient-x">
                dominer l'achat-revente
              </span>
            </h1>

            <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed">
              Sharkted scanne <span className="text-white font-semibold">24h/24</span> les meilleurs sites pour détecter les erreurs de prix et les opportunités de profit. <br className="hidden sm:block" />
              Ne perds plus ton temps à chercher.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              <Link
                href="/auth/register"
                className="w-full sm:w-auto px-8 py-4 bg-primary-600 hover:bg-primary-500 text-white rounded-xl font-bold text-lg transition-all shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40 hover:-translate-y-1 flex items-center justify-center gap-2"
              >
                Commencer à flipper
                <ArrowRight size={20} />
              </Link>
              <Link
                href="#pricing"
                className="w-full sm:w-auto px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-xl font-bold text-lg transition-all backdrop-blur-sm flex items-center justify-center gap-2"
              >
                Voir les offres
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 border-t border-white/10 pt-12">
              {[
                { label: "Deals détectés", value: "500+/j" },
                { label: "Marge Moyenne", value: "35%" },
                { label: "Sites Scannés", value: "25+" },
                { label: "Resellers satisfaits", value: "1.2k+" },
              ].map((stat, i) => (
                <div key={i}>
                  <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                  <div className="text-sm text-gray-500 uppercase tracking-wider">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section id="features" className="container mx-auto px-4 sm:px-6 lg:px-8 py-24 bg-gray-900/50">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">Tout ce dont tu as besoin</h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Une suite d'outils complète conçue par des resellers, pour des resellers.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Zap,
                title: "Scan Ultra-Rapide",
                desc: "Notre algorithme détecte les nouveaux produits et les baisses de prix en moins de 60 secondes.",
                color: "text-yellow-400"
              },
              {
                icon: TrendingUp,
                title: "Analyse de Profitabilité",
                desc: "Calcul automatique de la marge nette estimée en se basant sur le marché réel (Vinted/StockX).",
                color: "text-green-400"
              },
              {
                icon: Lock,
                title: "Proxies Résidentiels",
                desc: "Accès exclusif aux sites protégés (Nike, Zalando, Vinted) grâce à notre réseau de proxies (Plan Whale).",
                color: "text-blue-400"
              },
              {
                icon: Bell,
                title: "Alertes Instantanées",
                desc: "Reçois une notification Discord ou Email dès qu'une pépite correspondant à tes filtres pop.",
                color: "text-primary-400"
              },
              {
                icon: BarChart3,
                title: "Dashboard Pro",
                desc: "Suis tes performances, ton ROI et gère ton inventory directement depuis l'application.",
                color: "text-purple-400"
              },
              {
                icon: Shield,
                title: "Sécurité Maximale",
                desc: "Paiements sécurisés, données cryptées et transparence totale sur les sources.",
                color: "text-red-400"
              }
            ].map((item, i) => (
              <div key={i} className="p-8 rounded-3xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all hover:-translate-y-1">
                <item.icon className={`w-12 h-12 ${item.color} mb-6`} />
                <h3 className="text-xl font-bold mb-3">{item.title}</h3>
                <p className="text-gray-400 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="container mx-auto px-4 sm:px-6 lg:px-8 py-24 relative">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[600px] bg-primary-500/5 rounded-full blur-[120px] pointer-events-none" />

          <div className="text-center mb-16 relative z-10">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">Choisis ton arme</h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Des plans adaptés à chaque stade de ton évolution de reseller.
              <br /> Annulable à tout moment.
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8 relative z-10 max-w-6xl mx-auto">
            {/* Freemium */}
            <div className="p-8 rounded-3xl bg-gray-900/50 border border-white/5 flex flex-col">
              <div className="mb-4">
                <span className="px-3 py-1 bg-gray-800 text-gray-300 rounded-lg text-xs font-bold uppercase tracking-wider">Découverte</span>
              </div>
              <h3 className="text-2xl font-bold mb-2">Freemium</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-bold">0€</span>
                <span className="text-gray-500">/mois</span>
              </div>
              <p className="text-gray-400 mb-8 border-b border-white/10 pb-8">
                Parfait pour tester l'outil et faire ses premiers euros.
              </p>
              <ul className="space-y-4 mb-8 flex-1">
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-gray-500 mt-0.5 shrink-0" />
                  <span className="text-gray-300">5 deals / jour</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-gray-500 mt-0.5 shrink-0" />
                  <span className="text-gray-300">Catégorie Sneakers uniquement</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-heading mt-0.5 shrink-0" />
                  <span className="text-gray-300">1 "Top Deal" (&gt;70 Score) / jour</span>
                </li>
                <li className="flex items-start gap-3 text-sm opacity-50">
                  <Lock size={18} className="text-gray-600 mt-0.5 shrink-0" />
                  <span className="text-gray-500">Pas d'accès Proxies</span>
                </li>
              </ul>
              <Link href="/auth/register?plan=free" className="block w-full py-4 text-center rounded-xl bg-gray-800 hover:bg-gray-700 text-white font-bold transition">
                Créer un compte gratuit
              </Link>
            </div>

            {/* Shark */}
            <div className="p-8 rounded-3xl bg-gray-900 border border-primary-500/30 shadow-2xl shadow-primary-500/10 flex flex-col relative overflow-hidden group">
              <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-primary-500 to-blue-500" />
              <div className="mb-4 flex justify-between items-center">
                <span className="px-3 py-1 bg-primary-500/10 text-primary-400 rounded-lg text-xs font-bold uppercase tracking-wider">Le + Populaire</span>
                <Zap className="text-primary-400 w-5 h-5" />
              </div>
              <h3 className="text-2xl font-bold mb-2 text-white">Shark</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-5xl font-bold text-white">9<span className="text-3xl">.90€</span></span>
                <span className="text-gray-500">/mois</span>
              </div>
              <p className="text-gray-300 mb-8 border-b border-white/10 pb-8">
                L'indispensable pour scaler ton business sérieusement.
              </p>
              <ul className="space-y-4 mb-8 flex-1">
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-primary-400 mt-0.5 shrink-0" />
                  <span className="text-white font-medium">Deals illimités</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-primary-400 mt-0.5 shrink-0" />
                  <span className="text-white">Toutes catégories (Mode, Luxe...)</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-primary-400 mt-0.5 shrink-0" />
                  <span className="text-white">Sources standards (Courir, JD...)</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-primary-400 mt-0.5 shrink-0" />
                  <span className="text-white">SharkScore Avancé</span>
                </li>
              </ul>
              <Link href="/auth/register?plan=shark" className="block w-full py-4 text-center rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white font-bold transition shadow-lg transform group-hover:scale-[1.02]">
                Devenir un Shark
              </Link>
            </div>

            {/* Whale */}
            <div className="p-8 rounded-3xl bg-gray-900/50 border border-blue-500/20 flex flex-col relative overflow-hidden">
              <div className="mb-4 flex justify-between items-center">
                <span className="px-3 py-1 bg-blue-500/10 text-blue-400 rounded-lg text-xs font-bold uppercase tracking-wider">Pour les Pros</span>
                <Crown className="text-blue-400 w-5 h-5" />
              </div>
              <h3 className="text-2xl font-bold mb-2">Whale</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-5xl font-bold">29<span className="text-3xl">.90€</span></span>
                <span className="text-gray-500">/mois</span>
              </div>
              <p className="text-gray-400 mb-8 border-b border-white/10 pb-8">
                Accès total aux sites sécurisés high-profit.
              </p>
              <ul className="space-y-4 mb-8 flex-1">
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-blue-400 mt-0.5 shrink-0" />
                  <span className="text-white font-bold">Tout du plan Shark</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-blue-400 mt-0.5 shrink-0" />
                  <span className="text-white font-bold">Sites Premium avec Proxies</span>
                  <span className="text-[10px] bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded ml-auto border border-blue-500/30">Nike, Zalando...</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-blue-400 mt-0.5 shrink-0" />
                  <span className="text-gray-300">Vinted Scoring Temps Réel</span>
                </li>
                <li className="flex items-start gap-3 text-sm">
                  <CheckCircle size={18} className="text-blue-400 mt-0.5 shrink-0" />
                  <span className="text-gray-300">Support Prioritaire 24/7</span>
                </li>
              </ul>
              <Link href="/auth/register?plan=whale" className="block w-full py-4 text-center rounded-xl bg-white/10 hover:bg-white/20 hover:text-white border border-white/10 text-gray-300 font-bold transition">
                Accès Whale
              </Link>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="bg-gradient-to-r from-primary-900/50 to-blue-900/50 rounded-3xl p-12 text-center border border-white/10 relative overflow-hidden">
            <div className="relative z-10 max-w-2xl mx-auto">
              <h2 className="text-4xl font-bold mb-6">Prêt à encaisser ?</h2>
              <p className="text-xl text-gray-300 mb-8">
                Rejoins la communauté la plus active de France.
                <br />Commence gratuitement aujourd'hui, annule quand tu veux.
              </p>
              <Link
                href="/auth/register"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white text-gray-900 hover:bg-gray-100 rounded-xl text-lg font-bold transition hover:scale-105"
              >
                Créer mon compte
                <ArrowRight size={20} />
              </Link>
            </div>
          </div>
        </section>

        <footer className="border-t border-white/5 bg-black/20 py-12 text-center text-gray-500 text-sm">
          <p>&copy; 2025 SharkTed. Tous droits réservés.</p>
        </footer>
      </div>
    </div>
  );
}
