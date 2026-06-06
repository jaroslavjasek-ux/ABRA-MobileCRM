import { apiRequest } from "@/api/client";
import type { FirmDetailResponse, FirmSummary, PagedResult } from "@/api/types";

export function searchFirms(q: string, take = 20, skip = 0) {
  const params = new URLSearchParams({
    q,
    take: String(take),
    skip: String(skip),
  });
  return apiRequest<PagedResult<FirmSummary>>(`/firms?${params}`);
}

export function getFirmDetail(firmId: string, recentTake = 10) {
  const params = new URLSearchParams({ recentTake: String(recentTake) });
  return apiRequest<FirmDetailResponse>(`/firms/${firmId}?${params}`);
}
