import { useLocation, useNavigate } from "react-router-dom";
import { useI18n } from "@/i18n";

export function ConnectionErrorPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/app/my-day";
  const { t } = useI18n();

  return (
    <div className="page-center">
      <div className="card">
        <h1>{t("system.connectionTitle")}</h1>
        <p>{t("system.connectionBody")}</p>
        <button type="button" className="btn-primary" onClick={() => navigate(from, { replace: true })}>
          {t("common.retry")}
        </button>
      </div>
    </div>
  );
}
