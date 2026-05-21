/**
 * ============================================================================
 * File: frontend/src/api/client.ts
 * Purpose:
 *   Thin axios wrapper that:
 *     - Points at the FastAPI backend (proxied in dev).
 *     - Attaches the JWT from localStorage when present.
 *     - Surfaces backend errors in a normalized shape.
 * ============================================================================
 */

import axios, { AxiosError, AxiosInstance } from "axios";

const TOKEN_STORAGE_KEY = "smartcito.jwt";

export const api: AxiosInstance = axios.create({
  baseURL: "/api/v1",
  timeout: 10_000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/** Normalized error shape used across the UI. */
export interface ApiError {
  status: number;
  message: string;
}

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const normalized: ApiError = {
      status: error.response?.status ?? 0,
      message:
        error.response?.data?.detail ??
        error.message ??
        "Unknown network error",
    };
    return Promise.reject(normalized);
  },
);

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_STORAGE_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_STORAGE_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_STORAGE_KEY),
};
