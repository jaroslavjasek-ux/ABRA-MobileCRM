import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { addActivityNote, completeActivity, getActivity, startActivity } from "@/api/activities";
import { queryKeys } from "@/api/queryKeys";
import { searchUsers } from "@/api/users";
import { useAuth } from "@/auth/AuthContext";
import {
  activityDetailPath,
  contactDetailPath,
  firmDetailPath,
} from "@/lib/navigation";
import { isUnauthorized, isServiceUnavailable, ApiError } from "@/lib/errors";
import { useI18n } from "@/i18n";
import { ActivityDocumentNumber } from "@/features/activities/ActivityDocumentNumber";
import {
  defaultFollowUpSchedule,
  followUpScheduleToIso,
  isFollowUpScheduleComplete,
} from "@/features/activities/followUpDefaults";

type LocationState = { from?: string; activityCreated?: boolean };

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
  const locationState = location.state as LocationState | null;
  const backTo = locationState?.from ?? "/app/my-day";
  const [showCreatedSuccess] = useState(() => Boolean(locationState?.activityCreated));
  const { t, formatScheduleRange, formatActivityStatus, formatDateTimeFull } = useI18n();
  const { representative } = useAuth();

  const [outcome, setOutcome] = useState("");
  const [scheduleFollowUp, setScheduleFollowUp] = useState(true);
  const [followUpSubject, setFollowUpSubject] = useState("");
  const [followUpDate, setFollowUpDate] = useState(() => defaultFollowUpSchedule().date);
  const [followUpTime, setFollowUpTime] = useState(() => defaultFollowUpSchedule().time);
  const [followUpAssignedUserId, setFollowUpAssignedUserId] = useState("");
  const [noteText, setNoteText] = useState("");
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [outcomeError, setOutcomeError] = useState<string | null>(null);
  const [followUpSubjectError, setFollowUpSubjectError] = useState<string | null>(null);
  const [followUpStartError, setFollowUpStartError] = useState<string | null>(null);
  const [followUpAssignedUserError, setFollowUpAssignedUserError] = useState<string | null>(null);
  const [noteError, setNoteError] = useState<string | null>(null);
  const [completeSuccess, setCompleteSuccess] = useState<{
    followUpScheduled: boolean;
    followUpWarning: string | null;
  } | null>(null);

  useEffect(() => {
    if (locationState?.activityCreated) {
      navigate(location.pathname, {
        replace: true,
        state: { from: locationState.from },
      });
    }
  }, [location.pathname, locationState, navigate]);

  const detailQuery = useQuery({
    queryKey: queryKeys.activityDetail(activityId ?? ""),
    queryFn: () => getActivity(activityId!),
    enabled: Boolean(activityId),
    staleTime: 0,
    refetchOnMount: "always",
  });

  const usersQuery = useQuery({
    queryKey: queryKeys.users(),
    queryFn: () => searchUsers(undefined, 50),
    staleTime: 60_000,
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
    mutationFn: (payload: Parameters<typeof completeActivity>[1]) =>
      completeActivity(activityId!, payload),
    onSuccess: (updated) => {
      setActionError(null);
      setOutcomeError(null);
      setFollowUpSubjectError(null);
      setFollowUpStartError(null);
      setOutcome("");
      setScheduleFollowUp(true);
      const followUpFailed = updated.warnings?.some((w) => w.code === "FOLLOW_UP_CREATE_FAILED");
      setCompleteSuccess({
        followUpScheduled: Boolean(updated.followUpActivity) && !followUpFailed,
        followUpWarning: followUpFailed
          ? (updated.warnings?.find((w) => w.code === "FOLLOW_UP_CREATE_FAILED")?.message ??
            t("activity.followUpCreateFailed"))
          : null,
      });
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

  useEffect(() => {
    if (data?.subject) {
      setFollowUpSubject((prev) => prev || data.subject);
    }
  }, [data?.subject]);

  useEffect(() => {
    if (representative?.id) {
      setFollowUpAssignedUserId((current) => current || representative.id);
    }
  }, [representative?.id]);

  const handleComplete = (e: FormEvent) => {
    e.preventDefault();
    setActionError(null);
    setCompleteSuccess(null);
    if (!outcome.trim()) {
      setOutcomeError(t("activity.outcomeRequired"));
      return;
    }
    setOutcomeError(null);

    if (scheduleFollowUp) {
      let followUpValid = true;
      if (!followUpSubject.trim()) {
        setFollowUpSubjectError(t("activity.followUpSubjectRequired"));
        followUpValid = false;
      } else {
        setFollowUpSubjectError(null);
      }
      if (!isFollowUpScheduleComplete(followUpDate, followUpTime)) {
        setFollowUpStartError(t("activity.followUpStartRequired"));
        followUpValid = false;
      } else {
        setFollowUpStartError(null);
      }
      if (!followUpAssignedUserId.trim()) {
        setFollowUpAssignedUserError(t("activity.followUpAssignedUserRequired"));
        followUpValid = false;
      } else {
        setFollowUpAssignedUserError(null);
      }
      if (!followUpValid) {
        return;
      }
    }

    completeMutation.mutate({
      answer: outcome.trim(),
      followUp: scheduleFollowUp
        ? {
            enabled: true,
            subject: followUpSubject.trim(),
            scheduledStart: followUpScheduleToIso(followUpDate, followUpTime),
            assignedUserId: followUpAssignedUserId.trim(),
          }
        : { enabled: false },
    });
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

          {showCreatedSuccess && (
            <section className="activity-complete-success" role="status">
              <p className="activity-complete-success-line">✓ {t("activity.createdSuccess")}</p>
            </section>
          )}

          <section className="detail-section detail-section--compact">
            <h2>{t("activity.schedule")}</h2>
            <p className="schedule-line">
              {formatScheduleRange(data.scheduledStart, data.scheduledEnd)}
            </p>
          </section>

          {data.ownerDisplayName && (
            <section className="detail-section detail-section--compact">
              <h2>{t("activity.assignedUser")}</h2>
              <p>{data.ownerDisplayName}</p>
            </section>
          )}

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
                <form className="form activity-note-form" onSubmit={handleAddNote}>
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

          {completeSuccess && terminal && (
            <section className="activity-complete-success" role="status">
              <p className="activity-complete-success-line">✓ {t("activity.completeSuccess")}</p>
              {completeSuccess.followUpScheduled && (
                <p className="activity-complete-success-line">
                  ✓ {t("activity.followUpScheduledSuccess")}
                </p>
              )}
              {completeSuccess.followUpWarning && (
                <p className="error activity-complete-success-warning" role="alert">
                  {completeSuccess.followUpWarning}
                </p>
              )}
            </section>
          )}

          {isActionableStatus(data.status) && data.canComplete && (
            <section className="activity-actions">
              <form className="form activity-complete-form" onSubmit={handleComplete}>
                <label className="field">
                  <span>
                    {scheduleFollowUp
                      ? t("activity.newOutcomeLabelHandover")
                      : t("activity.newOutcomeLabel")}
                  </span>
                  <textarea
                    rows={4}
                    value={outcome}
                    onChange={(e) => {
                      setOutcome(e.target.value);
                      if (outcomeError) {
                        setOutcomeError(null);
                      }
                    }}
                    placeholder={
                      scheduleFollowUp
                        ? t("activity.newOutcomePlaceholderHandover")
                        : t("activity.newOutcomePlaceholder")
                    }
                    disabled={busy}
                    required
                  />
                </label>
                {scheduleFollowUp && (
                  <p className="hint activity-outcome-handover-hint">
                    {t("activity.outcomeHandoverHint")}
                  </p>
                )}
                {outcomeError && (
                  <p className="error" role="alert">
                    {outcomeError}
                  </p>
                )}

                <label className="field field--checkbox">
                  <input
                    type="checkbox"
                    checked={scheduleFollowUp}
                    disabled={busy}
                    onChange={(e) => {
                      setScheduleFollowUp(e.target.checked);
                      setFollowUpSubjectError(null);
                      setFollowUpStartError(null);
                      setFollowUpAssignedUserError(null);
                    }}
                  />
                  <span>{t("activity.scheduleNextStep")}</span>
                </label>

                {scheduleFollowUp && (
                  <div className="activity-follow-up-fields">
                    <label className="field">
                      <span>{t("activity.followUpSubject")}</span>
                      <input
                        type="text"
                        value={followUpSubject}
                        onChange={(e) => {
                          setFollowUpSubject(e.target.value);
                          if (followUpSubjectError) {
                            setFollowUpSubjectError(null);
                          }
                        }}
                        placeholder={t("activity.followUpSubjectPlaceholder")}
                        disabled={busy}
                        required
                      />
                    </label>
                    {followUpSubjectError && (
                      <p className="error" role="alert">
                        {followUpSubjectError}
                      </p>
                    )}
                    <div className="field">
                      <span>{t("activity.followUpScheduledStart")}</span>
                      <div className="follow-up-schedule">
                        <input
                          type="date"
                          className="follow-up-schedule-date"
                          value={followUpDate}
                          onChange={(e) => {
                            setFollowUpDate(e.target.value);
                            if (followUpStartError) {
                              setFollowUpStartError(null);
                            }
                          }}
                          disabled={busy}
                          required
                        />
                        <input
                          type="time"
                          className="follow-up-schedule-time"
                          value={followUpTime}
                          step={60}
                          onChange={(e) => {
                            setFollowUpTime(e.target.value);
                            if (followUpStartError) {
                              setFollowUpStartError(null);
                            }
                          }}
                          disabled={busy}
                          required
                        />
                      </div>
                      {isFollowUpScheduleComplete(followUpDate, followUpTime) && (
                        <p className="follow-up-schedule-preview">
                          {formatDateTimeFull(followUpScheduleToIso(followUpDate, followUpTime))}
                        </p>
                      )}
                    </div>
                    {followUpStartError && (
                      <p className="error" role="alert">
                        {followUpStartError}
                      </p>
                    )}
                    <label className="field">
                      <span>{t("activity.followUpAssignedUser")}</span>
                      <select
                        value={followUpAssignedUserId}
                        onChange={(e) => {
                          setFollowUpAssignedUserId(e.target.value);
                          if (followUpAssignedUserError) {
                            setFollowUpAssignedUserError(null);
                          }
                        }}
                        disabled={busy || usersQuery.isLoading}
                        required
                      >
                        {!followUpAssignedUserId && (
                          <option value="">{t("loading.connecting")}</option>
                        )}
                        {(usersQuery.data?.items ?? []).map((user) => (
                          <option key={user.id} value={user.id}>
                            {user.displayName} ({user.loginName})
                          </option>
                        ))}
                        {followUpAssignedUserId &&
                          !(usersQuery.data?.items ?? []).some(
                            (user) => user.id === followUpAssignedUserId,
                          ) &&
                          representative && (
                            <option value={representative.id}>
                              {representative.displayName}
                            </option>
                          )}
                      </select>
                    </label>
                    {followUpAssignedUserError && (
                      <p className="error" role="alert">
                        {followUpAssignedUserError}
                      </p>
                    )}
                  </div>
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
      if (err.body?.details?.some((d) => d.field === "followUp.subject")) {
        return t("activity.followUpSubjectRequired");
      }
      if (err.body?.details?.some((d) => d.field === "followUp.scheduledStart")) {
        return t("activity.followUpStartRequired");
      }
      if (err.body?.details?.some((d) => d.field === "followUp.assignedUserId")) {
        return t("activity.followUpAssignedUserRequired");
      }
    }
    return err.message || t("activity.actionFailed");
  }
  return t("activity.actionFailed");
}
