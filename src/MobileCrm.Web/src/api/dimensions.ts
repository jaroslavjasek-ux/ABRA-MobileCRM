import { apiRequest } from "@/api/client";
import type { DimensionSummary, PagedResult } from "@/api/types";

function buildDimensionQuery(
  q: string | undefined,
  firmId: string | undefined,
  take: number,
  skip: number,
): string {
  const params = new URLSearchParams();
  if (q?.trim()) {
    params.set("q", q.trim());
  }
  if (firmId?.trim()) {
    params.set("firmId", firmId.trim());
  }
  params.set("take", String(take));
  params.set("skip", String(skip));
  return params.toString();
}

export function searchBusinessCases(
  q?: string,
  firmId?: string,
  take = 30,
  skip = 0,
) {
  const query = buildDimensionQuery(q, firmId, take, skip);
  return apiRequest<PagedResult<DimensionSummary>>(`/business-cases?${query}`);
}

export function searchWorkOrders(q?: string, firmId?: string, take = 30, skip = 0) {
  const query = buildDimensionQuery(q, firmId, take, skip);
  return apiRequest<PagedResult<DimensionSummary>>(`/work-orders?${query}`);
}

export function searchProjects(q?: string, firmId?: string, take = 30, skip = 0) {
  const query = buildDimensionQuery(q, firmId, take, skip);
  return apiRequest<PagedResult<DimensionSummary>>(`/projects?${query}`);
}
