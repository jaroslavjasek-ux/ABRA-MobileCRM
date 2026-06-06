import type { ApiErrorBody } from "@/api/types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly body?: ApiErrorBody;

  constructor(status: number, code: string, message: string, body?: ApiErrorBody) {
    super(message);
    this.status = status;
    this.code = code;
    this.body = body;
  }
}

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.code === "UNAUTHORIZED");
}

export function isServiceUnavailable(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    (error.code === "SERVICE_UNAVAILABLE" || error.status === 502 || error.status === 503)
  );
}
