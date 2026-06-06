import { Link } from "react-router-dom";
import type { ActivitySummary } from "@/api/types";
import { partitionFirmActivities } from "@/features/firms/activityGroups";
import { activityDetailPath, firmDetailPath } from "@/lib/navigation";
import { useI18n } from "@/i18n";
import { ActivityDocumentNumber } from "@/features/activities/ActivityDocumentNumber";

function ActivityRow({
  activity,
  firmId,
  formatDateTimeFull,
  formatActivityStatus,
}: {
  activity: ActivitySummary;
  firmId: string;
  formatDateTimeFull: (iso: string) => string;
  formatActivityStatus: (status: string) => string;
}) {
  return (
    <li>
      <Link
        to={activityDetailPath(activity.id)}
        state={{ from: firmDetailPath(firmId) }}
        className="activity-row activity-row--compact activity-row--link"
      >
        <div className="activity-row-top">
          <time className="activity-when" dateTime={activity.scheduledStart}>
            {formatDateTimeFull(activity.scheduledStart)}
          </time>
          <span className={`badge status-${activity.status}`}>
            {formatActivityStatus(activity.status)}
          </span>
        </div>
        <ActivityDocumentNumber documentNumber={activity.documentNumber} />
        <strong className="activity-subject">{activity.subject}</strong>
      </Link>
    </li>
  );
}

export function FirmActivitiesSection({
  activities,
  firmId,
}: {
  activities: ActivitySummary[];
  firmId: string;
}) {
  const { t, formatDateTimeFull, formatActivityStatus } = useI18n();

  if (activities.length === 0) {
    return null;
  }

  const { active, history } = partitionFirmActivities(activities);

  return (
    <section className="detail-section detail-section--compact activities-section">
      <div className="section-heading-row">
        <h2>{t("firms.activeWork")}</h2>
        <span className="section-count">{active.length}</span>
      </div>

      {active.length === 0 ? (
        <p className="empty activities-empty">{t("firms.noOpenActivities")}</p>
      ) : (
        <ul className="activity-list">
          {active.map((a) => (
            <ActivityRow
              key={a.id}
              activity={a}
              firmId={firmId}
              formatDateTimeFull={formatDateTimeFull}
              formatActivityStatus={formatActivityStatus}
            />
          ))}
        </ul>
      )}

      {history.length > 0 && (
        <details className="activities-history">
          <summary>
            {t("firms.history")}
            <span className="section-count section-count--muted">{history.length}</span>
          </summary>
          <ul className="activity-list activity-list--history">
            {history.map((a) => (
              <ActivityRow
                key={a.id}
                activity={a}
                firmId={firmId}
                formatDateTimeFull={formatDateTimeFull}
                formatActivityStatus={formatActivityStatus}
              />
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
