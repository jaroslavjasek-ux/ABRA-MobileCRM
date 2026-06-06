import type { ActivitySummary } from "@/api/types";

const ACTIVE_STATUSES = new Set(["open", "inProgress"]);
const HISTORY_STATUSES = new Set(["completed", "handedOver"]);

export function isActiveActivity(status: string): boolean {
  return ACTIVE_STATUSES.has(status);
}

export function isHistoryActivity(status: string): boolean {
  return HISTORY_STATUSES.has(status);
}

function parseStart(iso: string): number {
  const t = Date.parse(iso);
  return Number.isNaN(t) ? 0 : t;
}

/** Soonest scheduled first — what needs attention next. */
function compareActive(a: ActivitySummary, b: ActivitySummary): number {
  return parseStart(a.scheduledStart) - parseStart(b.scheduledStart);
}

/** Most recent first in history. */
function compareHistory(a: ActivitySummary, b: ActivitySummary): number {
  return parseStart(b.scheduledStart) - parseStart(a.scheduledStart);
}

export function partitionFirmActivities(activities: ActivitySummary[]): {
  active: ActivitySummary[];
  history: ActivitySummary[];
} {
  const active: ActivitySummary[] = [];
  const history: ActivitySummary[] = [];

  for (const activity of activities) {
    if (isActiveActivity(activity.status)) {
      active.push(activity);
    } else if (isHistoryActivity(activity.status)) {
      history.push(activity);
    } else {
      history.push(activity);
    }
  }

  active.sort(compareActive);
  history.sort(compareHistory);

  return { active, history };
}

