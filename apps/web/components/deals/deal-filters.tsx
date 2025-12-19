"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Search, SlidersHorizontal, ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface DealFiltersProps {
  onFiltersChange: (filters: Record<string, any>) => void;
  totalResults?: number;
}

const categories = [
  { value: "", label: "Toutes categories" },
  { value: "sneakers", label: "Sneakers" },
  { value: "textile", label: "Textile" },
  { value: "accessoires", label: "Accessoires" },
];

const brands = [
  { value: "", label: "Toutes marques" },
  // Sneakers & Sport
  { value: "Nike", label: "Nike" },
  { value: "Adidas", label: "Adidas" },
  { value: "New Balance", label: "New Balance" },
  { value: "Jordan", label: "Jordan" },
  { value: "Puma", label: "Puma" },
  { value: "Asics", label: "Asics" },
  { value: "Reebok", label: "Reebok" },
  // Streetwear & Premium
  { value: "Stone Island", label: "Stone Island" },
  { value: "CP Company", label: "CP Company" },
  { value: "The North Face", label: "The North Face" },
  { value: "Carhartt WIP", label: "Carhartt WIP" },
  { value: "Stussy", label: "Stussy" },
  { value: "Supreme", label: "Supreme" },
  // Luxe Accessible
  { value: "Ralph Lauren", label: "Ralph Lauren" },
  { value: "Lacoste", label: "Lacoste" },
  { value: "Tommy Hilfiger", label: "Tommy Hilfiger" },
  { value: "Hugo Boss", label: "Hugo Boss" },
  { value: "Calvin Klein", label: "Calvin Klein" },
  // Outdoor & Heritage
  { value: "Arc'teryx", label: "Arc'teryx" },
  { value: "Patagonia", label: "Patagonia" },
  { value: "Moncler", label: "Moncler" },
  { value: "Timberland", label: "Timberland" },
  { value: "Levi's", label: "Levi's" },
];

const sources = [
  { value: "", label: "Toutes sources" },
  // Sneakers
  { value: "nike", label: "Nike" },
  { value: "adidas", label: "Adidas" },
  { value: "courir", label: "Courir" },
  { value: "footlocker", label: "Foot Locker" },
  { value: "snipes", label: "Snipes" },
  { value: "size", label: "Size?" },
  { value: "jdsports", label: "JD Sports" },
  // Textile Premium
  { value: "kith", label: "Kith" },
  { value: "printemps", label: "Printemps" },
  { value: "laredoute", label: "La Redoute" },
  // Multi-catégories
  { value: "zalando", label: "Zalando" },
  { value: "end", label: "END." },
  { value: "bstn", label: "BSTN" },
  { value: "yoox", label: "YOOX" },
];

const sortOptions = [
  { value: "detected_at", label: "Plus recents" },
  { value: "flip_score", label: "Meilleur SharkScore" },
  { value: "margin_pct", label: "Meilleure marge" },
  { value: "sale_price_asc", label: "Prix croissant" },
  { value: "sale_price_desc", label: "Prix decroissant" },
];

const marginPresets = [
  { value: 0, label: "Tout" },
  { value: 20, label: "> 20%" },
  { value: 30, label: "> 30%" },
  { value: 50, label: "> 50%" },
];

const scorePresets = [
  { value: 0, label: "Tout" },
  { value: 50, label: "> 50" },
  { value: 70, label: "> 70" },
  { value: 85, label: "> 85" },
];

export function DealFilters({ onFiltersChange, totalResults }: DealFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState({
    brand: "",
    category: "",
    source: "",
    min_score: 0,
    min_margin: 0,
    max_price: "",
    sort_by: "detected_at",
    recommended_only: false,
    positive_margin: false, // Marge > 0%
  });

  // Handle ESC key to close mobile drawer
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape" && isMobileDrawerOpen) {
      setIsMobileDrawerOpen(false);
    }
  }, [isMobileDrawerOpen]);

  // Body scroll lock when mobile drawer is open
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

  // Debounced search
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
        ? newFilters.sort_by.replace(/_asc|_desc/, "")
        : newFilters.sort_by,
      sort_order: newFilters.sort_by.includes("_asc") ? "asc" : "desc",
    };

    if (newFilters.brand) apiFilters.brand = newFilters.brand;
    if (newFilters.category) apiFilters.category = newFilters.category;
    if (newFilters.source) apiFilters.source = newFilters.source;
    if (newFilters.min_score) apiFilters.min_score = newFilters.min_score;
    if (newFilters.min_margin) apiFilters.min_margin = newFilters.min_margin;
    if (newFilters.max_price) apiFilters.max_price = Number(newFilters.max_price);
    if (newFilters.recommended_only) apiFilters.recommended_only = true;
    if (newFilters.positive_margin) apiFilters.min_margin = 1; // Marge > 0%
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
      min_score: 0,
      min_margin: 0,
      max_price: "",
      sort_by: "detected_at",
      recommended_only: false,
      positive_margin: false,
    };
    setFilters(defaultFilters);
    setSearchQuery("");
    applyFilters(defaultFilters);
  };

  const activeFiltersCount = [
    filters.brand,
    filters.category,
    filters.source,
    filters.min_score > 0,
    filters.min_margin > 0,
    filters.max_price,
    filters.recommended_only,
    filters.positive_margin,
    searchQuery,
  ].filter(Boolean).length;

  // Filter panel content (reused in desktop expand and mobile drawer)
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
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {brands.map((brand) => (
              <option key={brand.value} value={brand.value}>
                {brand.label}
              </option>
            ))}
          </select>
        </div>

        {/* Category Filter */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Categorie
          </label>
          <select
            value={filters.category}
            onChange={(e) => handleChange("category", e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {categories.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
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
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {sources.map((source) => (
              <option key={source.value} value={source.value}>
                {source.label}
              </option>
            ))}
          </select>
        </div>

        {/* Min Score */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            SharkScore minimum
          </label>
          <div className="flex gap-2">
            {scorePresets.map((preset) => (
              <button
                key={preset.value}
                onClick={() => handleChange("min_score", preset.value)}
                className={cn(
                  "flex-1 py-2 px-2 sm:px-3 rounded-lg text-xs sm:text-sm font-medium transition-colors",
                  filters.min_score === preset.value
                    ? "bg-primary-500 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                )}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Min Margin */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Marge minimum
          </label>
          <div className="flex gap-2">
            {marginPresets.map((preset) => (
              <button
                key={preset.value}
                onClick={() => handleChange("min_margin", preset.value)}
                className={cn(
                  "flex-1 py-2 px-2 sm:px-3 rounded-lg text-xs sm:text-sm font-medium transition-colors",
                  filters.min_margin === preset.value
                    ? "bg-green-500 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                )}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Price Range */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Prix maximum
        </label>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min="0"
            max="500"
            step="10"
            value={filters.max_price || 500}
            onChange={(e) =>
              handleChange("max_price", e.target.value === "500" ? "" : e.target.value)
            }
            className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
          />
          <span className="text-sm font-medium text-gray-700 w-20 text-right">
            {filters.max_price ? `${filters.max_price} EUR` : "Illimite"}
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Main Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search
            className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 text-gray-400"
            size={18}
          />
          <input
            type="text"
            placeholder="Rechercher..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white text-gray-900 border border-gray-200 rounded-xl pl-10 sm:pl-12 pr-10 py-2.5 sm:py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Quick Filters Row */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0 sm:flex-nowrap">
          {/* Sort Dropdown */}
          <div className="relative flex-shrink-0">
            <select
              value={filters.sort_by}
              onChange={(e) => handleChange("sort_by", e.target.value)}
              className="appearance-none bg-white border border-gray-200 rounded-xl px-3 sm:px-4 py-2.5 sm:py-3 pr-8 sm:pr-10 text-xs sm:text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 cursor-pointer"
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <ChevronDown
              className="absolute right-2 sm:right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
              size={16}
            />
          </div>

          {/* Buy Only Toggle - Hidden text on mobile */}
          <button
            onClick={() => handleChange("recommended_only", !filters.recommended_only)}
            className={cn(
              "flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2.5 sm:py-3 rounded-xl border text-xs sm:text-sm font-medium transition-all flex-shrink-0 whitespace-nowrap",
              filters.recommended_only
                ? "bg-green-500 border-green-500 text-white"
                : "bg-white border-gray-200 text-gray-700 hover:border-gray-300"
            )}
          >
            {filters.recommended_only && <Check size={14} />}
            <span className="hidden sm:inline">Acheter uniquement</span>
            <span className="sm:hidden">Acheter</span>
          </button>

          {/* Positive Margin Toggle */}
          <button
            onClick={() => handleChange("positive_margin", !filters.positive_margin)}
            className={cn(
              "flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2.5 sm:py-3 rounded-xl border text-xs sm:text-sm font-medium transition-all flex-shrink-0 whitespace-nowrap",
              filters.positive_margin
                ? "bg-green-500 border-green-500 text-white"
                : "bg-white border-gray-200 text-gray-700 hover:border-gray-300"
            )}
          >
            {filters.positive_margin && <Check size={14} />}
            <span className="hidden sm:inline">Marge positive</span>
            <span className="sm:hidden">Marge +</span>
          </button>

          {/* More Filters Toggle - Opens drawer on mobile */}
          <button
            onClick={() => {
              if (window.innerWidth < 640) {
                setIsMobileDrawerOpen(true);
              } else {
                setIsExpanded(!isExpanded);
              }
            }}
            className={cn(
              "flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2.5 sm:py-3 rounded-xl border text-xs sm:text-sm font-medium transition-all flex-shrink-0",
              (isExpanded || isMobileDrawerOpen || activeFiltersCount > 0)
                ? "bg-primary-500 border-primary-500 text-white"
                : "bg-white border-gray-200 text-gray-700 hover:border-gray-300"
            )}
            aria-expanded={isExpanded || isMobileDrawerOpen}
          >
            <SlidersHorizontal size={16} />
            <span className="hidden sm:inline">Filtres</span>
            {activeFiltersCount > 0 && (
              <span className="bg-white/20 px-1.5 sm:px-2 py-0.5 rounded-full text-xs">
                {activeFiltersCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Mobile Filter Drawer */}
      {isMobileDrawerOpen && (
        <>
          {/* Overlay */}
          <div
            className="sm:hidden fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsMobileDrawerOpen(false)}
            aria-hidden="true"
          />
          {/* Drawer */}
          <div
            className="sm:hidden fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-xl max-h-[85vh] overflow-y-auto"
            role="dialog"
            aria-modal="true"
            aria-label="Filtres"
          >
            {/* Drawer Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Filtres</h2>
              <button
                onClick={() => setIsMobileDrawerOpen(false)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                aria-label="Fermer les filtres"
              >
                <X size={20} />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="p-4">
              {filterPanelContent}
            </div>

            {/* Drawer Footer */}
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-4 py-3 flex gap-3">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  resetFilters();
                  setIsMobileDrawerOpen(false);
                }}
              >
                Réinitialiser
              </Button>
              <Button
                variant="primary"
                className="flex-1"
                onClick={() => setIsMobileDrawerOpen(false)}
              >
                Appliquer
              </Button>
            </div>
          </div>
        </>
      )}

      {/* Active Filters Chips */}
      {activeFiltersCount > 0 && (
        <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
          <span className="text-xs sm:text-sm text-gray-500 hidden sm:inline">Filtres actifs:</span>

          {filters.brand && (
            <FilterChip
              label={filters.brand}
              onRemove={() => handleChange("brand", "")}
            />
          )}
          {filters.category && (
            <FilterChip
              label={categories.find(c => c.value === filters.category)?.label || filters.category}
              onRemove={() => handleChange("category", "")}
            />
          )}
          {filters.source && (
            <FilterChip
              label={sources.find(s => s.value === filters.source)?.label || filters.source}
              onRemove={() => handleChange("source", "")}
            />
          )}
          {filters.min_score > 0 && (
            <FilterChip
              label={`>${filters.min_score}`}
              onRemove={() => handleChange("min_score", 0)}
            />
          )}
          {filters.min_margin > 0 && (
            <FilterChip
              label={`>${filters.min_margin}%`}
              onRemove={() => handleChange("min_margin", 0)}
            />
          )}
          {filters.max_price && (
            <FilterChip
              label={`<${filters.max_price}€`}
              onRemove={() => handleChange("max_price", "")}
            />
          )}
          {filters.positive_margin && (
            <FilterChip
              label="Marge positive"
              onRemove={() => handleChange("positive_margin", false)}
            />
          )}
          {searchQuery && (
            <FilterChip
              label={searchQuery.length > 10 ? searchQuery.slice(0, 10) + "..." : searchQuery}
              onRemove={() => setSearchQuery("")}
            />
          )}

          <button
            onClick={resetFilters}
            className="text-xs sm:text-sm text-red-500 hover:text-red-600 font-medium ml-1 sm:ml-2"
          >
            Effacer
          </button>
        </div>
      )}

      {/* Desktop Expanded Filters Panel - Hidden on mobile */}
      {isExpanded && (
        <div className="hidden sm:block bg-white rounded-2xl border border-gray-200 p-4 sm:p-6 shadow-sm">
          {filterPanelContent}
        </div>
      )}

      {/* Results count */}
      {totalResults !== undefined && (
        <div className="text-sm text-gray-500">
          {totalResults} resultats trouves
        </div>
      )}
    </div>
  );
}

// Filter Chip Component
function FilterChip({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-0.5 sm:gap-1 px-2 sm:px-3 py-0.5 sm:py-1 bg-primary-100 text-primary-700 rounded-full text-xs sm:text-sm font-medium">
      {label}
      <button
        onClick={onRemove}
        className="hover:bg-primary-200 rounded-full p-0.5 transition-colors"
        aria-label={`Supprimer le filtre ${label}`}
      >
        <X size={12} className="sm:w-3.5 sm:h-3.5" />
      </button>
    </span>
  );
}
