import { useI18n } from "@/i18n";

type ActivityDocumentNumberProps = {
  documentNumber?: string;
  className?: string;
};

export function ActivityDocumentNumber({
  documentNumber,
  className = "activity-doc-number",
}: ActivityDocumentNumberProps) {
  const { t } = useI18n();

  if (!documentNumber) {
    return null;
  }

  return (
    <span className={className} aria-label={t("activity.documentNumber")}>
      {documentNumber}
    </span>
  );
}
