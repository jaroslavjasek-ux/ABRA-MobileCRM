import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ConnectivityBanner } from "@/features/system/ConnectivityBanner";
import { useAuth } from "@/auth/AuthContext";
import { deleteSession, getSession } from "@/api/session";
import { queryKeys } from "@/api/queryKeys";
import { useNavigate } from "react-router-dom";
import { useI18n } from "@/i18n";
import { createActivityPath } from "@/lib/navigation";

export function AuthenticatedLayout() {
  const { clearSession } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();

  const sessionQuery = useQuery({
    queryKey: queryKeys.session,
    queryFn: getSession,
  });
  const showCreateActivity = sessionQuery.data?.activityFeatures?.createActivity ?? false;

  const handleLogout = async () => {
    try {
      await deleteSession();
    } catch {
      /* ignore */
    }
    clearSession();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-brand">{t("app.brand")}</span>
        <button type="button" className="btn-text" onClick={handleLogout}>
          {t("nav.signOut")}
        </button>
      </header>
      <ConnectivityBanner />
      <main className="app-main">
        <Outlet />
      </main>
      <nav className="bottom-nav" aria-label={t("nav.mainAria")}>
        <NavLink to="/app/my-day" className={({ isActive }) => (isActive ? "active" : "")}>
          {t("nav.myDay")}
        </NavLink>
        <NavLink to="/app/firms" className={({ isActive }) => (isActive ? "active" : "")}>
          {t("nav.customers")}
        </NavLink>
        {showCreateActivity && (
          <NavLink to={createActivityPath()} className={({ isActive }) => (isActive ? "active" : "")}>
            {t("nav.newActivity")}
          </NavLink>
        )}
      </nav>
    </div>
  );
}
