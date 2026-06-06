import type { TranslateFn } from "@/i18n/types";

export function formatActivityStatus(status: string, t: TranslateFn): string {
  const key = `activity.status.${status}`;
  const label = t(key);
  return label === key ? status : label;
}

export function formatCommercialStatus(status: string | undefined, t: TranslateFn): string {
  if (!status) {
    return "";
  }
  const key = `commercialStatus.${status}`;
  const label = t(key);
  return label === key ? status : label;
}
