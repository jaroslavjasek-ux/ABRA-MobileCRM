import { createContext, useContext, useMemo, type ReactNode } from "react";
import { createTranslator, getDefaultLocale } from "@/i18n/translate";
import {
  formatCalendarDate,
  formatDate,
  formatDateTimeFull,
  formatScheduleRange,
  formatSearchResultCount,
  formatTime,
} from "@/i18n/format";
import { formatActivityStatus, formatCommercialStatus } from "@/i18n/labels";
import type { LocaleId, TranslateFn } from "@/i18n/types";

export type I18nContextValue = {
  locale: LocaleId;
  t: TranslateFn;
  formatDate: (iso: string) => string;
  formatTime: (iso: string) => string;
  formatCalendarDate: (iso: string) => string;
  formatDateTimeFull: (iso: string) => string;
  formatScheduleRange: (startIso: string, endIso?: string) => string;
  formatSearchResultCount: (count: number) => string;
  formatActivityStatus: (status: string) => string;
  formatCommercialStatus: (status: string | undefined) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({
  children,
  locale = getDefaultLocale(),
}: {
  children: ReactNode;
  locale?: LocaleId;
}) {
  const value = useMemo<I18nContextValue>(() => {
    const t = createTranslator(locale);
    return {
      locale,
      t,
      formatDate: (iso) => formatDate(iso, locale),
      formatTime: (iso) => formatTime(iso, locale),
      formatCalendarDate: (iso) => formatCalendarDate(iso, locale),
      formatDateTimeFull: (iso) => formatDateTimeFull(iso, locale),
      formatScheduleRange: (start, end) => formatScheduleRange(start, end, locale),
      formatSearchResultCount: (count) => formatSearchResultCount(count, t),
      formatActivityStatus: (status) => formatActivityStatus(status, t),
      formatCommercialStatus: (status) => formatCommercialStatus(status, t),
    };
  }, [locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return ctx;
}

/** @deprecated Use useI18n — alias for clarity in components */
export const useTranslation = useI18n;
