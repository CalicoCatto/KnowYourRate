import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { searchBrands } from "@/api/client";
import type { BrandInfo } from "@/types";

interface Props {
  platform: string | null;
  value: string;
  onChange: (name: string) => void;
  onSelect?: (brand: BrandInfo) => void;
}

export default function BrandSearch({ platform, value, onChange, onSelect }: Props) {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<BrandInfo[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const [showBrowser, setShowBrowser] = useState(false);
  const [selectedBrand, setSelectedBrand] = useState<BrandInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search as user types in the brand name input
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!value.trim() || value.length < 1) {
      setResults([]);
      setShowDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await searchBrands(value, platform ?? "", "");
        setResults(data.brands);
        if (data.brands.length > 0) {
          setShowDropdown(true);
        }
      } catch {
        // ignore search errors
      }
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [value, platform]);

  const handleBrandSelect = (brand: BrandInfo) => {
    onChange(brand.name);
    setSelectedBrand(brand);
    setShowDropdown(false);
    onSelect?.(brand);
  };

  const handleBrowse = async () => {
    setShowBrowser(true);
    setLoading(true);
    try {
      const data = await searchBrands(query, platform ?? "", selectedCategory);
      setResults(data.brands);
      setCategories(data.categories);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleBrowseSearch = async () => {
    setLoading(true);
    try {
      const data = await searchBrands(query, platform ?? "", selectedCategory);
      setResults(data.brands);
      setCategories(data.categories);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const budgetColor = (tier: string) => {
    if (tier === "极高") return "text-red-600 dark:text-red-400";
    if (tier === "高") return "text-orange-600 dark:text-orange-400";
    if (tier === "中高" || tier === "中") return "text-yellow-600 dark:text-yellow-400";
    return "text-gray-600 dark:text-gray-400";
  };

  return (
    <div className="space-y-2">
      {/* Brand name input with autocomplete dropdown */}
      <div className="relative" ref={dropdownRef}>
        <div className="flex gap-2">
          <input
            className="input flex-1"
            placeholder={t("creator.brandNamePlaceholder")}
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              setSelectedBrand(null);
            }}
            onFocus={() => {
              if (results.length > 0 && value.trim()) setShowDropdown(true);
            }}
          />
          <button
            type="button"
            onClick={handleBrowse}
            className="btn-secondary flex-shrink-0 text-sm"
          >
            {t("creator.browseBrands")}
          </button>
        </div>

        {/* Autocomplete dropdown */}
        {showDropdown && results.length > 0 && (
          <div className="absolute z-50 mt-1 w-full max-h-64 overflow-auto rounded-xl border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
            {results.slice(0, 8).map((brand) => (
              <button
                key={brand.id}
                type="button"
                className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                onClick={() => handleBrandSelect(brand)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-gray-900 dark:text-white">{brand.name}</span>
                    {brand.name_en && (
                      <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">{brand.name_en}</span>
                    )}
                  </div>
                  <span className={`text-xs font-medium ${budgetColor(brand.budget_tier)}`}>
                    {brand.budget_tier}
                  </span>
                </div>
                <div className="mt-1 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  <span>{brand.category}</span>
                  {brand.sub_category && <span>· {brand.sub_category}</span>}
                  {brand.cpm_low != null && brand.cpm_high != null && (
                    <span>· CPM ¥{brand.cpm_low}-{brand.cpm_high}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Selected brand info card */}
      {selectedBrand && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-950/30">
          <div className="flex items-start justify-between">
            <div>
              <h5 className="font-semibold text-gray-900 dark:text-white">
                {selectedBrand.name}
                {selectedBrand.name_en && (
                  <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                    {selectedBrand.name_en}
                  </span>
                )}
              </h5>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                {selectedBrand.category}
                {selectedBrand.sub_category && ` · ${selectedBrand.sub_category}`}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setSelectedBrand(null)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              ✕
            </button>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 text-sm">
            <div>
              <span className="text-xs text-gray-500 dark:text-gray-400">{t("creator.budgetTier")}</span>
              <p className={`font-medium ${budgetColor(selectedBrand.budget_tier)}`}>{selectedBrand.budget_tier}</p>
            </div>
            <div>
              <span className="text-xs text-gray-500 dark:text-gray-400">{t("creator.negotiationFlex")}</span>
              <p className="font-medium text-gray-900 dark:text-white">{selectedBrand.negotiation_flexibility}</p>
            </div>
            {selectedBrand.cpm_low != null && selectedBrand.cpm_high != null && (
              <div>
                <span className="text-xs text-gray-500 dark:text-gray-400">CPM</span>
                <p className="font-medium text-gray-900 dark:text-white">¥{selectedBrand.cpm_low}-{selectedBrand.cpm_high}</p>
              </div>
            )}
            <div>
              <span className="text-xs text-gray-500 dark:text-gray-400">{t("creator.paymentReliability")}</span>
              <p className="font-medium text-gray-900 dark:text-white">{selectedBrand.payment_reliability || "N/A"}</p>
            </div>
          </div>
          {selectedBrand.notes && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              {selectedBrand.notes}
            </p>
          )}
          {/* Platform badges */}
          <div className="mt-2 flex gap-2">
            {selectedBrand.bilibili && <span className="rounded-full bg-pink-100 px-2 py-0.5 text-xs text-pink-700 dark:bg-pink-900/30 dark:text-pink-300">B站</span>}
            {selectedBrand.douyin && <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-700 dark:text-gray-300">抖音</span>}
            {selectedBrand.kuaishou && <span className="rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-700 dark:bg-orange-900/30 dark:text-orange-300">快手</span>}
          </div>
        </div>
      )}

      {/* Brand browser modal */}
      {showBrowser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[80vh] w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-gray-900">
            {/* Header */}
            <div className="border-b border-gray-200 p-4 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t("creator.brandDatabase")}</h3>
                <button
                  type="button"
                  onClick={() => setShowBrowser(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl"
                >
                  ✕
                </button>
              </div>
              {/* Search & filter */}
              <div className="mt-3 flex gap-2">
                <input
                  className="input flex-1"
                  placeholder={t("creator.searchBrandPlaceholder")}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleBrowseSearch()}
                />
                <select
                  className="select w-32"
                  value={selectedCategory}
                  onChange={(e) => {
                    setSelectedCategory(e.target.value);
                    // Trigger search with new category
                    setTimeout(handleBrowseSearch, 0);
                  }}
                >
                  <option value="">{t("creator.allCategories")}</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <button onClick={handleBrowseSearch} className="btn-primary text-sm">
                  {t("creator.search")}
                </button>
              </div>
            </div>

            {/* Results */}
            <div className="max-h-[55vh] overflow-auto p-4">
              {loading ? (
                <p className="text-center text-gray-500 dark:text-gray-400 py-8">{t("creator.loading")}</p>
              ) : results.length === 0 ? (
                <p className="text-center text-gray-500 dark:text-gray-400 py-8">{t("creator.noBrandsFound")}</p>
              ) : (
                <div className="space-y-2">
                  {results.map((brand) => (
                    <button
                      key={brand.id}
                      type="button"
                      className="w-full rounded-xl border border-gray-200 p-4 text-left hover:border-primary-300 hover:bg-primary-50 dark:border-gray-700 dark:hover:border-primary-600 dark:hover:bg-primary-950/20 transition-colors"
                      onClick={() => {
                        handleBrandSelect(brand);
                        setShowBrowser(false);
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium text-gray-900 dark:text-white">{brand.name}</span>
                          {brand.name_en && (
                            <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">{brand.name_en}</span>
                          )}
                        </div>
                        <span className={`text-xs font-medium ${budgetColor(brand.budget_tier)}`}>
                          {t("creator.budget")}: {brand.budget_tier}
                        </span>
                      </div>
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                        <span>{brand.category}</span>
                        {brand.sub_category && <span>· {brand.sub_category}</span>}
                        {brand.cpm_low != null && brand.cpm_high != null && (
                          <span>· CPM ¥{brand.cpm_low}-{brand.cpm_high}</span>
                        )}
                        <span>· {t("creator.negotiation")}: {brand.negotiation_flexibility}</span>
                        {brand.payment_reliability && <span>· {t("creator.payment")}: {brand.payment_reliability}</span>}
                      </div>
                      {brand.notes && (
                        <p className="mt-1 text-xs text-gray-400 dark:text-gray-500 line-clamp-1">{brand.notes}</p>
                      )}
                      <div className="mt-2 flex gap-1.5">
                        {brand.bilibili && <span className="rounded-full bg-pink-100 px-2 py-0.5 text-xs text-pink-700 dark:bg-pink-900/30 dark:text-pink-300">B站</span>}
                        {brand.douyin && <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-700 dark:text-gray-300">抖音</span>}
                        {brand.kuaishou && <span className="rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-700 dark:bg-orange-900/30 dark:text-orange-300">快手</span>}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
