import { apiClient } from "../client";
import type { Appointment, PaginatedResponse } from "../../types";

export function listAppointments(params?: Record<string, string | number | undefined>) {
  return apiClient.get<PaginatedResponse<Appointment>>("/appointments/", { params: { page_size: 100, ...params } });
}

export interface BookAppointmentPayload {
  patient: number;
  provider: number;
  clinic: number;
  start_time: string;
  reason?: string;
  referral?: number;
}

export function bookAppointment(payload: BookAppointmentPayload) {
  return apiClient.post<Appointment>("/appointments/", payload);
}

export function cancelAppointment(id: number, reason?: string) {
  return apiClient.post<Appointment>(`/appointments/${id}/cancel/`, { reason });
}

export function checkInAppointment(id: number) {
  return apiClient.post<Appointment>(`/appointments/${id}/check-in/`);
}

export function completeAppointment(id: number) {
  return apiClient.post<Appointment>(`/appointments/${id}/complete/`);
}

export function markNoShow(id: number) {
  return apiClient.post<Appointment>(`/appointments/${id}/no-show/`);
}
