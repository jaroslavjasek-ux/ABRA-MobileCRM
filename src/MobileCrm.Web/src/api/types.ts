export type SalesRepresentative = {
  id: string;
  loginName: string;
  displayName: string;
  email?: string;
  employeeNumber?: string;
};

export type SessionResponse = {
  representative: SalesRepresentative;
  expiresAt?: string | null;
  sessionToken?: string;
  capabilities?: string[];
  provider?: { name: string; version?: string };
};

export type ActivitySummary = {
  id: string;
  documentNumber?: string;
  subject: string;
  status: string;
  activityTypeId?: string;
  activityTypeName?: string;
  firmId?: string;
  firmName?: string;
  contactId?: string;
  contactName?: string;
  scheduledStart: string;
  scheduledEnd?: string;
  isOverdue: boolean;
};

export type MyDayResponse = {
  date: string;
  representative: SalesRepresentative;
  today: ActivitySummary[];
  overdue: ActivitySummary[];
  todayCount: number;
  overdueCount: number;
  meta?: { schemaVersion?: string };
};

export type ApiErrorBody = {
  code: string;
  message: string;
  details?: { field: string; message: string }[];
  traceId?: string;
};

export type LoginRequest = {
  loginName: string;
  password: string;
};

export type Address = {
  line1?: string;
  street?: string;
  city?: string;
  postCode?: string;
  countryCode?: string;
  phone1?: string;
  phone2?: string;
  email?: string;
  fax?: string;
};

export type FirmSummary = {
  id: string;
  name: string;
  code?: string;
  businessRegistrationNumber?: string;
  city?: string;
  commercialStatus?: string;
};

export type PagedResult<T> = {
  items: T[];
  total: number;
  hasMore: boolean;
};

export type ContactSummary = {
  id: string;
  displayName: string;
  firstName?: string;
  lastName?: string;
  jobTitle?: string;
  isPrimary: boolean;
  phone1?: string;
  email?: string;
};

export type CommercialHealth = {
  statusLine?: string;
  commercialStatus?: string;
  creditIndicator?: string;
  overdueIndicator?: string;
  guidanceText?: string;
};

export type FirmDetailResponse = {
  id: string;
  name: string;
  code?: string;
  businessRegistrationNumber?: string;
  taxNumber?: string;
  commercialStatus?: string;
  commercialHealth?: CommercialHealth | null;
  mainAddress?: Address;
  electronicAddress?: Address;
  website?: string;
  contacts: ContactSummary[];
  primaryContactId?: string;
  recentActivities: ActivitySummary[];
  pipelineSnapshot?: { openDealCount?: number | null };
  lastModifiedAt?: string;
  meta?: {
    schemaVersion?: string;
    availability?: Record<string, string>;
  };
};

export type ScheduleFollowUpRequest = {
  enabled: boolean;
  subject?: string;
  scheduledStart?: string;
  description?: string;
  assignedUserId?: string;
};

export type CompleteActivityRequest = {
  answer: string;
  description?: string;
  followUp?: ScheduleFollowUpRequest;
};

export type FollowUpActivitySummary = {
  id: string;
  documentNumber?: string;
  subject: string;
  scheduledStart: string;
};

export type ApiWarning = {
  code: string;
  message: string;
};

export type AddActivityNoteRequest = {
  note: string;
};

export type ActivityDetailResponse = {
  id: string;
  documentNumber?: string;
  subject: string;
  description?: string;
  answer?: string;
  status: string;
  activityTypeId?: string;
  activityTypeName?: string;
  scheduledStart: string;
  scheduledEnd?: string;
  firm: FirmSummary;
  contact?: ContactSummary;
  ownerId?: string;
  ownerDisplayName?: string;
  canEdit: boolean;
  canComplete: boolean;
  canAddNote: boolean;
  lastModifiedAt?: string;
  followUpActivity?: FollowUpActivitySummary;
  warnings?: ApiWarning[];
  meta?: { schemaVersion?: string };
};

export type ContactDetailResponse = {
  id: string;
  firmId?: string;
  firmName?: string;
  firstName?: string;
  lastName?: string;
  displayName: string;
  jobTitle?: string;
  address?: Address;
  isPrimary: boolean;
  notes?: string;
};
