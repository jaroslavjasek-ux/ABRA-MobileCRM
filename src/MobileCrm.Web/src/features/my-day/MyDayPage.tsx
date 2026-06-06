import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getMyDay } from "@/api/myDay";
import { queryKeys } from "@/api/queryKeys";
import { useAuth } from "@/auth/AuthContext";
import { isUnauthorized, isServiceUnavailable } from "@/lib/errors";
import { Link, useNavigate } from "react-router-dom";
import { activityDetailPath, firmDetailPath } from "@/lib/navigation";
import { useI18n } from "@/i18n";
import { useEffect, useState } from "react";
import type { ActivitySummary } from "@/api/types";
import { ActivityDocumentNumber } from "@/features/activities/ActivityDocumentNumber";

function ActivityRow({
  item,
  formatWhen,
  formatActivityStatus,
}: {
  item: ActivitySummary;
  formatWhen: (iso: string) => string;
  formatActivityStatus: (status: string) => string;
}) {
  return (
    <li className="activity-row-card">
      <Link
        to={activityDetailPath(item.id)}
        state={{ from: "/app/my-day" }}
        className="activity-row-main"
      >
        <div className="activity-row-top">
          <span className="activity-time">{formatWhen(item.scheduledStart)}</span>
          <span className={`badge status-${item.status}`}>
            {formatActivityStatus(item.status)}
          </span>
        </div>
        <ActivityDocumentNumber documentNumber={item.documentNumber} />
        <strong className="activity-subject">{item.subject}</strong>
      </Link>
      {item.firmName && item.firmId && (
        <Link to={firmDetailPath(item.firmId)} className="activity-firm-link">
          {item.firmName}
        </Link>
      )}
    </li>
  );
}

function ActivitySection({
  title,
  items,
  emptyText,
  formatWhen,
  formatActivityStatus,
}: {
  title: string;
  items: ActivitySummary[];
  emptyText: string;
  formatWhen: (iso: string) => string;
  formatActivityStatus: (status: string) => string;
}) {
  return (
    <section className="day-section">
      <h2>
        {title} <span className="count">({items.length})</span>
      </h2>
      {items.length === 0 ? (
        <p className="empty">{emptyText}</p>
      ) : (
        <ul className="activity-list">
          {items.map((a) => (
            <ActivityRow
              key={a.id}
              item={a}
              formatWhen={formatWhen}
              formatActivityStatus={formatActivityStatus}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

export function MyDayPage() {
  const { representative } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);
  const { t, formatDate, formatTime, formatCalendarDate, formatActivityStatus } = useI18n();

  const myDayQuery = useQuery({
    queryKey: queryKeys.myDay(),
    queryFn: () => getMyDay(),
  });

  useEffect(() => {
    if (!myDayQuery.isError) {
      return;
    }
    const err = myDayQuery.error;
    if (isUnauthorized(err)) {
      navigate("/app/session-expired", { replace: true });
    } else if (isServiceUnavailable(err)) {
      navigate("/app/connection-error", {
        replace: true,
        state: { from: "/app/my-day" },
      });
    }
  }, [myDayQuery.isError, myDayQuery.error, navigate]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await queryClient.invalidateQueries({ queryKey: queryKeys.myDay() });
      await myDayQuery.refetch();
    } finally {
      setRefreshing(false);
    }
  };

  const data = myDayQuery.data;
  const displayName = data?.representative.displayName ?? representative?.displayName ?? "";
  const agendaDateIso = data?.date ?? new Date().toISOString().slice(0, 10);
  const agendaDateLabel = formatDate(agendaDateIso);

  return (
    <div className="my-day-page">
      <header className="my-day-header">
        <div>
          <h1>{t("myDay.title")}</h1>
          <p className="muted">
            {displayName
              ? t("myDay.hello", { name: displayName })
              : t("myDay.helloShort")}{" "}
            · {agendaDateLabel}
          </p>
        </div>
        <button
          type="button"
          className="btn-secondary"
          onClick={handleRefresh}
          disabled={myDayQuery.isFetching || refreshing}
        >
          {myDayQuery.isFetching || refreshing ? t("common.refreshing") : t("common.refresh")}
        </button>
      </header>

      {myDayQuery.isLoading && <p className="loading">{t("loading.agenda")}</p>}

      {myDayQuery.isError && !isUnauthorized(myDayQuery.error) && (
        <p className="error" role="alert">
          {myDayQuery.error instanceof Error ? myDayQuery.error.message : t("common.failedLoad")}
        </p>
      )}

      {data && (
        <>
          <ActivitySection
            title={t("myDay.today")}
            items={data.today}
            emptyText={t("myDay.emptyToday")}
            formatWhen={formatTime}
            formatActivityStatus={formatActivityStatus}
          />
          <ActivitySection
            title={t("myDay.overdue")}
            items={data.overdue}
            emptyText={t("myDay.emptyOverdue")}
            formatWhen={formatCalendarDate}
            formatActivityStatus={formatActivityStatus}
          />
        </>
      )}
    </div>
  );
}
