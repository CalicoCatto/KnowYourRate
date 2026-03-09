import { useTranslation } from "react-i18next";
import { useSettingsStore } from "@/store/settingsStore";

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const setLanguage = useSettingsStore((s) => s.setLanguage);

  const toggle = () => {
    const next = i18n.language === "en" ? "zh" : "en";
    i18n.changeLanguage(next);
    setLanguage(next);
  };

  return (
    <button
      onClick={toggle}
      className="btn-ghost rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wide"
      title={t("language." + (i18n.language === "en" ? "zh" : "en"))}
    >
      {i18n.language === "en" ? "EN" : "ZH"}
    </button>
  );
}
