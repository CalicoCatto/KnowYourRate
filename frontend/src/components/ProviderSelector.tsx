import { useTranslation } from "react-i18next";
import type { ProviderInfo } from "@/types";

const PROVIDER_ICONS: Record<string, { gradient: string; letter: string }> = {
  openai: { gradient: "from-emerald-500 to-teal-600", letter: "O" },
  anthropic: { gradient: "from-orange-500 to-amber-600", letter: "A" },
  google: { gradient: "from-blue-500 to-cyan-600", letter: "G" },
  deepseek: { gradient: "from-violet-500 to-purple-600", letter: "D" },
};

interface Props {
  providers: ProviderInfo[];
  selected: string | null;
  onSelect: (providerId: string) => void;
}

export default function ProviderSelector({
  providers,
  selected,
  onSelect,
}: Props) {
  const { t } = useTranslation();

  return (
    <div>
      <h3 className="label text-base font-semibold mb-4">
        {t("setup.selectProvider")}
      </h3>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {providers.map((p) => {
          const icon = PROVIDER_ICONS[p.id] ?? {
            gradient: "from-gray-500 to-gray-600",
            letter: p.display_name[0] ?? "?",
          };
          const isSelected = selected === p.id;

          return (
            <button
              key={p.id}
              onClick={() => onSelect(p.id)}
              className={`flex items-center gap-4 rounded-2xl border p-5 text-left transition-all ${
                isSelected
                  ? "border-primary-400 bg-primary-50 ring-2 ring-primary-500 dark:bg-primary-950 dark:border-primary-600"
                  : "border-gray-200 bg-white hover:border-primary-300 hover:shadow-md dark:border-gray-800 dark:bg-gray-900 dark:hover:border-primary-700"
              }`}
            >
              <div
                className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${icon.gradient} text-xl font-bold text-white shadow-sm`}
              >
                {icon.letter}
              </div>
              <div className="min-w-0">
                <p className="font-semibold text-gray-900 dark:text-white">
                  {p.display_name}
                </p>
                <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                  {p.models.length} models available
                </p>
              </div>
              {isSelected && (
                <svg
                  className="ml-auto h-5 w-5 flex-shrink-0 text-primary-600 dark:text-primary-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
