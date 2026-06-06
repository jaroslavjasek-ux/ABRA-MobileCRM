import { useOnlineStatus } from "@/hooks/useOnlineStatus";
import { useI18n } from "@/i18n";

export function ConnectivityBanner() {
  const online = useOnlineStatus();
  const { t } = useI18n();
  if (online) {
    return null;
  }
  return (
    <div className="connectivity-banner" role="status">
      {t("system.offlineBanner")}
    </div>
  );
}
