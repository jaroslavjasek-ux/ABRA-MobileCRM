import { apiRequest } from "@/api/client";
import type { ClassificationSummary, PagedResult } from "@/api/types";

function buildClassificationQuery(
  q: string | undefined,
  take: number,
  skip: number,
  filters?: { areaId?: string; activityTypeId?: string },
): string {
  const params = new URLSearchParams();
  if (q?.trim()) {
    params.set("q", q.trim());
  }
  if (filters?.areaId?.trim()) {
    params.set("areaId", filters.areaId.trim());
  }
  if (filters?.activityTypeId?.trim()) {
    params.set("activityTypeId", filters.activityTypeId.trim());
  }
  params.set("take", String(take));
  params.set("skip", String(skip));
  return params.toString();
}

export function searchActivityAreas(q?: string, take = 50, skip = 0) {
  const query = buildClassificationQuery(q, take, skip);
  return apiRequest<PagedResult<ClassificationSummary>>(`/activity-areas?${query}`);
}

export function searchActivityTypes(q?: string, areaId?: string, take = 50, skip = 0) {
  const query = buildClassificationQuery(q, take, skip, { areaId });
  return apiRequest<PagedResult<ClassificationSummary>>(`/activity-types?${query}`);
}

export function searchActivityQueues(
  q?: string,
  areaId?: string,
  activityTypeId?: string,
  take = 50,
  skip = 0,
) {
  const query = buildClassificationQuery(q, take, skip, { areaId, activityTypeId });
  return apiRequest<PagedResult<ClassificationSummary>>(`/activity-queues?${query}`);
}
