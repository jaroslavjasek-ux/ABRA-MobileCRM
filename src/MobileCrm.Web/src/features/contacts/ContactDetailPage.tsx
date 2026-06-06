import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getContact } from "@/api/contacts";
import { queryKeys } from "@/api/queryKeys";
import { ContactReachSection } from "@/features/contacts/ContactReachSection";
import { firmDetailPath } from "@/lib/navigation";
import { isUnauthorized, isServiceUnavailable, ApiError } from "@/lib/errors";
import { useI18n } from "@/i18n";

export function ContactDetailPage() {
  const { contactId } = useParams<{ contactId: string }>();
  const [searchParams] = useSearchParams();
  const firmId = searchParams.get("firmId") ?? undefined;
  const navigate = useNavigate();
  const { t } = useI18n();

  const detailQuery = useQuery({
    queryKey: queryKeys.contactDetail(contactId ?? "", firmId),
    queryFn: () => getContact(contactId!, firmId),
    enabled: Boolean(contactId),
  });

  if (detailQuery.isError) {
    const err = detailQuery.error;
    if (isUnauthorized(err)) {
      navigate("/app/session-expired", { replace: true });
    } else if (isServiceUnavailable(err)) {
      navigate("/app/connection-error", {
        replace: true,
        state: { from: `/app/contacts/${contactId}` },
      });
    }
  }

  const notFound =
    detailQuery.isError &&
    detailQuery.error instanceof ApiError &&
    detailQuery.error.status === 404;

  const data = detailQuery.data;
  const backTo = firmId ? firmDetailPath(firmId) : "/app/firms";

  return (
    <div className="contact-detail-page page--compact">
      <header className="page-toolbar">
        <button type="button" className="btn-back" onClick={() => navigate(backTo)}>
          {t("common.back")}
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

      {detailQuery.isLoading && <p className="loading">{t("loading.contact")}</p>}
      {notFound && <p className="error">{t("contact.notFound")}</p>}

      {data && (
        <>
          <div className="detail-hero detail-hero--compact">
            <h1>{data.displayName}</h1>
            {data.isPrimary && (
              <span className="badge badge-primary">{t("contact.mainContact")}</span>
            )}
          </div>

          {data.jobTitle && <p className="contact-role">{data.jobTitle}</p>}

          {data.firmId && data.firmName && (
            <p className="contact-firm-link">
              <span className="contact-firm-label">{t("contact.customerLabel")} </span>
              <Link to={firmDetailPath(data.firmId)}>{data.firmName}</Link>
            </p>
          )}

          <ContactReachSection address={data.address} />

          {data.notes && (
            <section className="detail-section detail-section--compact">
              <h2>{t("contact.notes")}</h2>
              <p className="notes-body">{data.notes}</p>
            </section>
          )}
        </>
      )}
    </div>
  );
}
