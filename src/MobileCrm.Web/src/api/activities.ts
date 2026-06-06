import { apiRequest } from "@/api/client";
import type {
  ActivityDetailResponse,
  AddActivityNoteRequest,
  CompleteActivityRequest,
} from "@/api/types";

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

export function addActivityNote(activityId: string, body: AddActivityNoteRequest) {
  return apiRequest<ActivityDetailResponse>(`/activities/${activityId}/note`, {
    method: "PUT",
    body,
  });
}
