import type { LocaleId, TranslateFn, TranslationTree, TranslationValues } from "@/i18n/types";
import { skSK } from "@/i18n/locales/sk-SK";

const catalogs: Record<LocaleId, TranslationTree> = {
  "sk-SK": skSK,
};

function resolvePath(tree: TranslationTree, path: string): string | undefined {
  const parts = path.split(".");
  let current: string | TranslationTree = tree;

  for (const part of parts) {
    if (typeof current !== "object" || current === null || !(part in current)) {
      return undefined;
    }
    current = current[part];
  }

  return typeof current === "string" ? current : undefined;
}

function interpolate(template: string, values?: TranslationValues): string {
  if (!values) {
    return template;
  }

  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => {
    const value = values[key];
    return value === undefined ? "" : String(value);
  });
}

export function createTranslator(locale: LocaleId = "sk-SK"): TranslateFn {
  const tree = catalogs[locale] ?? skSK;

  return (key: string, values?: TranslationValues) => {
    const template = resolvePath(tree, key);
    if (template === undefined) {
      return key;
    }
    return interpolate(template, values);
  };
}

export function getDefaultLocale(): LocaleId {
  return "sk-SK";
}
