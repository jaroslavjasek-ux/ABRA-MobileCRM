import { FormEvent, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { postSession } from "@/api/session";
import { useAuth } from "@/auth/AuthContext";
import { isServiceUnavailable, isUnauthorized } from "@/lib/errors";
import { useOnlineStatus } from "@/hooks/useOnlineStatus";
import { useI18n } from "@/i18n";

export function LoginPage() {
  const [loginName, setLoginName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { setSession } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const online = useOnlineStatus();
  const { t } = useI18n();

  const returnTo = (location.state as { from?: string } | null)?.from ?? "/app/my-day";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!online) {
      setError(t("login.offline"));
      return;
    }

    setLoading(true);
    try {
      const res = await postSession({ loginName: loginName.trim(), password });
      const token = res.sessionToken;
      if (!token) {
        setError(t("login.noToken"));
        return;
      }
      setSession(token, res.representative);
      navigate(returnTo.startsWith("/app") ? returnTo : "/app/my-day", { replace: true });
    } catch (err) {
      if (isUnauthorized(err)) {
        setError(t("login.invalidCredentials"));
      } else if (isServiceUnavailable(err)) {
        navigate("/app/connection-error", { replace: true, state: { from: "/login" } });
      } else {
        setError(err instanceof Error ? err.message : t("login.failed"));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-center">
      <form className="card login-card form" onSubmit={handleSubmit}>
        <h1>{t("app.brand")}</h1>
        <p className="muted">{t("login.subtitle")}</p>

        <label className="field">
          <span>{t("login.username")}</span>
          <input
            type="text"
            autoComplete="username"
            value={loginName}
            onChange={(e) => setLoginName(e.target.value)}
            disabled={loading}
            required
          />
        </label>

        <label className="field">
          <span>{t("login.password")}</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            required
          />
        </label>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="btn-primary" disabled={loading || !loginName || !password}>
          {loading ? t("login.signingIn") : t("login.signIn")}
        </button>
      </form>
    </div>
  );
}
