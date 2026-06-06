import { apiRequest } from "@/api/client";
import type { ActivityDetailResponse, CompleteActivityRequest } from "@/api/types";

export function getActivity(activityId: string) {
  return apiRequest<ActivityDetailResponse>(`/activities/${activityId}`);
}

export function startActivity(activityId: string) {
  return apiRequest<ActivityDetailResponse>(`/activities/${activityId}/start`, {
    method: "PUT",
  });
}

export function completeActivity(activityId: string, body: CompleteActivityRequest) {
  return apiRequest<ActivityDetailResponse>(`/activities/${activityId}/complete`, {
    method: "PUT",
    body,
  });
}
