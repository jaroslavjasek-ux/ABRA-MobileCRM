import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { getFirmDetail } from "@/api/firms";
import { queryKeys } from "@/api/queryKeys";
import type { CommercialHealth } from "@/api/types";
import { FirmActivitiesSection } from "@/features/firms/FirmActivitiesSection";
import { ContactCard } from "@/features/firms/ContactCard";
import { FirmReachSection } from "@/features/firms/FirmReachSection";
import { KvGrid } from "@/features/firms/KvGrid";
import { backFromFirmDetail } from "@/lib/navigation";
import { isUnauthorized, isServiceUnavailable, ApiError } from "@/lib/errors";
import { useI18n } from "@/i18n";

function CommercialHealthSection({
  health,
  title,
}: {
  health: CommercialHealth;
  title: string;
}) {
  return (
    <section className="detail-section detail-section--compact">
      <h2>{title}</h2>
      {health.statusLine && <p>{health.statusLine}</p>}
      {health.guidanceText && <p className="muted">{health.guidanceText}</p>}
    </section>
  );
}

export function FirmDetailPage() {
  const { firmId } = useParams<{ firmId: string }>();
  const navigate = useNavigate();
  const { t, formatCommercialStatus } = useI18n();

  const detailQuery = useQuery({
    queryKey: queryKeys.firmDetail(firmId ?? ""),
    queryFn: () => getFirmDetail(firmId!),
    enabled: Boolean(firmId),
  });

  if (detailQuery.isError) {
    const err = detailQuery.error;
    if (isUnauthorized(err)) {
      navigate("/app/session-expired", { replace: true });
    } else if (isServiceUnavailable(err)) {
      navigate("/app/connection-error", {
        replace: true,
        state: { from: `/app/firms/${firmId}` },
      });
    }
  }

  const notFound =
    detailQuery.isError &&
    detailQuery.error instanceof ApiError &&
    detailQuery.error.status === 404;

  const data = detailQuery.data;

  const companyRows = data
    ? [
        data.businessRegistrationNumber
          ? { label: t("firms.labels.ico"), value: data.businessRegistrationNumber }
          : null,
        data.taxNumber ? { label: t("firms.labels.dic"), value: data.taxNumber } : null,
        data.code ? { label: t("firms.labels.customerCode"), value: data.code } : null,
      ].filter((row): row is { label: string; value: string } => row !== null)
    : [];

  const primary = data?.contacts.find((c) => c.isPrimary);
  const otherContacts = data?.contacts.filter((c) => !c.isPrimary) ?? [];

  return (
    <div className="firm-detail-page page--compact">
      <header className="page-toolbar">
        <button type="button" className="btn-back" onClick={() => navigate(backFromFirmDetail())}>
          {t("firms.backCustomers")}
        </button>
        <button
          type="button"
          className="btn-secondary btn-secondary--small"
          onClick={() => void detailQuery.refetch()}
          disabled={detailQuery.isFetching}
        >
          {t("common.refresh")}
        </button>
      </header>

      {detailQuery.isLoading && <p className="loading">{t("loading.customer")}</p>}
      {notFound && <p className="error">{t("firms.notFound")}</p>}

      {data && (
        <>
          <div className="detail-hero detail-hero--compact">
            <h1>{data.name}</h1>
            {data.commercialStatus && (
              <span className={`badge status-${data.commercialStatus}`}>
                {formatCommercialStatus(data.commercialStatus)}
              </span>
            )}
          </div>

          {companyRows.length > 0 && (
            <section className="detail-section detail-section--compact">
              <h2>{t("firms.companyDetails")}</h2>
              <KvGrid rows={companyRows} />
            </section>
          )}

          <FirmReachSection
            mainAddress={data.mainAddress}
            electronicAddress={data.electronicAddress}
            website={data.website}
          />

          <FirmActivitiesSection activities={data.recentActivities} firmId={data.id} />

          <section className="detail-section detail-section--compact">
            <h2>{t("firms.people")}</h2>
            {data.contacts.length === 0 ? (
              <p className="empty">{t("firms.noContacts")}</p>
            ) : (
              <ul className="contact-list">
                {primary && <ContactCard contact={primary} firmId={data.id} />}
                {otherContacts.map((c) => (
                  <ContactCard key={c.id} contact={c} firmId={data.id} />
                ))}
              </ul>
            )}
          </section>

          {data.commercialHealth && (
            <CommercialHealthSection
              health={data.commercialHealth}
              title={t("firms.commercialHealth")}
            />
          )}

          <p className="phase-note">{t("common.pipelineLater")}</p>
        </>
      )}
    </div>
  );
}
