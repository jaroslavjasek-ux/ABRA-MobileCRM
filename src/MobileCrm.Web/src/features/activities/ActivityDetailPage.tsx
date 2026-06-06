import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { addActivityNote, completeActivity, getActivity, startActivity } from "@/api/activities";
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
  return status === "completed" || status === "handedOver" || status === "unknown";
}

function isActionableStatus(status: string): boolean {
  return status === "open" || status === "inProgress";
}

export function ActivityDetailPage() {
  const { activityId } = useParams<{ activityId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const backTo = (location.state as LocationState | null)?.from ?? "/app/my-day";
  const { t, formatScheduleRange, formatActivityStatus } = useI18n();

  const [outcome, setOutcome] = useState("");
  const [noteText, setNoteText] = useState("");
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [outcomeError, setOutcomeError] = useState<string | null>(null);
  const [noteError, setNoteError] = useState<string | null>(null);

  const detailQuery = useQuery({
    queryKey: queryKeys.activityDetail(activityId ?? ""),
    queryFn: () => getActivity(activityId!),
    enabled: Boolean(activityId),
    staleTime: 0,
    refetchOnMount: "always",
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

  const noteMutation = useMutation({
    mutationFn: () => addActivityNote(activityId!, { note: noteText.trim() }),
    onSuccess: (updated) => {
      setActionError(null);
      setNoteError(null);
      setNoteText("");
      setShowNoteForm(false);
      queryClient.setQueryData(queryKeys.activityDetail(activityId!), updated);
      invalidateRelated(updated.firm?.id);
    },
    onError: (err) => setActionError(resolveActionError(err, t, "note")),
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
  const busy = startMutation.isPending || completeMutation.isPending || noteMutation.isPending;

  const handleAddNote = (e: FormEvent) => {
    e.preventDefault();
    setActionError(null);
    if (!noteText.trim()) {
      setNoteError(t("activity.noteRequired"));
      return;
    }
    setNoteError(null);
    noteMutation.mutate();
  };

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

          {!terminal && (data.description || data.answer) && (
            <section className="detail-section detail-section--compact">
              <h2>{t("activity.notes")}</h2>
              {data.description && (
                <div className="note-block">
                  <h3 className="note-label">{t("activity.description")}</h3>
                  <p className="note-body">{data.description}</p>
                </div>
              )}
              {data.answer && (
                <div className="note-block">
                  <h3 className="note-label">{t("activity.outcome")}</h3>
                  <p className="note-body note-body--readonly">{data.answer}</p>
                </div>
              )}
            </section>
          )}

          {!terminal && !data.description && !data.answer && (
            <p className="hint">{t("activity.noNotes")}</p>
          )}

          {isActionableStatus(data.status) && data.canAddNote && (
            <section className="activity-actions">
              {!showNoteForm ? (
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={busy}
                  onClick={() => {
                    setShowNoteForm(true);
                    setActionError(null);
                    setNoteError(null);
                  }}
                >
                  {t("activity.addNote")}
                </button>
              ) : (
                <form className="activity-note-form" onSubmit={handleAddNote}>
                  <label className="field">
                    <span>{t("activity.noteLabel")}</span>
                    <textarea
                      rows={4}
                      value={noteText}
                      onChange={(e) => {
                        setNoteText(e.target.value);
                        if (noteError) {
                          setNoteError(null);
                        }
                      }}
                      placeholder={t("activity.notePlaceholder")}
                      disabled={busy}
                      required
                    />
                  </label>
                  {noteError && (
                    <p className="error" role="alert">
                      {noteError}
                    </p>
                  )}
                  <div className="activity-note-form-actions">
                    <button type="submit" className="btn-primary" disabled={busy}>
                      {noteMutation.isPending ? t("activity.savingNote") : t("activity.saveNote")}
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={busy}
                      onClick={() => {
                        setShowNoteForm(false);
                        setNoteText("");
                        setNoteError(null);
                      }}
                    >
                      {t("activity.cancelNote")}
                    </button>
                  </div>
                </form>
              )}
            </section>
          )}

          {actionError && (
            <p className="error activity-action-error" role="alert">
              {actionError}
            </p>
          )}

          {isActionableStatus(data.status) && data.canEdit && (
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

          {isActionableStatus(data.status) && data.canComplete && (
            <section className="activity-actions">
              <form className="activity-complete-form" onSubmit={handleComplete}>
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
  field?: "answer" | "note",
): string {
  if (err instanceof ApiError) {
    if (err.code === "NOT_EDITABLE" || err.status === 409) {
      return t("activity.notEditable");
    }
    if (err.code === "VALIDATION_FAILED") {
      const fieldAnswer = err.body?.details?.find((d) => d.field === "answer");
      if (fieldAnswer || field === "answer") {
        return t("activity.outcomeRequired");
      }
      const fieldNote = err.body?.details?.find((d) => d.field === "note");
      if (fieldNote || field === "note") {
        return t("activity.noteRequired");
      }
    }
    return err.message || t("activity.actionFailed");
  }
  return t("activity.actionFailed");
}
