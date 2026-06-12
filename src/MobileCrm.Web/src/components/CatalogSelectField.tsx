import type { AbraCatalogSelectorResult } from "@/hooks/useAbraCatalogSelector";

type CatalogSelectFieldProps = {
  label: string;
  required?: boolean;
  selector: AbraCatalogSelectorResult;
  busy?: boolean;
  noneLabel: string;
  loadingLabel: string;
  requiredErrorLabel: string;
  configurationErrorLabel: string;
  error?: string | null;
  onClearError?: () => void;
};

export function CatalogSelectField({
  label,
  required = false,
  selector,
  busy = false,
  noneLabel,
  loadingLabel,
  requiredErrorLabel,
  configurationErrorLabel,
  error,
  onClearError,
}: CatalogSelectFieldProps) {
  if (!selector.showPicker && !selector.isConfigurationError && selector.selectedDisplayName) {
    return null;
  }

  if (selector.isConfigurationError) {
    return (
      <div className="field">
        <span>{label}{required ? " *" : ""}</span>
        <p className="error" role="alert">
          {configurationErrorLabel}
        </p>
      </div>
    );
  }

  if (!selector.showPicker) {
    return null;
  }

  return (
    <label className="field">
      <span>{label}{required ? " *" : ""}</span>
      <select
        value={selector.value}
        onChange={(e) => {
          selector.setValue(e.target.value);
          onClearError?.();
        }}
        disabled={busy || selector.isLoading}
        required={required}
      >
        <option value="">{noneLabel}</option>
        {selector.items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.displayName}
          </option>
        ))}
      </select>
      {selector.isLoading && <p className="hint">{loadingLabel}</p>}
      {(error || selector.isSelectionMissing) && (
        <p className="error" role="alert">
          {error ?? requiredErrorLabel}
        </p>
      )}
    </label>
  );
}
