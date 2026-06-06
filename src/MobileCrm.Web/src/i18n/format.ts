import type { LocaleId } from "@/i18n/types";

const DEFAULT_LOCALE: LocaleId = "sk-SK";

function localeTag(locale: LocaleId = DEFAULT_LOCALE): string {
  return locale;
}

function parseInstant(iso: string): Date {
  if (iso.length === 10 && /^\d{4}-\d{2}-\d{2}$/.test(iso)) {
    return new Date(`${iso}T12:00:00`);
  }
  return new Date(iso);
}

/** DD.MM.YYYY (e.g. 04.06.2026) — no weekday/month abbreviations */
function formatNumericDate(date: Date, locale: LocaleId = DEFAULT_LOCALE): string {
  const parts = new Intl.DateTimeFormat(localeTag(locale), {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).formatToParts(date);

  const get = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((p) => p.type === type)?.value ?? "";

  return `${get("day")}.${get("month")}.${get("year")}`;
}

/** ISO date `YYYY-MM-DD` or full instant — long agenda heading (My Day header) */
export function formatDate(iso: string, locale: LocaleId = DEFAULT_LOCALE): string {
  try {
    return parseInstant(iso).toLocaleDateString(localeTag(locale), {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

/** HH:mm (e.g. 08:00) — My Day today */
export function formatTime(iso: string, locale: LocaleId = DEFAULT_LOCALE): string {
  try {
    return parseInstant(iso).toLocaleTimeString(localeTag(locale), {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
}

/** DD.MM.YYYY — My Day overdue */
export function formatCalendarDate(iso: string, locale: LocaleId = DEFAULT_LOCALE): string {
  try {
    return formatNumericDate(parseInstant(iso), locale);
  } catch {
    return iso;
  }
}

/** DD.MM.YYYY HH:mm (e.g. 04.06.2026 23:02) — activity & firm lists */
export function formatDateTimeFull(iso: string, locale: LocaleId = DEFAULT_LOCALE): string {
  try {
    const date = parseInstant(iso);
    return `${formatNumericDate(date, locale)} ${formatTime(iso, locale)}`;
  } catch {
    return iso;
  }
}

/** @deprecated Use formatDateTimeFull */
export function formatDateTime(iso: string, locale: LocaleId = DEFAULT_LOCALE): string {
  return formatDateTimeFull(iso, locale);
}

/** Activity detail schedule — full numeric date/time, optional end */
export function formatScheduleRange(
  startIso: string,
  endIso?: string,
  locale: LocaleId = DEFAULT_LOCALE,
): string {
  try {
    if (!endIso) {
      return formatDateTimeFull(startIso, locale);
    }

    const start = parseInstant(startIso);
    const end = parseInstant(endIso);
    const sameDay = start.toDateString() === end.toDateString();

    if (sameDay) {
      return `${formatNumericDate(start, locale)} ${formatTime(startIso, locale)} – ${formatTime(endIso, locale)}`;
    }

    return `${formatDateTimeFull(startIso, locale)} – ${formatDateTimeFull(endIso, locale)}`;
  } catch {
    return endIso ? `${startIso} – ${endIso}` : startIso;
  }
}

export function formatSearchResultCount(
  count: number,
  t: (key: string, values?: Record<string, string | number>) => string,
): string {
  const rules = new Intl.PluralRules("sk-SK");
  const form = rules.select(count);

  if (form === "one") {
    return t("firms.resultCountOne", { count });
  }

  if (form === "few") {
    return t("firms.resultCountFew", { count });
  }

  return t("firms.resultCountMany", { count });
}
