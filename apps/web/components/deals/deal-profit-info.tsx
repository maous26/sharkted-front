import React from "react";
import { Deal } from "../../types";
import { cn } from "../../lib/utils";
import { CheckCircle2, AlertCircle } from "lucide-react";

interface DealProfitInfoProps {
    deal: Deal;
}

export const DealProfitInfo = ({ deal }: DealProfitInfoProps) => {
    // On priorise les stats réelles (Vinted)
    const vinted = deal.vinted_stats;
    const score = deal.score?.score_breakdown;

    // Données à afficher
    const hasRealData = !!vinted?.nb_listings;

    // Si on a des données Vinted, on les utilise
    // Sinon on fallback sur l'estimation du score
    const marginEuro = hasRealData ? vinted?.margin_euro : score?.estimated_margin_euro;
    const marginPct = hasRealData ? vinted?.margin_pct : score?.estimated_margin_pct;
    const medianPrice = hasRealData ? vinted?.price_median : deal.score?.recommended_price;

    if (marginEuro === undefined || marginPct === undefined) return null;

    const isProfitable = marginEuro > 0;

    return (
        <div className={cn(
            "p-3 rounded-lg border mt-2",
            hasRealData ? "bg-green-50/50 border-green-100" : "bg-gray-50 border-gray-100"
        )}>
            <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-semibold uppercase flex items-center gap-1.5">
                    {hasRealData ? (
                        <>
                            <CheckCircle2 size={14} className="text-green-600" />
                            <span className="text-green-700">Marché Vérifié</span>
                        </>
                    ) : (
                        <>
                            <span className="text-gray-500">Estimation IA</span>
                        </>
                    )}
                </h4>
                {hasRealData && (
                    <span className="text-[10px] bg-white px-1.5 py-0.5 rounded text-gray-400 border border-gray-100">
                        {vinted?.nb_listings} annonces
                    </span>
                )}
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <p className="text-[10px] text-gray-500 uppercase">Prix Marché</p>
                    <p className="font-bold text-gray-900">{medianPrice || "—"} €</p>
                </div>

                <div>
                    <p className="text-[10px] text-gray-500 uppercase">Profit Net</p>
                    <div className="flex items-baseline gap-1">
                        <span className={cn(
                            "font-bold",
                            isProfitable ? "text-green-600" : "text-red-500"
                        )}>
                            {isProfitable ? '+' : ''}{marginEuro.toFixed(2)} €
                        </span>
                        <span className={cn(
                            "text-xs",
                            isProfitable ? "text-green-600" : "text-red-500"
                        )}>
                            ({marginPct.toFixed(0)}%)
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};
