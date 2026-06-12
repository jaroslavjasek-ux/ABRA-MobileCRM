import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { createStandaloneActivity } from "@/api/activities";
import {
  searchActivityAreas,
  searchActivityQueues,
  searchActivityTypes,
} from "@/api/classification";
import {
  searchBusinessCases,
  searchProjects,
  searchWorkOrders,
} from "@/api/dimensions";
import { getFirmDetail, searchFirms } from "@/api/firms";
import { getSession } from "@/api/session";
import { searchUsers } from "@/api/users";
import { queryKeys } from "@/api/queryKeys";
import { useAuth } from "@/auth/AuthContext";
import type { FirmSummary } from "@/api/types";
import {
  defaultFollowUpSchedule,
  followUpScheduleToIso,
  isFollowUpScheduleComplete,
} from "@/features/activities/followUpDefaults";
import { CatalogSelectField } from "@/components/CatalogSelectField";
import { useAbraCatalogSelector } from "@/hooks/useAbraCatalogSelector";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { ApiError, isServiceUnavailable, isUnauthorized } from "@/lib/errors";
import { activityDetailPath } from "@/lib/navigation";
import { useI18n } from "@/i18n";

export function CreateActivityPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { representative } = useAuth();
  const { t, formatDateTimeFull } = useI18n();

  const sessionQuery = useQuery({
    queryKey: queryKeys.session,
    queryFn: getSession,
  });

  const [subject, setSubject] = useState("");
  const [firmQuery, setFirmQuery] = useState("");
  const [selectedFirm, setSelectedFirm] = useState<FirmSummary | null>(null);
  const [contactPersonId, setContactPersonId] = useState("");
  const [scheduleDate, setScheduleDate] = useState(() => defaultFollowUpSchedule().date);
  const [scheduleTime, setScheduleTime] = useState(() => defaultFollowUpSchedule().time);
  const [description, setDescription] = useState("");
  const [assignedUserId, setAssignedUserId] = useState("");
  const [businessCaseId, setBusinessCaseId] = useState("");
  const [workOrderId, setWorkOrderId] = useState("");
  const [projectId, setProjectId] = useState("");

  const [subjectError, setSubjectError] = useState<string | null>(null);
  const [firmError, setFirmError] = useState<string | null>(null);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [assignedUserError, setAssignedUserError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [activityTypeError, setActivityTypeError] = useState<string | null>(null);
  const [activityQueueError, setActivityQueueError] = useState<string | null>(null);

  const debouncedFirmQ = useDebouncedValue(firmQuery.trim(), 300);
  const canSearchFirms = debouncedFirmQ.length >= 2 && !selectedFirm;

  const firmSearchQuery = useQuery({
    queryKey: queryKeys.firmsSearch(debouncedFirmQ, 10),
    queryFn: () => searchFirms(debouncedFirmQ, 10, 0),
    enabled: canSearchFirms,
  });

  const firmDetailQuery = useQuery({
    queryKey: queryKeys.firmDetail(selectedFirm?.id ?? ""),
    queryFn: () => getFirmDetail(selectedFirm!.id, 0),
    enabled: Boolean(selectedFirm?.id),
  });

  const usersQuery = useQuery({
    queryKey: queryKeys.users(),
    queryFn: () => searchUsers(undefined, 50),
    staleTime: 60_000,
  });

  const dimensionFlags = sessionQuery.data?.activityFeatures?.dimensions;
  const showBusinessCase = dimensionFlags?.businessCase ?? false;
  const showWorkOrder = dimensionFlags?.workOrder ?? false;
  const showProject = dimensionFlags?.project ?? false;
  const showDimensionsSection = showBusinessCase || showWorkOrder || showProject;
  const firmIdForDimensions = selectedFirm?.id;

  const businessCasesQuery = useQuery({
    queryKey: queryKeys.businessCases(firmIdForDimensions),
    queryFn: () => searchBusinessCases(undefined, firmIdForDimensions, 50),
    enabled: showBusinessCase && Boolean(firmIdForDimensions),
    staleTime: 60_000,
  });

  const workOrdersQuery = useQuery({
    queryKey: queryKeys.workOrders(firmIdForDimensions),
    queryFn: () => searchWorkOrders(undefined, firmIdForDimensions, 50),
    enabled: showWorkOrder && Boolean(firmIdForDimensions),
    staleTime: 60_000,
  });

  const projectsQuery = useQuery({
    queryKey: queryKeys.projects(firmIdForDimensions),
    queryFn: () => searchProjects(undefined, firmIdForDimensions, 50),
    enabled: showProject && Boolean(firmIdForDimensions),
    staleTime: 60_000,
  });

  const classificationFlags = sessionQuery.data?.activityFeatures?.classification;
  const showActivityArea = classificationFlags?.area ?? false;
  const showActivityType = classificationFlags?.type ?? false;
  const showActivityQueue = classificationFlags?.queue ?? false;
  const autoHideSingleValue = classificationFlags?.autoHideSingleValue ?? true;
  const showClassificationSection =
    showActivityArea || showActivityType || showActivityQueue;

  const areaSelector = useAbraCatalogSelector({
    enabled: showActivityArea,
    required: false,
    autoHideSingleValue,
    queryKey: queryKeys.activityAreas(),
    queryFn: () => searchActivityAreas(undefined, 50),
  });

  const resolvedAreaId = showActivityArea ? areaSelector.value.trim() : "";
  const areaReady = !showActivityArea || Boolean(resolvedAreaId);

  const typeSelector = useAbraCatalogSelector({
    enabled: showActivityType && Boolean(selectedFirm) && areaReady,
    required: true,
    autoHideSingleValue,
    parentKey: resolvedAreaId,
    queryKey: queryKeys.activityTypes(resolvedAreaId || undefined),
    queryFn: () => searchActivityTypes(undefined, resolvedAreaId || undefined, 50),
  });

  const resolvedTypeId = typeSelector.value.trim();
  const typeReady = typeSelector.isReady && !typeSelector.isConfigurationError;

  const queueSelector = useAbraCatalogSelector({
    enabled: showActivityQueue && Boolean(selectedFirm) && areaReady && Boolean(resolvedTypeId) && typeReady,
    required: true,
    autoHideSingleValue,
    parentKey: `${resolvedAreaId}:${resolvedTypeId}`,
    queryKey: queryKeys.activityQueues(resolvedAreaId || undefined, resolvedTypeId || undefined),
    queryFn: () =>
      searchActivityQueues(undefined, resolvedAreaId || undefined, resolvedTypeId || undefined, 50),
  });

  const classificationConfigurationError =
    (showActivityArea && areaSelector.isConfigurationError)
    || (showActivityType && areaReady && typeSelector.isConfigurationError)
    || (showActivityQueue && typeReady && Boolean(resolvedTypeId) && queueSelector.isConfigurationError);

  useEffect(() => {
    const repId =
      representative?.id ?? sessionQuery.data?.representative.id ?? "";
    if (repId) {
      setAssignedUserId((current) => current || repId);
    }
  }, [representative?.id, sessionQuery.data?.representative.id]);

  useEffect(() => {
    if (sessionQuery.isSuccess && !sessionQuery.data.activityFeatures?.createActivity) {
      navigate("/app/my-day", { replace: true });
    }
  }, [sessionQuery.isSuccess, sessionQuery.data, navigate]);

  useEffect(() => {
    if (!sessionQuery.isError) {
      return;
    }
    const err = sessionQuery.error;
    if (isUnauthorized(err)) {
      navigate("/app/session-expired", { replace: true });
    } else if (isServiceUnavailable(err)) {
      navigate("/app/connection-error", {
        replace: true,
        state: { from: "/app/activities/new" },
      });
    }
  }, [sessionQuery.isError, sessionQuery.error, navigate]);

  const createMutation = useMutation({
    mutationFn: createStandaloneActivity,
    onSuccess: async (created) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.myDay() });
      navigate(activityDetailPath(created.id), {
        replace: true,
        state: { activityCreated: true, from: "/app/activities/new" },
      });
    },
    onError: (err) => {
      if (isUnauthorized(err)) {
        navigate("/app/session-expired", { replace: true });
        return;
      }
      if (isServiceUnavailable(err)) {
        navigate("/app/connection-error", {
          replace: true,
          state: { from: "/app/activities/new" },
        });
        return;
      }
      if (err instanceof ApiError && err.code === "CLASSIFICATION_INVALID") {
        setFormError(t("createActivity.classificationInvalid"));
        return;
      }
      if (err instanceof ApiError && err.body?.details?.length) {
        let hasFieldError = false;
        for (const detail of err.body.details) {
          const field = detail.field.toLowerCase();
          if (field === "subject") {
            setSubjectError(detail.message);
            hasFieldError = true;
          } else if (field === "firmid") {
            setFirmError(detail.message);
            hasFieldError = true;
          } else if (field === "scheduledstart") {
            setScheduleError(detail.message);
            hasFieldError = true;
          } else if (field === "assigneduserid") {
            setAssignedUserError(detail.message);
            hasFieldError = true;
          } else if (field === "activitytypeid") {
            setActivityTypeError(detail.message);
            hasFieldError = true;
          } else if (field === "actqueueid") {
            setActivityQueueError(detail.message);
            hasFieldError = true;
          }
        }
        if (!hasFieldError) {
          setFormError(err.message);
        }
        return;
      }
      setFormError(err instanceof Error ? err.message : t("createActivity.failed"));
    },
  });

  const handleSelectFirm = (firm: FirmSummary) => {
    setSelectedFirm(firm);
    setFirmQuery(firm.name);
    setFirmError(null);
    setContactPersonId("");
    setBusinessCaseId("");
    setWorkOrderId("");
    setProjectId("");
  };

  const handleClearFirm = () => {
    setSelectedFirm(null);
    setFirmQuery("");
    setContactPersonId("");
    setBusinessCaseId("");
    setWorkOrderId("");
    setProjectId("");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubjectError(null);
    setFirmError(null);
    setScheduleError(null);
    setAssignedUserError(null);
    setActivityTypeError(null);
    setActivityQueueError(null);

    let valid = true;
    if (!subject.trim()) {
      setSubjectError(t("createActivity.subjectRequired"));
      valid = false;
    }
    if (!selectedFirm) {
      setFirmError(t("createActivity.firmRequired"));
      valid = false;
    }
    if (!isFollowUpScheduleComplete(scheduleDate, scheduleTime)) {
      setScheduleError(t("createActivity.scheduleRequired"));
      valid = false;
    }
    if (!assignedUserId.trim()) {
      setAssignedUserError(t("createActivity.assignedUserRequired"));
      valid = false;
    }
    if (showActivityArea && areaSelector.isConfigurationError) {
      setFormError(t("createActivity.classificationConfigurationError"));
      valid = false;
    } else if (showActivityType && areaReady && typeSelector.isConfigurationError) {
      setFormError(t("createActivity.classificationNoTypesForArea"));
      valid = false;
    } else if (
      showActivityQueue
      && typeReady
      && Boolean(resolvedTypeId)
      && queueSelector.isConfigurationError
    ) {
      setFormError(t("createActivity.classificationNoQueuesForAreaType"));
      valid = false;
    }
    if (showActivityType && typeSelector.isSelectionMissing) {
      setActivityTypeError(t("createActivity.activityTypeRequired"));
      valid = false;
    }
    if (showActivityQueue && queueSelector.isSelectionMissing) {
      setActivityQueueError(t("createActivity.activityQueueRequired"));
      valid = false;
    }
    if (!valid) {
      return;
    }

    createMutation.mutate({
      subject: subject.trim(),
      scheduledStart: followUpScheduleToIso(scheduleDate, scheduleTime),
      firmId: selectedFirm!.id,
      contactPersonId: contactPersonId.trim() || undefined,
      description: description.trim() || undefined,
      assignedUserId: assignedUserId.trim(),
      businessCaseId: businessCaseId.trim() || undefined,
      workOrderId: workOrderId.trim() || undefined,
      projectId: projectId.trim() || undefined,
      activityAreaId: showActivityArea ? areaSelector.value.trim() || undefined : undefined,
      activityTypeId: showActivityType ? typeSelector.value.trim() || undefined : undefined,
      actQueueId: showActivityQueue ? queueSelector.value.trim() || undefined : undefined,
    });
  };

  const firmResults = firmSearchQuery.data?.items ?? [];
  const contacts = firmDetailQuery.data?.contacts ?? [];
  const busy = createMutation.isPending;

  return (
    <div className="create-activity-page page--compact">
      <header className="page-toolbar page-toolbar--title">
        <h1>{t("createActivity.title")}</h1>
      </header>

      <form className="form create-activity-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>{t("createActivity.subject")} *</span>
          <input
            type="text"
            value={subject}
            onChange={(e) => {
              setSubject(e.target.value);
              if (subjectError) {
                setSubjectError(null);
              }
            }}
            placeholder={t("createActivity.subjectPlaceholder")}
            disabled={busy}
            required
          />
        </label>
        {subjectError && (
          <p className="error" role="alert">
            {subjectError}
          </p>
        )}

        <div className="field">
          <span>{t("createActivity.firm")} *</span>
          <input
            type="search"
            value={firmQuery}
            onChange={(e) => {
              setFirmQuery(e.target.value);
              if (selectedFirm && e.target.value !== selectedFirm.name) {
                setSelectedFirm(null);
                setContactPersonId("");
              }
              if (firmError) {
                setFirmError(null);
              }
            }}
            placeholder={t("createActivity.firmPlaceholder")}
            disabled={busy}
            aria-label={t("createActivity.firmSearchAria")}
          />
          {selectedFirm && (
            <button
              type="button"
              className="btn-clear create-activity-clear-firm"
              onClick={handleClearFirm}
              disabled={busy}
            >
              {t("common.clear")}
            </button>
          )}
        </div>
        {firmError && (
          <p className="error" role="alert">
            {firmError}
          </p>
        )}
        {canSearchFirms && !selectedFirm && (
          <div className="create-activity-firm-results">
            {firmSearchQuery.isLoading && <p className="hint">{t("createActivity.searchingFirms")}</p>}
            {firmSearchQuery.isSuccess && firmResults.length === 0 && (
              <p className="hint">{t("firms.empty")}</p>
            )}
            {firmResults.length > 0 && (
              <ul className="create-activity-firm-list">
                {firmResults.map((firm) => (
                  <li key={firm.id}>
                    <button
                      type="button"
                      className="list-card firm-card create-activity-firm-option"
                      onClick={() => handleSelectFirm(firm)}
                      disabled={busy}
                    >
                      <strong className="firm-card-name">{firm.name}</strong>
                      {firm.city && <span className="muted">{firm.city}</span>}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
        {!selectedFirm && firmQuery.trim().length > 0 && firmQuery.trim().length < 2 && (
          <p className="hint">{t("firms.hintMinChars")}</p>
        )}

        {selectedFirm && contacts.length > 0 && (
          <label className="field">
            <span>{t("createActivity.contact")}</span>
            <select
              value={contactPersonId}
              onChange={(e) => setContactPersonId(e.target.value)}
              disabled={busy || firmDetailQuery.isLoading}
            >
              <option value="">{t("createActivity.contactNone")}</option>
              {contacts.map((contact) => (
                <option key={contact.id} value={contact.id}>
                  {contact.displayName}
                  {contact.jobTitle ? ` — ${contact.jobTitle}` : ""}
                </option>
              ))}
            </select>
          </label>
        )}

        {selectedFirm && showDimensionsSection && (
          <section className="form-section" aria-labelledby="create-activity-dimensions-title">
            <h2 id="create-activity-dimensions-title" className="form-section__title">
              {t("createActivity.dimensionsSection")}
            </h2>

            {showBusinessCase && (
              <label className="field">
                <span>{t("createActivity.businessCase")}</span>
                <select
                  value={businessCaseId}
                  onChange={(e) => setBusinessCaseId(e.target.value)}
                  disabled={busy || businessCasesQuery.isLoading}
                >
                  <option value="">{t("createActivity.dimensionNone")}</option>
                  {(businessCasesQuery.data?.items ?? []).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.displayName}
                    </option>
                  ))}
                </select>
                {businessCasesQuery.isLoading && (
                  <p className="hint">{t("createActivity.loadingDimensions")}</p>
                )}
              </label>
            )}

            {showWorkOrder && (
              <label className="field">
                <span>{t("createActivity.workOrder")}</span>
                <select
                  value={workOrderId}
                  onChange={(e) => setWorkOrderId(e.target.value)}
                  disabled={busy || workOrdersQuery.isLoading}
                >
                  <option value="">{t("createActivity.dimensionNone")}</option>
                  {(workOrdersQuery.data?.items ?? []).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.displayName}
                    </option>
                  ))}
                </select>
                {workOrdersQuery.isLoading && (
                  <p className="hint">{t("createActivity.loadingDimensions")}</p>
                )}
              </label>
            )}

            {showProject && (
              <label className="field">
                <span>{t("createActivity.project")}</span>
                <select
                  value={projectId}
                  onChange={(e) => setProjectId(e.target.value)}
                  disabled={busy || projectsQuery.isLoading}
                >
                  <option value="">{t("createActivity.dimensionNone")}</option>
                  {(projectsQuery.data?.items ?? []).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.displayName}
                    </option>
                  ))}
                </select>
                {projectsQuery.isLoading && (
                  <p className="hint">{t("createActivity.loadingDimensions")}</p>
                )}
              </label>
            )}
          </section>
        )}

        {selectedFirm && showClassificationSection && (
          <section className="form-section" aria-labelledby="create-activity-classification-title">
            <h2 id="create-activity-classification-title" className="form-section__title">
              {t("createActivity.classificationSection")}
            </h2>

            {showActivityArea && (
              <CatalogSelectField
                label={t("createActivity.activityArea")}
                selector={areaSelector}
                busy={busy}
                noneLabel={t("createActivity.classificationNone")}
                loadingLabel={t("createActivity.loadingClassification")}
                requiredErrorLabel={t("createActivity.classificationRequired")}
                configurationErrorLabel={t("createActivity.classificationConfigurationError")}
              />
            )}

            {showActivityType && (
              <CatalogSelectField
                label={t("createActivity.activityType")}
                required
                selector={typeSelector}
                busy={busy}
                noneLabel={t("createActivity.classificationNone")}
                loadingLabel={t("createActivity.loadingClassification")}
                requiredErrorLabel={t("createActivity.activityTypeRequired")}
                configurationErrorLabel={t("createActivity.classificationNoTypesForArea")}
                error={activityTypeError}
                onClearError={() => setActivityTypeError(null)}
              />
            )}

            {showActivityQueue && (
              <CatalogSelectField
                label={t("createActivity.activityQueue")}
                required
                selector={queueSelector}
                busy={busy}
                noneLabel={t("createActivity.classificationNone")}
                loadingLabel={t("createActivity.loadingClassification")}
                requiredErrorLabel={t("createActivity.activityQueueRequired")}
                configurationErrorLabel={t("createActivity.classificationNoQueuesForAreaType")}
                error={activityQueueError}
                onClearError={() => setActivityQueueError(null)}
              />
            )}
          </section>
        )}

        <div className="field">
          <span>{t("createActivity.plannedDate")} *</span>
          <div className="follow-up-schedule">
            <input
              type="date"
              className="follow-up-schedule-date"
              value={scheduleDate}
              onChange={(e) => {
                setScheduleDate(e.target.value);
                if (scheduleError) {
                  setScheduleError(null);
                }
              }}
              disabled={busy}
              required
            />
            <input
              type="time"
              className="follow-up-schedule-time"
              value={scheduleTime}
              step={60}
              onChange={(e) => {
                setScheduleTime(e.target.value);
                if (scheduleError) {
                  setScheduleError(null);
                }
              }}
              disabled={busy}
              required
            />
          </div>
          {isFollowUpScheduleComplete(scheduleDate, scheduleTime) && (
            <p className="follow-up-schedule-preview">
              {formatDateTimeFull(followUpScheduleToIso(scheduleDate, scheduleTime))}
            </p>
          )}
        </div>
        {scheduleError && (
          <p className="error" role="alert">
            {scheduleError}
          </p>
        )}

        <label className="field">
          <span>{t("createActivity.assignedUser")}</span>
          <select
            value={assignedUserId}
            onChange={(e) => {
              setAssignedUserId(e.target.value);
              if (assignedUserError) {
                setAssignedUserError(null);
              }
            }}
            disabled={busy || usersQuery.isLoading}
            required
          >
            {!assignedUserId && <option value="">{t("loading.connecting")}</option>}
            {(usersQuery.data?.items ?? []).map((user) => (
              <option key={user.id} value={user.id}>
                {user.displayName} ({user.loginName})
              </option>
            ))}
            {assignedUserId &&
              !(usersQuery.data?.items ?? []).some((user) => user.id === assignedUserId) &&
              (representative ?? sessionQuery.data?.representative) && (
                <option value={(representative ?? sessionQuery.data!.representative).id}>
                  {(representative ?? sessionQuery.data!.representative).displayName}
                  {(representative ?? sessionQuery.data!.representative).loginName
                    ? ` (${(representative ?? sessionQuery.data!.representative).loginName})`
                    : ""}
                </option>
              )}
          </select>
        </label>
        {assignedUserError && (
          <p className="error" role="alert">
            {assignedUserError}
          </p>
        )}

        <label className="field">
          <span>{t("createActivity.description")}</span>
          <textarea
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={t("createActivity.descriptionPlaceholder")}
            disabled={busy}
          />
        </label>

        {formError && (
          <p className="error create-activity-form-error" role="alert">
            {formError}
          </p>
        )}

        <button
          type="submit"
          className="btn-primary create-activity-submit"
          disabled={busy || classificationConfigurationError}
        >
          {busy ? t("createActivity.creating") : t("createActivity.submit")}
        </button>
      </form>
    </div>
  );
}
