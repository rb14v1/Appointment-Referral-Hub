import { apiClient } from "../client";
import type { PaginatedResponse, Provider, ProviderAvailability, Slot } from "../../types";

export function listProviders(params?: { home_clinic?: number }) {
  return apiClient.get<PaginatedResponse<Provider>>("/providers/", { params: { page_size: 100, ...params } });
}

export function getSlots(providerId: number, dateFrom: string, dateTo: string, clinic?: number) {
  return apiClient.get<Slot[]>(`/providers/${providerId}/slots/`, {
    params: { date_from: dateFrom, date_to: dateTo, clinic },
  });
}

export function listAvailability(params?: { provider?: number }) {
  return apiClient.get<PaginatedResponse<ProviderAvailability>>("/availability/", {
    params: { page_size: 100, ...params },
  });
}

export function createAvailability(data: Partial<ProviderAvailability>) {
  return apiClient.post<ProviderAvailability>("/availability/", data);
}

export function deleteAvailability(id: number) {
  return apiClient.delete(`/availability/${id}/`);
}
