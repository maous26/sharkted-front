import Link from "next/link";
import { ArrowRight, TrendingUp, Zap, Shield } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex items-center justify-between">
          <div className="text-2xl font-bold text-primary-400">FlipRadar</div>
          <div className="flex gap-4">
            <Link
              href="/auth/login"
              className="px-4 py-2 text-gray-300 hover:text-white transition"
            >
              Connexion
            </Link>
            <Link
              href="/auth/register"
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg transition"
            >
              Commencer
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <main className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            Trouve les deals rentables{" "}
            <span className="text-primary-400">avant tout le monde</span>
          </h1>
          <p className="text-xl text-gray-400 mb-8">
            FlipRadar scanne les promos retail et calcule automatiquement ta
            marge de revente sur Vinted. Fini les recherches manuelles, place
            aux deals intelligents.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/auth/register"
              className="flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 rounded-lg text-lg font-semibold transition"
            >
              Essai gratuit <ArrowRight size={20} />
            </Link>
            <Link
              href="/dashboard/deals"
              className="flex items-center gap-2 px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-lg font-semibold transition"
            >
              Voir les deals
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-24">
          <div className="bg-gray-800 p-6 rounded-xl">
            <div className="w-12 h-12 bg-primary-600/20 rounded-lg flex items-center justify-center mb-4">
              <Zap className="text-primary-400" size={24} />
            </div>
            <h3 className="text-xl font-semibold mb-2">Détection automatique</h3>
            <p className="text-gray-400">
              Notre IA scanne Nike, Adidas, Zalando et 15+ sources toutes les 15
              minutes pour trouver les meilleures promos.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl">
            <div className="w-12 h-12 bg-primary-600/20 rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="text-primary-400" size={24} />
            </div>
            <h3 className="text-xl font-semibold mb-2">FlipScore intelligent</h3>
            <p className="text-gray-400">
              Chaque deal est noté de 0 à 100 selon la marge, la liquidité et la
              popularité du produit sur Vinted.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl">
            <div className="w-12 h-12 bg-primary-600/20 rounded-lg flex items-center justify-center mb-4">
              <Shield className="text-primary-400" size={24} />
            </div>
            <h3 className="text-xl font-semibold mb-2">Alertes instantanées</h3>
            <p className="text-gray-400">
              Reçois une notification Discord dès qu'un deal correspond à tes
              critères. Ne rate plus jamais une pépite.
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6 mt-24 bg-gray-800 rounded-xl p-8">
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-400">15+</div>
            <div className="text-gray-400">Sources scannées</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-400">500+</div>
            <div className="text-gray-400">Deals/jour</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-400">30%</div>
            <div className="text-gray-400">Marge moyenne</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-400">85%</div>
            <div className="text-gray-400">Précision ML</div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 mt-20 border-t border-gray-700">
        <div className="flex justify-between items-center text-gray-400">
          <div>© 2024 FlipRadar. Tous droits réservés.</div>
          <div className="flex gap-6">
            <Link href="#" className="hover:text-white transition">
              CGU
            </Link>
            <Link href="#" className="hover:text-white transition">
              Confidentialité
            </Link>
            <Link href="#" className="hover:text-white transition">
              Contact
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
