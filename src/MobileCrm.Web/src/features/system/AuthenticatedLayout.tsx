import { NavLink, Outlet } from "react-router-dom";
import { ConnectivityBanner } from "@/features/system/ConnectivityBanner";
import { useAuth } from "@/auth/AuthContext";
import { deleteSession } from "@/api/session";
import { useNavigate } from "react-router-dom";
import { useI18n } from "@/i18n";

export function AuthenticatedLayout() {
  const { clearSession } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();

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
      </nav>
    </div>
  );
}
