"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Search, SlidersHorizontal, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface DealFiltersProps {
  onFiltersChange: (filters: Record<string, any>) => void;
  totalResults?: number;
}

const categories = [
  { value: "", label: "Toutes catégories" },
  { value: "sneakers", label: "Sneakers" },
  { value: "textile", label: "Textile" },
  { value: "accessoires", label: "Accessoires" },
];

const brands = [
  { value: "", label: "Toutes marques" },
  { value: "Nike", label: "Nike" },
  { value: "Adidas", label: "Adidas" },
  { value: "New Balance", label: "New Balance" },
  { value: "Jordan", label: "Jordan" },
  { value: "Puma", label: "Puma" },
  { value: "Asics", label: "Asics" },
  { value: "Reebok", label: "Reebok" },
  { value: "Stone Island", label: "Stone Island" },
  { value: "CP Company", label: "CP Company" },
  { value: "The North Face", label: "The North Face" },
  { value: "Carhartt WIP", label: "Carhartt WIP" },
  { value: "Stussy", label: "Stussy" },
  { value: "Supreme", label: "Supreme" },
  { value: "Ralph Lauren", label: "Ralph Lauren" },
  { value: "Lacoste", label: "Lacoste" },
  { value: "Tommy Hilfiger", label: "Tommy Hilfiger" },
  { value: "Hugo Boss", label: "Hugo Boss" },
  { value: "Arc'teryx", label: "Arc'teryx" },
  { value: "Patagonia", label: "Patagonia" },
  { value: "Moncler", label: "Moncler" },
];

const sources = [
  { value: "", label: "Toutes sources" },
  { value: "nike", label: "Nike" },
  { value: "adidas", label: "Adidas" },
  { value: "courir", label: "Courir" },
  { value: "footlocker", label: "Foot Locker" },
  { value: "snipes", label: "Snipes" },
  { value: "size", label: "Size?" },
  { value: "jdsports", label: "JD Sports" },
  { value: "kith", label: "Kith" },
  { value: "printemps", label: "Printemps" },
  { value: "laredoute", label: "La Redoute" },
  { value: "zalando", label: "Zalando" },
  { value: "asos", label: "ASOS" },
];

// NOUVEAU: Options de tri simplifiées (plus de score/marge)
const sortOptions = [
  { value: "smart", label: "Pertinence" },
  { value: "detected_at", label: "Plus récents" },
  { value: "discount", label: "Meilleure décote" },
  { value: "price_asc", label: "Prix croissant" },
  { value: "price_desc", label: "Prix décroissant" },
];

// NOUVEAU: Filtres par % de décote
const discountPresets = [
  { value: 0, label: "Tout" },
  { value: 20, label: "> 20%" },
  { value: 30, label: "> 30%" },
  { value: 50, label: "> 50%" },
  { value: 70, label: "> 70%" },
];

export function DealFilters({ onFiltersChange, totalResults }: DealFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState({
    brand: "",
    category: "",
    source: "",
    min_discount: 0,
    max_price: "",
    sort_by: "smart",
  });

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape" && isMobileDrawerOpen) {
      setIsMobileDrawerOpen(false);
    }
  }, [isMobileDrawerOpen]);

  useEffect(() => {
    if (isMobileDrawerOpen) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isMobileDrawerOpen, handleKeyDown]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery !== undefined) {
        applyFilters({ ...filters, search: searchQuery });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const applyFilters = (newFilters: typeof filters & { search?: string }) => {
    const apiFilters: Record<string, any> = {
      sort_by: newFilters.sort_by.includes("_asc") || newFilters.sort_by.includes("_desc")
        ? "price"
        : newFilters.sort_by,
      sort_order: newFilters.sort_by.includes("_asc") ? "asc" : "desc",
    };

    if (newFilters.brand) apiFilters.brand = newFilters.brand;
    if (newFilters.category) apiFilters.category = newFilters.category;
    if (newFilters.source) apiFilters.source = newFilters.source;
    if (newFilters.min_discount) apiFilters.min_discount = newFilters.min_discount;
    if (newFilters.max_price) apiFilters.max_price = Number(newFilters.max_price);
    if (newFilters.search) apiFilters.search = newFilters.search;

    onFiltersChange(apiFilters);
  };

  const handleChange = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    applyFilters(newFilters);
  };

  const resetFilters = () => {
    const defaultFilters = {
      brand: "",
      category: "",
      source: "",
      min_discount: 0,
      max_price: "",
      sort_by: "smart",
    };
    setFilters(defaultFilters);
    setSearchQuery("");
    applyFilters(defaultFilters);
  };

  const activeFiltersCount = [
    filters.brand,
    filters.category,
    filters.source,
    filters.min_discount > 0,
    filters.max_price,
    searchQuery,
  ].filter(Boolean).length;

  const filterPanelContent = (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* Brand Filter */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Marque
          </label>
          <select
            value={filters.brand}
            onChange={(e) => handleChange("brand", e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {brands.map((b) => (
              <option key={b.value} value={b.value}>{b.label}</option>
            ))}
          </select>
        </div>

        {/* Category Filter */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Catégorie
          </label>
          <select
            value={filters.category}
            onChange={(e) => handleChange("category", e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {categories.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>

        {/* Source Filter */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Source
          </label>
          <select
            value={filters.source}
            onChange={(e) => handleChange("source", e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {sources.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        {/* Sort */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Trier par
          </label>
          <select
            value={filters.sort_by}
            onChange={(e) => handleChange("sort_by", e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {sortOptions.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Discount Presets */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Décote minimum
          </label>
          <div className="flex flex-wrap gap-2">
            {discountPresets.map((preset) => (
              <button
                key={preset.value}
                onClick={() => handleChange("min_discount", preset.value)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                  filters.min_discount === preset.value
                    ? "bg-green-500 text-white shadow-sm"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                )}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Max Price */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Prix maximum
          </label>
          <div className="relative">
            <input
              type="number"
              value={filters.max_price}
              onChange={(e) => handleChange("max_price", e.target.value)}
              placeholder="Ex: 150"
              className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm">€</span>
          </div>
        </div>

        {/* Reset */}
        <div className="flex items-end">
          <Button
            variant="outline"
            onClick={resetFilters}
            className="w-full"
          >
            <X size={16} className="mr-2" />
            Réinitialiser
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="mb-6">
      {/* Search Bar + Toggle */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher un produit, une marque..."
            className="w-full bg-white border border-gray-200 rounded-xl pl-12 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
          />
        </div>

        {/* Filter Toggle Button */}
        <Button
          variant="outline"
          onClick={() => {
            if (window.innerWidth < 768) {
              setIsMobileDrawerOpen(true);
            } else {
              setIsExpanded(!isExpanded);
            }
          }}
          className={cn(
            "flex items-center gap-2 px-4 py-3 rounded-xl transition-all",
            activeFiltersCount > 0 && "border-blue-500 bg-blue-50 text-blue-600"
          )}
        >
          <SlidersHorizontal size={18} />
          <span>Filtres</span>
          {activeFiltersCount > 0 && (
            <span className="bg-blue-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {activeFiltersCount}
            </span>
          )}
          <ChevronDown
            size={16}
            className={cn(
              "transition-transform hidden sm:block",
              isExpanded && "rotate-180"
            )}
          />
        </Button>
      </div>

      {/* Desktop Expanded Filters */}
      <div
        className={cn(
          "hidden sm:block overflow-hidden transition-all duration-300",
          isExpanded ? "max-h-96 opacity-100 mb-4" : "max-h-0 opacity-0"
        )}
      >
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          {filterPanelContent}
        </div>
      </div>

      {/* Mobile Drawer */}
      {isMobileDrawerOpen && (
        <div className="fixed inset-0 z-50 sm:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setIsMobileDrawerOpen(false)}
          />
          
          {/* Drawer */}
          <div className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl p-6 max-h-[80vh] overflow-y-auto animate-slide-up">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-gray-900">Filtres</h3>
              <button
                onClick={() => setIsMobileDrawerOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <X size={20} />
              </button>
            </div>
            
            {filterPanelContent}
            
            <div className="mt-6 pt-4 border-t">
              <Button
                onClick={() => setIsMobileDrawerOpen(false)}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl"
              >
                Voir {totalResults || 0} résultats
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Active Filters Summary */}
      {activeFiltersCount > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {filters.brand && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
              {filters.brand}
              <button onClick={() => handleChange("brand", "")} className="hover:text-blue-900">
                <X size={14} />
              </button>
            </span>
          )}
          {filters.category && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
              {filters.category}
              <button onClick={() => handleChange("category", "")} className="hover:text-purple-900">
                <X size={14} />
              </button>
            </span>
          )}
          {filters.source && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
              {filters.source}
              <button onClick={() => handleChange("source", "")} className="hover:text-orange-900">
                <X size={14} />
              </button>
            </span>
          )}
          {filters.min_discount > 0 && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
              Décote &gt; {filters.min_discount}%
              <button onClick={() => handleChange("min_discount", 0)} className="hover:text-green-900">
                <X size={14} />
              </button>
            </span>
          )}
          {filters.max_price && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm">
              Max {filters.max_price}€
              <button onClick={() => handleChange("max_price", "")} className="hover:text-yellow-900">
                <X size={14} />
              </button>
            </span>
          )}
          {searchQuery && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
              "{searchQuery}"
              <button onClick={() => setSearchQuery("")} className="hover:text-gray-900">
                <X size={14} />
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
}
