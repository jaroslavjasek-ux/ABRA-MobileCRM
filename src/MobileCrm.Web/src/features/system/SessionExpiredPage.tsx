import { Link } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { useEffect } from "react";
import { useI18n } from "@/i18n";

export function SessionExpiredPage() {
  const { clearSession } = useAuth();
  const { t } = useI18n();

  useEffect(() => {
    clearSession();
  }, [clearSession]);

  return (
    <div className="page-center">
      <div className="card">
        <h1>{t("system.sessionExpiredTitle")}</h1>
        <p>{t("system.sessionExpiredBody")}</p>
        <Link to="/login" className="btn-primary">
          {t("login.signIn")}
        </Link>
      </div>
    </div>
  );
}
