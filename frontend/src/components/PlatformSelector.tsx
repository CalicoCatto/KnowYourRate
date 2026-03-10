import { useTranslation } from "react-i18next";
import type { Platform } from "@/types";
import { isCN } from "@/types";

interface Props {
  selected: Platform | null;
  onSelect: (platform: Platform) => void;
}

export default function PlatformSelector({ selected, onSelect }: Props) {
  const { t } = useTranslation();

  const internationalPlatforms: { id: Platform; icon: JSX.Element; gradient: string }[] = [
    {
      id: "youtube",
      gradient: "from-red-500 to-red-600",
      icon: (
        <svg className="h-7 w-7" viewBox="0 0 24 24" fill="currentColor">
          <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
        </svg>
      ),
    },
    {
      id: "tiktok",
      gradient: "from-gray-900 to-black dark:from-gray-100 dark:to-white",
      icon: (
        <svg className="h-7 w-7 dark:text-gray-900" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z" />
        </svg>
      ),
    },
  ];

  const cnPlatforms: { id: Platform; icon: JSX.Element; gradient: string }[] = [
    {
      id: "bilibili",
      gradient: "from-pink-400 to-blue-400",
      icon: (
        <svg className="h-7 w-7" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.813 4.653h.854c1.51.054 2.769.578 3.773 1.574 1.004.995 1.524 2.249 1.56 3.76v7.36c-.036 1.51-.556 2.769-1.56 3.773s-2.262 1.524-3.773 1.56H5.333c-1.51-.036-2.769-.556-3.773-1.56S.036 18.858 0 17.347v-7.36c.036-1.511.556-2.765 1.56-3.76 1.004-.996 2.262-1.52 3.773-1.574h.774l-1.174-1.12a1.234 1.234 0 0 1-.373-.906c0-.356.124-.658.373-.907l.027-.027c.267-.249.573-.373.92-.373.347 0 .653.124.92.373L9.653 4.44c.071.071.134.142.187.213h4.267a.836.836 0 0 1 .16-.213l2.853-2.747c.267-.249.573-.373.92-.373.347 0 .662.151.929.4.267.249.391.551.391.907 0 .355-.124.657-.373.906zM5.333 7.24c-.746.018-1.373.276-1.88.773-.506.498-.769 1.13-.786 1.894v7.52c.017.764.28 1.395.786 1.893.507.498 1.134.756 1.88.773h13.334c.746-.017 1.373-.275 1.88-.773.506-.498.769-1.129.786-1.893v-7.52c-.017-.765-.28-1.396-.786-1.894-.507-.497-1.134-.755-1.88-.773zM8 11.107c.373 0 .684.124.933.373.25.249.383.569.4.96v1.173c-.017.391-.15.711-.4.96-.249.25-.56.374-.933.374s-.684-.125-.933-.374c-.25-.249-.383-.569-.4-.96V12.44c.017-.391.15-.711.4-.96.249-.249.56-.373.933-.373zm8 0c.373 0 .684.124.933.373.25.249.383.569.4.96v1.173c-.017.391-.15.711-.4.96-.249.25-.56.374-.933.374s-.684-.125-.933-.374c-.25-.249-.383-.569-.4-.96V12.44c.017-.391.15-.711.4-.96.249-.249.56-.373.933-.373z" />
        </svg>
      ),
    },
    {
      id: "douyin",
      gradient: "from-gray-900 to-black dark:from-gray-100 dark:to-white",
      icon: (
        <svg className="h-7 w-7 dark:text-gray-900" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z" />
        </svg>
      ),
    },
    {
      id: "kuaishou",
      gradient: "from-orange-400 to-orange-600",
      icon: (
        <svg className="h-7 w-7" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15.5v-4.17l-3.5 2.08L6 13.33 9 11.5 6 9.67 7.5 7.58 11 9.67V5.5h2v4.17l3.5-2.09L18 9.67 15 11.5l3 1.83-1.5 2.08L13 13.33v4.17h-2z" />
        </svg>
      ),
    },
  ];

  const platforms = isCN ? cnPlatforms : internationalPlatforms;
  const gridCols = isCN ? "grid-cols-3" : "grid-cols-2";

  return (
    <div>
      <h3 className="label text-base font-semibold mb-4">
        {t("creator.selectPlatform")}
      </h3>
      <div className={`grid ${gridCols} gap-4`}>
        {platforms.map(({ id, icon, gradient }) => {
          const isSelected = selected === id;
          return (
            <button
              key={id}
              onClick={() => onSelect(id)}
              className={`flex flex-col items-center gap-3 rounded-2xl border p-6 transition-all ${
                isSelected
                  ? "border-primary-400 bg-primary-50 ring-2 ring-primary-500 dark:bg-primary-950 dark:border-primary-600"
                  : "border-gray-200 bg-white hover:border-primary-300 hover:shadow-md dark:border-gray-800 dark:bg-gray-900 dark:hover:border-primary-700"
              }`}
            >
              <div
                className={`flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} text-white shadow-sm`}
              >
                {icon}
              </div>
              <span className="font-semibold text-gray-900 dark:text-white">
                {t(`creator.${id}`)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
