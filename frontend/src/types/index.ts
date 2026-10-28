export type Role = "patient" | "front_desk" | "clinician" | "admin";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  clinic: number | null;
  phone: string;
}

export interface Clinic {
  id: number;
  name: string;
  address: string;
  timezone: string;
  phone: string;
  is_active: boolean;
  requires_front_desk_approval: boolean;
}

export interface Provider {
  id: number;
  user: number;
  user_detail: User;
  home_clinic: number;
  specialty: string;
  license_number: string;
  is_active: boolean;
  clinic_ids: number[];
}

export interface ProviderAvailability {
  id: number;
  provider: number;
  clinic: number;
  recurrence_rule: "weekly" | "one_off";
  day_of_week: number | null;
  specific_date: string | null;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  is_blocked: boolean;
}

export interface Slot {
  provider: number;
  clinic: number;
  start_time: string;
  end_time: string;
}

export interface Patient {
  id: number;
  user: number;
  user_detail: User;
  date_of_birth: string | null;
  primary_clinic: number | null;
  emergency_contact: string;
}

export type AppointmentStatus =
  | "requested"
  | "confirmed"
  | "checked_in"
  | "completed"
  | "cancelled"
  | "no_show";

export interface Appointment {
  id: number;
  patient: number;
  provider: number;
  clinic: number;
  start_time: string;
  end_time: string;
  status: AppointmentStatus;
  reason: string;
  created_by: number | null;
  referral: number | null;
  created_at: string;
  updated_at: string;
  patient_name: string;
  provider_name: string;
  clinic_name: string;
}

export type ReferralUrgency = "routine" | "urgent";
export type ReferralStatus =
  | "pending"
  | "accepted"
  | "rejected"
  | "scheduled"
  | "completed"
  | "cancelled";

export interface Referral {
  id: number;
  patient: number;
  referring_clinic: number;
  referring_provider: number | null;
  receiving_clinic: number;
  receiving_provider: number | null;
  reason: string;
  urgency: ReferralUrgency;
  status: ReferralStatus;
  notes: string;
  created_by: number | null;
  created_at: string;
  resolved_at: string | null;
  patient_name: string;
}

export type WaitlistStatus = "waiting" | "offered" | "booked" | "expired" | "cancelled";

export interface WaitlistEntry {
  id: number;
  patient: number;
  clinic: number;
  provider: number | null;
  desired_date_range_start: string;
  desired_date_range_end: string;
  status: WaitlistStatus;
  priority: number;
  created_at: string;
}

export interface WaitlistOffer {
  id: number;
  waitlist_entry: number;
  provider: number;
  start_time: string;
  end_time: string;
  offered_at: string;
  expires_at: string;
  response: "pending" | "accepted" | "declined" | "expired";
  responded_at: string | null;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
