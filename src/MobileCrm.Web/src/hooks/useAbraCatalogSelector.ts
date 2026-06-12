import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { PagedResult } from "@/api/types";

export type CatalogItem = {
  id: string;
  displayName: string;
};

export type AbraCatalogSelectorResult = {
  value: string;
  setValue: (id: string) => void;
  items: CatalogItem[];
  isLoading: boolean;
  isConfigurationError: boolean;
  showPicker: boolean;
  selectedDisplayName: string | null;
  isReady: boolean;
  isSelectionMissing: boolean;
};

/**
 * ABRA Desktop catalog selection pattern:
 * 0 values → configuration error
 * 1 value → auto-select (hide picker when autoHideSingleValue)
 * multiple values → user must choose when required
 */
export function useAbraCatalogSelector<T extends CatalogItem>(config: {
  enabled: boolean;
  required: boolean;
  autoHideSingleValue: boolean;
  queryKey: readonly unknown[];
  queryFn: () => Promise<PagedResult<T>>;
}): AbraCatalogSelectorResult {
  const [value, setValue] = useState("");

  const query = useQuery({
    queryKey: config.queryKey,
    queryFn: config.queryFn,
    enabled: config.enabled,
    staleTime: 60_000,
  });

  const items = useMemo(() => query.data?.items ?? [], [query.data?.items]);
  const isConfigurationError = config.enabled && query.isSuccess && items.length === 0;
  const showPicker =
    config.enabled &&
    query.isSuccess &&
    (items.length > 1 || (items.length === 1 && !config.autoHideSingleValue));

  useEffect(() => {
    if (!config.enabled) {
      setValue("");
      return;
    }
    if (!query.isSuccess) {
      return;
    }
    if (items.length === 1) {
      setValue(items[0]!.id);
      return;
    }
    if (items.length > 1) {
      setValue((current) =>
        current && items.some((item) => item.id === current) ? current : "",
      );
    }
  }, [config.enabled, query.isSuccess, items]);

  const selectedDisplayName = items.find((item) => item.id === value)?.displayName ?? null;
  const isReady = !config.enabled || (query.isSuccess && !isConfigurationError);
  const selectionRequired = config.enabled && config.required && items.length > 1;
  const isSelectionMissing = selectionRequired && !value.trim();

  return {
    value,
    setValue,
    items,
    isLoading: query.isLoading,
    isConfigurationError,
    showPicker,
    selectedDisplayName,
    isReady,
    isSelectionMissing,
  };
}
