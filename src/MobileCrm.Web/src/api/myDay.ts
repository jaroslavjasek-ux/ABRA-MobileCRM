import { apiRequest } from "@/api/client";
import type { MyDayResponse } from "@/api/types";

export function getMyDay(date?: string, take = 50) {
  const params = new URLSearchParams();
  if (date) {
    params.set("date", date);
  }
  params.set("take", String(take));
  const q = params.toString();
  return apiRequest<MyDayResponse>(`/my-day${q ? `?${q}` : ""}`);
}
