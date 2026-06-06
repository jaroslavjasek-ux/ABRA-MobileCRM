import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getSession } from "@/api/session";
import { queryKeys } from "@/api/queryKeys";
import { useAuth } from "@/auth/AuthContext";
import { ApiError, isUnauthorized, isServiceUnavailable } from "@/lib/errors";
import { getSessionToken } from "@/auth/sessionStorage";
import { useI18n } from "@/i18n";

export function AppLoadingPage() {
  const navigate = useNavigate();
  const { setSession, clearSession } = useAuth();
  const token = getSessionToken();
  const { t } = useI18n();

  const sessionQuery = useQuery({
    queryKey: queryKeys.session,
    queryFn: getSession,
    enabled: Boolean(token),
    retry: false,
  });

  useEffect(() => {
    if (!token) {
      navigate("/login", { replace: true });
      return;
    }

    if (sessionQuery.isSuccess && sessionQuery.data) {
      const sessionToken = sessionQuery.data.sessionToken ?? token;
      setSession(sessionToken, sessionQuery.data.representative);
      navigate("/app/my-day", { replace: true });
    }
  }, [token, sessionQuery.isSuccess, sessionQuery.data, navigate, setSession]);

  useEffect(() => {
    if (!sessionQuery.isError) {
      return;
    }
    const err = sessionQuery.error;
    clearSession();
    if (isUnauthorized(err)) {
      navigate("/app/session-expired", { replace: true });
    } else if (isServiceUnavailable(err) || (err instanceof ApiError && err.code === "NETWORK_ERROR")) {
      navigate("/app/connection-error", {
        replace: true,
        state: { from: "/app/my-day" },
      });
    } else {
      navigate("/login", { replace: true });
    }
  }, [sessionQuery.isError, sessionQuery.error, navigate, clearSession]);

  return (
    <div className="page-center">
      <div className="brand-block">
        <h1>{t("app.brand")}</h1>
        <p className="muted">{t("loading.connecting")}</p>
        <div className="spinner" aria-hidden />
      </div>
    </div>
  );
}
