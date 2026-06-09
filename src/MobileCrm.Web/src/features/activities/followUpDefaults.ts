export type FollowUpSchedule = {
  date: string;
  time: string;
};

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function toDateInput(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function toTimeInput(d: Date): string {
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Default follow-up start: now + 1 hour, rounded to full minutes (local time). */
export function defaultFollowUpSchedule(): FollowUpSchedule {
  const d = new Date();
  d.setSeconds(0, 0);
  d.setMinutes(d.getMinutes() + 60);
  return {
    date: toDateInput(d),
    time: toTimeInput(d),
  };
}

/** Combine date + time inputs into ISO-8601 instant for the API. */
export function followUpScheduleToIso(date: string, time: string): string {
  return new Date(`${date}T${time}`).toISOString();
}

/** Whether both date and time inputs are non-empty. */
export function isFollowUpScheduleComplete(date: string, time: string): boolean {
  return date.trim().length > 0 && time.trim().length > 0;
}
