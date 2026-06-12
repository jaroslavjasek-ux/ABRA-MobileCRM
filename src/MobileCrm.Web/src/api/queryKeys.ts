export const queryKeys = {
  session: ["session"] as const,
  myDay: (date?: string) => ["myDay", date ?? "today"] as const,
  firmsSearch: (q: string, take: number) => ["firms", "search", q, take] as const,
  firmDetail: (id: string) => ["firms", "detail", id] as const,
  contactDetail: (id: string, firmId?: string) =>
    ["contacts", "detail", id, firmId ?? ""] as const,
  activityDetail: (id: string) => ["activities", "detail", id] as const,
  users: (q?: string) => ["users", q ?? ""] as const,
  businessCases: (firmId?: string, q?: string) =>
    ["businessCases", firmId ?? "", q ?? ""] as const,
  workOrders: (firmId?: string, q?: string) => ["workOrders", firmId ?? "", q ?? ""] as const,
  projects: (firmId?: string, q?: string) => ["projects", firmId ?? "", q ?? ""] as const,
  activityAreas: (q?: string) => ["activityAreas", q ?? ""] as const,
  activityTypes: (areaId?: string, q?: string) =>
    ["activityTypes", areaId ?? "", q ?? ""] as const,
  activityQueues: (areaId?: string, activityTypeId?: string, q?: string) =>
    ["activityQueues", areaId ?? "", activityTypeId ?? "", q ?? ""] as const,
};
