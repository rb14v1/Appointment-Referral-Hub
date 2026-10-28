import { apiClient } from "../client";
import type { PaginatedResponse, WaitlistEntry, WaitlistOffer } from "../../types";

export function listWaitlist(params?: Record<string, string | number | undefined>) {
  return apiClient.get<PaginatedResponse<WaitlistEntry>>("/waitlist/", { params: { page_size: 100, ...params } });
}

export interface JoinWaitlistPayload {
  patient: number;
  clinic: number;
  provider?: number;
  desired_date_range_start: string;
  desired_date_range_end: string;
  priority?: number;
}

export function joinWaitlist(payload: JoinWaitlistPayload) {
  return apiClient.post<WaitlistEntry>("/waitlist/", payload);
}

export function listWaitlistOffers(params?: Record<string, string | number | undefined>) {
  return apiClient.get<PaginatedResponse<WaitlistOffer>>("/waitlist-offers/", { params: { page_size: 100, ...params } });
}

export function respondToOffer(id: number, accept: boolean) {
  return apiClient.post<WaitlistOffer>(`/waitlist-offers/${id}/respond/`, { accept });
}
