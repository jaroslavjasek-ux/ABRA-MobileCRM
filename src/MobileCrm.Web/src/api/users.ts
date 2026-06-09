import { apiRequest } from "@/api/client";
import type { PagedResult, SalesRepresentative } from "@/api/types";

export function searchUsers(q?: string, take = 30) {
  const params = new URLSearchParams();
  if (q?.trim()) {
    params.set("q", q.trim());
  }
  params.set("take", String(take));
  const query = params.toString();
  return apiRequest<PagedResult<SalesRepresentative>>(`/users?${query}`);
}
