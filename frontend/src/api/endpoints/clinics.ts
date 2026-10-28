import { apiClient } from "../client";
import type { Clinic, PaginatedResponse } from "../../types";

export function listClinics() {
  return apiClient.get<PaginatedResponse<Clinic>>("/clinics/", { params: { page_size: 100 } });
}
