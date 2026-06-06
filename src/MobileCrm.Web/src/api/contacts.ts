import { apiRequest } from "@/api/client";
import type { ContactDetailResponse } from "@/api/types";

export function getContact(contactId: string, firmId?: string) {
  const params = firmId ? `?firmId=${encodeURIComponent(firmId)}` : "";
  return apiRequest<ContactDetailResponse>(`/contacts/${contactId}${params}`);
}
