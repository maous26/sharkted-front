"use client";

import { useState, useEffect } from "react";
import { X, Search, SlidersHorizontal, ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";

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
  { value: "Nike", label: "Nike" },
  { value: "Adidas", label: "Adidas" },
  { value: "New Balance", label: "New Balance" },
  { value: "Jordan", label: "Jordan" },
  { value: "Ralph Lauren", label: "Ralph Lauren" },
  { value: "Puma", label: "Puma" },
  { value: "Lacoste", label: "Lacoste" },
];

const sortOptions = [
  { value: "detected_at", label: "Plus recents" },
  { value: "flip_score", label: "Meilleur score" },
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
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState({
    brand: "",
    category: "",
    min_score: 0,
    min_margin: 0,
    max_price: "",
    sort_by: "detected_at",
    recommended_only: false,
  });

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
    if (newFilters.min_score) apiFilters.min_score = newFilters.min_score;
    if (newFilters.min_margin) apiFilters.min_margin = newFilters.min_margin;
    if (newFilters.max_price) apiFilters.max_price = Number(newFilters.max_price);
    if (newFilters.recommended_only) apiFilters.recommended_only = true;
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
      min_score: 0,
      min_margin: 0,
      max_price: "",
      sort_by: "detected_at",
      recommended_only: false,
    };
    setFilters(defaultFilters);
    setSearchQuery("");
    applyFilters(defaultFilters);
  };

  const activeFiltersCount = [
    filters.brand,
    filters.category,
    filters.min_score > 0,
    filters.min_margin > 0,
    filters.max_price,
    filters.recommended_only,
    searchQuery,
  ].filter(Boolean).length;

  return (
    <div className="space-y-4">
      {/* Main Filter Bar */}
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search
            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            size={20}
          />
          <input
            type="text"
            placeholder="Rechercher un produit, une marque..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white text-gray-900 border border-gray-200 rounded-xl pl-12 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Quick Filters */}
        <div className="flex items-center gap-2 flex-wrap lg:flex-nowrap">
          {/* Sort Dropdown */}
          <div className="relative">
            <select
              value={filters.sort_by}
              onChange={(e) => handleChange("sort_by", e.target.value)}
              className="appearance-none bg-white border border-gray-200 rounded-xl px-4 py-3 pr-10 text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 cursor-pointer"
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <ChevronDown
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
              size={18}
            />
          </div>

          {/* Buy Only Toggle */}
          <button
            onClick={() => handleChange("recommended_only", !filters.recommended_only)}
            className={cn(
              "flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium transition-all",
              filters.recommended_only
                ? "bg-green-500 border-green-500 text-white"
                : "bg-white border-gray-200 text-gray-700 hover:border-gray-300"
            )}
          >
            {filters.recommended_only && <Check size={16} />}
            Acheter uniquement
          </button>

          {/* More Filters Toggle */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={cn(
              "flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium transition-all",
              isExpanded || activeFiltersCount > 0
                ? "bg-primary-500 border-primary-500 text-white"
                : "bg-white border-gray-200 text-gray-700 hover:border-gray-300"
            )}
          >
            <SlidersHorizontal size={18} />
            Filtres
            {activeFiltersCount > 0 && (
              <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                {activeFiltersCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Active Filters Chips */}
      {activeFiltersCount > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-gray-500">Filtres actifs:</span>

          {filters.brand && (
            <FilterChip
              label={`Marque: ${filters.brand}`}
              onRemove={() => handleChange("brand", "")}
            />
          )}
          {filters.category && (
            <FilterChip
              label={`Categorie: ${categories.find(c => c.value === filters.category)?.label}`}
              onRemove={() => handleChange("category", "")}
            />
          )}
          {filters.min_score > 0 && (
            <FilterChip
              label={`Score > ${filters.min_score}`}
              onRemove={() => handleChange("min_score", 0)}
            />
          )}
          {filters.min_margin > 0 && (
            <FilterChip
              label={`Marge > ${filters.min_margin}%`}
              onRemove={() => handleChange("min_margin", 0)}
            />
          )}
          {filters.max_price && (
            <FilterChip
              label={`Prix max: ${filters.max_price}EUR`}
              onRemove={() => handleChange("max_price", "")}
            />
          )}
          {searchQuery && (
            <FilterChip
              label={`"${searchQuery}"`}
              onRemove={() => setSearchQuery("")}
            />
          )}

          <button
            onClick={resetFilters}
            className="text-sm text-red-500 hover:text-red-600 font-medium ml-2"
          >
            Tout effacer
          </button>
        </div>
      )}

      {/* Expanded Filters Panel */}
      {isExpanded && (
        <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-6 shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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

            {/* Min Score */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Score minimum
              </label>
              <div className="flex gap-2">
                {scorePresets.map((preset) => (
                  <button
                    key={preset.value}
                    onClick={() => handleChange("min_score", preset.value)}
                    className={cn(
                      "flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors",
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
                      "flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors",
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
    <span className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
      {label}
      <button
        onClick={onRemove}
        className="hover:bg-primary-200 rounded-full p-0.5 transition-colors"
      >
        <X size={14} />
      </button>
    </span>
  );
}
