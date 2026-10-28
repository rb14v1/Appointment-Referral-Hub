import { apiClient } from "../client";
import type { PaginatedResponse, Referral } from "../../types";

export function listReferrals(params?: Record<string, string | number | undefined>) {
  return apiClient.get<PaginatedResponse<Referral>>("/referrals/", { params: { page_size: 100, ...params } });
}

export interface CreateReferralPayload {
  patient: number;
  referring_clinic: number;
  referring_provider?: number;
  receiving_clinic: number;
  reason: string;
  urgency: "routine" | "urgent";
}

export function createReferral(payload: CreateReferralPayload) {
  return apiClient.post<Referral>("/referrals/", payload);
}

export function acceptReferral(id: number, receiving_provider?: number, notes?: string) {
  return apiClient.post<Referral>(`/referrals/${id}/accept/`, { receiving_provider, notes });
}

export function rejectReferral(id: number, notes?: string) {
  return apiClient.post<Referral>(`/referrals/${id}/reject/`, { notes });
}

export function scheduleReferral(id: number, provider: number, start_time: string, reason?: string) {
  return apiClient.post(`/referrals/${id}/schedule/`, { provider, start_time, reason });
}

export function cancelReferral(id: number) {
  return apiClient.post<Referral>(`/referrals/${id}/cancel/`);
}
