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
} from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-green-500/5 rounded-full blur-3xl animate-pulse delay-500" />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <header className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <nav className="flex items-center justify-between">
            <div className="flex items-center bg-white rounded-lg px-3 py-1.5">
              <Image
                src="/logo.png"
                alt="SharkTed"
                width={180}
                height={50}
                className="h-8 sm:h-10 w-auto"
              />
            </div>
            <div className="flex items-center gap-2 sm:gap-4">
              <Link
                href="/auth/login"
                className="px-3 sm:px-5 py-2 sm:py-2.5 text-sm sm:text-base text-gray-300 hover:text-white transition font-medium"
              >
                Connexion
              </Link>
              <Link
                href="/auth/register"
                className="px-4 sm:px-6 py-2 sm:py-2.5 bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-xl text-sm sm:text-base font-semibold transition shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40"
              >
                Essai gratuit
              </Link>
            </div>
          </nav>
        </header>

        {/* Hero Section */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 pt-12 sm:pt-20 pb-16 sm:pb-24">
          <div className="text-center max-w-5xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-full text-primary-400 text-sm font-medium mb-6 sm:mb-8">
              <Zap size={16} className="animate-pulse" />
              <span>Nouveau: Alertes Discord en temps reel</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6 sm:mb-8 leading-tight">
              Trouve les deals{" "}
              <span className="relative">
                <span className="bg-gradient-to-r from-primary-400 via-primary-500 to-green-400 bg-clip-text text-transparent">
                  rentables
                </span>
                <svg
                  className="absolute -bottom-2 left-0 w-full"
                  viewBox="0 0 200 12"
                  fill="none"
                >
                  <path
                    d="M2 10C50 4 150 4 198 10"
                    stroke="url(#gradient)"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#22c55e" />
                      <stop offset="100%" stopColor="#10b981" />
                    </linearGradient>
                  </defs>
                </svg>
              </span>
              <br />
              <span className="text-gray-400">avant tout le monde</span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg sm:text-xl md:text-2xl text-gray-400 mb-8 sm:mb-10 max-w-3xl mx-auto leading-relaxed">
              Sharkted scanne <span className="text-white font-medium">Nike, Adidas, Courir</span> et
              10+ sources pour calculer ta{" "}
              <span className="text-green-400 font-medium">marge de revente Vinted</span> en temps reel.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12 sm:mb-16">
              <Link
                href="/auth/register"
                className="group flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-xl text-lg font-semibold transition-all shadow-xl shadow-primary-500/25 hover:shadow-primary-500/40 hover:scale-105"
              >
                Commencer gratuitement
                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="/dashboard/deals"
                className="group flex items-center justify-center gap-2 px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl text-lg font-semibold transition-all backdrop-blur-sm"
              >
                <Play size={20} className="text-primary-400" />
                Voir la demo
              </Link>
            </div>

            {/* Social Proof */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-8 text-sm text-gray-400">
              <div className="flex items-center gap-2">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 border-2 border-gray-900 flex items-center justify-center text-xs font-bold"
                    >
                      {String.fromCharCode(64 + i)}
                    </div>
                  ))}
                </div>
                <span>+200 resellers actifs</span>
              </div>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Star key={i} size={16} className="fill-yellow-400 text-yellow-400" />
                ))}
                <span className="ml-1">4.9/5 satisfaction</span>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Banner */}
        <section className="border-y border-white/5 bg-white/[0.02] backdrop-blur-sm">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8">
              {[
                { value: "15+", label: "Sources scannees", icon: Target },
                { value: "500+", label: "Deals / jour", icon: TrendingUp },
                { value: "32%", label: "Marge moyenne", icon: BarChart3 },
                { value: "< 5min", label: "Temps de detection", icon: Zap },
              ].map((stat, i) => (
                <div key={i} className="text-center">
                  <stat.icon className="w-6 h-6 sm:w-8 sm:h-8 text-primary-400 mx-auto mb-2 sm:mb-3" />
                  <div className="text-2xl sm:text-4xl font-bold text-white mb-1">{stat.value}</div>
                  <div className="text-xs sm:text-sm text-gray-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6">
              Tout ce qu&apos;il te faut pour{" "}
              <span className="text-primary-400">flip</span>
            </h2>
            <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto">
              Un outil complet pour identifier, analyser et tracker les meilleures opportunites de revente.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {[
              {
                icon: Zap,
                title: "Detection automatique",
                description:
                  "Scan continu de Nike, Adidas, Courir, Footlocker et 10+ sources pour ne rater aucune promo.",
                color: "from-yellow-500 to-orange-500",
              },
              {
                icon: TrendingUp,
                title: "FlipScore intelligent",
                description:
                  "Chaque deal est note de 0 a 100 selon la marge, la liquidite et la popularite sur Vinted.",
                color: "from-green-500 to-emerald-500",
              },
              {
                icon: Bell,
                title: "Alertes Discord",
                description:
                  "Notification instantanee quand un deal match tes criteres. Ne rate plus jamais une pepite.",
                color: "from-blue-500 to-cyan-500",
              },
              {
                icon: Target,
                title: "Filtres avances",
                description:
                  "Filtre par marque, categorie, marge minimum, score. Trouve exactement ce que tu cherches.",
                color: "from-purple-500 to-pink-500",
              },
              {
                icon: BarChart3,
                title: "Analytics detailles",
                description:
                  "Dashboard avec stats de performance, tendances marques et historique de tes achats.",
                color: "from-primary-500 to-primary-600",
              },
              {
                icon: Shield,
                title: "Sources fiables",
                description:
                  "Uniquement des sources retail officielles. Pas de fakes, pas d'arnaques, que du solide.",
                color: "from-red-500 to-rose-500",
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="group p-6 sm:p-8 bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 hover:border-white/10 rounded-2xl transition-all duration-300"
              >
                <div
                  className={`w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-gradient-to-br ${feature.color} p-3 mb-4 sm:mb-6 group-hover:scale-110 transition-transform`}
                >
                  <feature.icon className="w-full h-full text-white" />
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold mb-2 sm:mb-3">{feature.title}</h3>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6">
              Comment ca marche ?
            </h2>
            <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto">
              3 etapes simples pour commencer a generer des profits
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 sm:gap-12">
            {[
              {
                step: "01",
                title: "Configure tes criteres",
                description:
                  "Choisis tes marques preferees, ta marge minimum et tes tailles. Sharkted s'adapte a toi.",
              },
              {
                step: "02",
                title: "Recois des alertes",
                description:
                  "Des qu'un deal match tes criteres, tu recois une notification Discord avec tous les details.",
              },
              {
                step: "03",
                title: "Achete et revends",
                description:
                  "Achete le produit au prix promo, revends-le sur Vinted au prix marche. Profit.",
              },
            ].map((item, i) => (
              <div key={i} className="relative">
                <div className="text-6xl sm:text-8xl font-bold text-white/5 absolute -top-4 -left-2">
                  {item.step}
                </div>
                <div className="relative pt-8 sm:pt-12">
                  <h3 className="text-xl sm:text-2xl font-semibold mb-3 sm:mb-4">{item.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{item.description}</p>
                </div>
                {i < 2 && (
                  <ChevronRight
                    className="hidden md:block absolute top-1/2 -right-6 text-gray-700"
                    size={24}
                  />
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Pricing Preview */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6">
                Un prix simple et transparent
              </h2>
            </div>

            <div className="grid md:grid-cols-2 gap-6 sm:gap-8">
              {/* Free Plan */}
              <div className="p-6 sm:p-8 bg-white/[0.02] border border-white/5 rounded-2xl">
                <div className="text-lg font-medium text-gray-400 mb-2">Gratuit</div>
                <div className="text-4xl sm:text-5xl font-bold mb-4">0EUR</div>
                <p className="text-gray-400 mb-6">Pour decouvrir et tester</p>
                <ul className="space-y-3 mb-8">
                  {[
                    "5 sources (Nike, Adidas, Courir...)",
                    "10 deals / jour",
                    "FlipScore basique",
                    "Alertes email",
                  ].map((feature, i) => (
                    <li key={i} className="flex items-center gap-3 text-gray-300">
                      <CheckCircle size={18} className="text-gray-500 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/auth/register"
                  className="block w-full py-3 text-center bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl font-medium transition"
                >
                  Commencer gratuitement
                </Link>
              </div>

              {/* Pro Plan */}
              <div className="relative p-6 sm:p-8 bg-gradient-to-br from-primary-500/10 to-primary-600/5 border border-primary-500/20 rounded-2xl">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-primary-500 to-primary-600 rounded-full text-sm font-medium">
                  Populaire
                </div>
                <div className="text-lg font-medium text-primary-400 mb-2">Pro</div>
                <div className="text-4xl sm:text-5xl font-bold mb-4">
                  19EUR<span className="text-lg text-gray-400">/mois</span>
                </div>
                <p className="text-gray-400 mb-6">Pour les resellers serieux</p>
                <ul className="space-y-3 mb-8">
                  {[
                    "15+ sources (toutes)",
                    "Deals illimites",
                    "FlipScore avance + ML",
                    "Alertes Discord instantanees",
                    "Analytics detailles",
                    "Support prioritaire",
                  ].map((feature, i) => (
                    <li key={i} className="flex items-center gap-3 text-gray-300">
                      <CheckCircle size={18} className="text-primary-400 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/auth/register"
                  className="block w-full py-3 text-center bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-xl font-medium transition shadow-lg shadow-primary-500/25"
                >
                  Essayer Pro gratuitement
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
          <div className="relative max-w-4xl mx-auto text-center p-8 sm:p-12 lg:p-16 bg-gradient-to-br from-primary-500/10 via-primary-600/5 to-transparent border border-primary-500/20 rounded-3xl overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-primary-500/5 to-transparent" />
            <div className="relative">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6">
                Pret a faire du profit ?
              </h2>
              <p className="text-lg sm:text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
                Rejoins +200 resellers qui utilisent Sharkted pour trouver les meilleurs deals chaque jour.
              </p>
              <Link
                href="/auth/register"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white text-gray-900 hover:bg-gray-100 rounded-xl text-lg font-semibold transition-all hover:scale-105"
              >
                Creer mon compte gratuit
                <ArrowRight size={20} />
              </Link>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/5">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="bg-white rounded-md px-2 py-1">
                  <Image src="/logo.png" alt="SharkTed" width={120} height={35} className="h-6 w-auto" />
                </div>
                <span className="font-semibold text-gray-400">
                  2025 SharkTed. Tous droits reserves.
                </span>
              </div>
              <div className="flex items-center gap-6 text-sm text-gray-500">
                <Link href="#" className="hover:text-white transition">
                  CGU
                </Link>
                <Link href="#" className="hover:text-white transition">
                  Confidentialite
                </Link>
                <Link href="#" className="hover:text-white transition">
                  Contact
                </Link>
                <a
                  href="https://discord.gg/sharkted"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition"
                >
                  Discord
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
