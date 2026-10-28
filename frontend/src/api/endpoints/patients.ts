import { apiClient } from "../client";
import type { PaginatedResponse, Patient } from "../../types";

export function listPatients() {
  return apiClient.get<PaginatedResponse<Patient>>("/patients/", { params: { page_size: 100 } });
}

/** The patients endpoint is queryset-scoped server-side to "me" for a
 * patient-role user, so this just grabs that one record. */
export function getMyPatientProfile() {
  return apiClient
    .get<PaginatedResponse<Patient>>("/patients/", { params: { page_size: 1 } })
    .then((res) => res.data.results[0] ?? null);
}
