import { apiRequest } from "@/api/client";
import type { LoginRequest, SessionResponse } from "@/api/types";

export function postSession(body: LoginRequest) {
  return apiRequest<SessionResponse>("/session", {
    method: "POST",
    body,
    auth: false,
  });
}

export function getSession() {
  return apiRequest<SessionResponse>("/session");
}

export function deleteSession() {
  return apiRequest<void>("/session", { method: "DELETE" });
}
