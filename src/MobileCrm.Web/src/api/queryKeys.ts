export const queryKeys = {
  session: ["session"] as const,
  myDay: (date?: string) => ["myDay", date ?? "today"] as const,
  firmsSearch: (q: string, take: number) => ["firms", "search", q, take] as const,
  firmDetail: (id: string) => ["firms", "detail", id] as const,
  contactDetail: (id: string, firmId?: string) =>
    ["contacts", "detail", id, firmId ?? ""] as const,
  activityDetail: (id: string) => ["activities", "detail", id] as const,
};
