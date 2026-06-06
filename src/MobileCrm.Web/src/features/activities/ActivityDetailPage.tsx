import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { completeActivity, getActivity, startActivity } from "@/api/activities";
import { queryKeys } from "@/api/queryKeys";
import {
  activityDetailPath,
  contactDetailPath,
  firmDetailPath,
} from "@/lib/navigation";
import { isUnauthorized, isServiceUnavailable, ApiError } from "@/lib/errors";
import { useI18n } from "@/i18n";
import { ActivityDocumentNumber } from "@/features/activities/ActivityDocumentNumber";

type LocationState = { from?: string };

function isTerminalStatus(status: string): boolean {
  return status === "completed" || status === "handedOver";
}

export function ActivityDetailPage() {
  const { activityId } = useParams<{ activityId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const backTo = (location.state as LocationState | null)?.from ?? "/app/my-day";
  const { t, formatScheduleRange, formatActivityStatus } = useI18n();

  const [outcome, setOutcome] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [outcomeError, setOutcomeError] = useState<string | null>(null);

  const detailQuery = useQuery({
    queryKey: queryKeys.activityDetail(activityId ?? ""),
    queryFn: () => getActivity(activityId!),
    enabled: Boolean(activityId),
  });

  const invalidateRelated = (firmId?: string) => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.myDay() });
    if (activityId) {
      void queryClient.invalidateQueries({ queryKey: queryKeys.activityDetail(activityId) });
    }
    if (firmId) {
      void queryClient.invalidateQueries({ queryKey: queryKeys.firmDetail(firmId) });
    }
  };

  const startMutation = useMutation({
    mutationFn: () => startActivity(activityId!),
    onSuccess: (updated) => {
      setActionError(null);
      queryClient.setQueryData(queryKeys.activityDetail(activityId!), updated);
      invalidateRelated(updated.firm?.id);
    },
    onError: (err) => setActionError(resolveActionError(err, t)),
  });

  const completeMutation = useMutation({
    mutationFn: () =>
      completeActivity(activityId!, {
        answer: outcome.trim(),
      }),
    onSuccess: (updated) => {
      setActionError(null);
      setOutcomeError(null);
      setOutcome("");
      queryClient.setQueryData(queryKeys.activityDetail(activityId!), updated);
      invalidateRelated(updated.firm?.id);
    },
    onError: (err) => setActionError(resolveActionError(err, t)),
  });

  if (detailQuery.isError) {
    const err = detailQuery.error;
    if (isUnauthorized(err)) {
      navigate("/app/session-expired", { replace: true });
    } else if (isServiceUnavailable(err)) {
      navigate("/app/connection-error", {
        replace: true,
        state: { from: activityId ? activityDetailPath(activityId) : "/app/my-day" },
      });
    }
  }

  const notFound =
    detailQuery.isError &&
    detailQuery.error instanceof ApiError &&
    detailQuery.error.status === 404;

  const data = detailQuery.data;
  const backLabel = backTo.includes("/firms/")
    ? t("activity.backCustomer")
    : t("activity.backMyDay");
  const terminal = data ? isTerminalStatus(data.status) : false;
  const busy = startMutation.isPending || completeMutation.isPending;

  const handleComplete = (e: FormEvent) => {
    e.preventDefault();
    setActionError(null);
    if (!outcome.trim()) {
      setOutcomeError(t("activity.outcomeRequired"));
      return;
    }
    setOutcomeError(null);
    completeMutation.mutate();
  };

  return (
    <div className="activity-detail-page page--compact">
      <header className="page-toolbar">
        <button type="button" className="btn-back" onClick={() => navigate(backTo)}>
          {backLabel}
        </button>
        <button
          type="button"
          className="btn-secondary btn-secondary--small"
          onClick={() => void detailQuery.refetch()}
          disabled={detailQuery.isFetching || busy}
        >
          {t("common.refresh")}
        </button>
      </header>

      {detailQuery.isLoading && <p className="loading">{t("loading.activity")}</p>}
      {notFound && <p className="error">{t("activity.notFound")}</p>}

      {data && (
        <>
          <div className="detail-hero detail-hero--compact">
            <p className="activity-type-line">
              {data.activityTypeName ?? data.activityTypeId ?? t("activity.defaultType")}
            </p>
            <ActivityDocumentNumber
              documentNumber={data.documentNumber}
              className="activity-doc-number activity-doc-number--hero"
            />
            <h1>{data.subject}</h1>
            <span className={`badge status-${data.status}`}>
              {formatActivityStatus(data.status)}
            </span>
          </div>

          <section className="detail-section detail-section--compact">
            <h2>{t("activity.schedule")}</h2>
            <p className="schedule-line">
              {formatScheduleRange(data.scheduledStart, data.scheduledEnd)}
            </p>
          </section>

          {data.firm?.id && (
            <section className="detail-section detail-section--compact">
              <h2>{t("activity.customer")}</h2>
              <Link to={firmDetailPath(data.firm.id)} className="entity-card">
                <strong>{data.firm.name}</strong>
                {(data.firm.businessRegistrationNumber || data.firm.code) && (
                  <span className="muted entity-card-meta">
                    {[
                      data.firm.businessRegistrationNumber &&
                        t("firms.meta.icoCode", {
                          value: data.firm.businessRegistrationNumber,
                        }),
                      data.firm.code && t("firms.meta.code", { value: data.firm.code }),
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </span>
                )}
              </Link>
            </section>
          )}

          {data.contact && (
            <section className="detail-section detail-section--compact">
              <h2>{t("activity.contact")}</h2>
              <Link
                to={contactDetailPath(data.contact.id, data.firm?.id)}
                className="entity-card"
              >
                <strong>{data.contact.displayName}</strong>
                {data.contact.jobTitle && (
                  <span className="muted entity-card-meta">{data.contact.jobTitle}</span>
                )}
              </Link>
            </section>
          )}

          {terminal && (
            <section className="detail-section detail-section--compact">
              <h2>{t("activity.storedOutcome")}</h2>
              {data.answer ? (
                <p className="note-body">{data.answer}</p>
              ) : (
                <p className="hint">{t("activity.noNotes")}</p>
              )}
              {data.description && (
                <div className="note-block">
                  <h3 className="note-label">{t("activity.description")}</h3>
                  <p className="note-body">{data.description}</p>
                </div>
              )}
            </section>
          )}

          {!terminal && (data.description || (data.answer && !data.canComplete)) && (
            <section className="detail-section detail-section--compact">
              <h2>{t("activity.notes")}</h2>
              {data.description && (
                <div className="note-block">
                  <h3 className="note-label">{t("activity.description")}</h3>
                  <p className="note-body">{data.description}</p>
                </div>
              )}
              {data.answer && !data.canComplete && (
                <div className="note-block">
                  <h3 className="note-label">{t("activity.outcome")}</h3>
                  <p className="note-body">{data.answer}</p>
                </div>
              )}
            </section>
          )}

          {!terminal && !data.description && !data.answer && !data.canComplete && (
            <p className="hint">{t("activity.noNotes")}</p>
          )}

          {actionError && (
            <p className="error activity-action-error" role="alert">
              {actionError}
            </p>
          )}

          {data.canEdit && (
            <section className="activity-actions">
              <button
                type="button"
                className="btn-primary"
                disabled={busy}
                onClick={() => startMutation.mutate()}
              >
                {startMutation.isPending ? t("activity.startingWork") : t("activity.startWork")}
              </button>
            </section>
          )}

          {data.canComplete && (
            <section className="activity-actions">
              <form className="activity-complete-form" onSubmit={handleComplete}>
                {data.answer && (
                  <div className="note-block activity-previous-notes">
                    <h3 className="note-label">{t("activity.previousNotes")}</h3>
                    <p className="note-body note-body--readonly">{data.answer}</p>
                  </div>
                )}
                <label className="field">
                  <span>{t("activity.newOutcomeLabel")}</span>
                  <textarea
                    rows={4}
                    value={outcome}
                    onChange={(e) => {
                      setOutcome(e.target.value);
                      if (outcomeError) {
                        setOutcomeError(null);
                      }
                    }}
                    placeholder={t("activity.newOutcomePlaceholder")}
                    disabled={busy}
                    required
                  />
                </label>
                {outcomeError && (
                  <p className="error" role="alert">
                    {outcomeError}
                  </p>
                )}
                <button type="submit" className="btn-primary" disabled={busy}>
                  {completeMutation.isPending ? t("activity.completing") : t("activity.complete")}
                </button>
              </form>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function resolveActionError(
  err: unknown,
  t: (key: string) => string,
): string {
  if (err instanceof ApiError) {
    if (err.code === "NOT_EDITABLE" || err.status === 409) {
      return t("activity.notEditable");
    }
    if (err.code === "VALIDATION_FAILED") {
      const fieldAnswer = err.body?.details?.find((d) => d.field === "answer");
      if (fieldAnswer) {
        return t("activity.outcomeRequired");
      }
    }
    return err.message || t("activity.actionFailed");
  }
  return t("activity.actionFailed");
}
