export function backFromFirmDetail(): string {
  return "/app/firms";
}

export function firmDetailPath(firmId: string): string {
  return `/app/firms/${firmId}`;
}

export function contactDetailPath(contactId: string, firmId?: string): string {
  const base = `/app/contacts/${contactId}`;
  return firmId ? `${base}?firmId=${encodeURIComponent(firmId)}` : base;
}

export function activityDetailPath(activityId: string): string {
  return `/app/activities/${activityId}`;
}
