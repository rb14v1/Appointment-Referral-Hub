import { apiClient } from "../client";
import type { User } from "../../types";

export interface LoginResponse {
  access: string;
  refresh: string;
}

export function login(email: string, password: string) {
  return apiClient.post<LoginResponse>("/auth/login/", { email, password });
}

export function register(data: { email: string; password: string; first_name?: string; last_name?: string }) {
  return apiClient.post<User>("/auth/register/", data);
}

export function fetchMe() {
  return apiClient.get<User>("/me/");
}

export function logout(refresh: string) {
  return apiClient.post("/auth/logout/", { refresh });
}
