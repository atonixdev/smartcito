/**
 * ============================================================================
 * File: webapp/src/api/client.ts
 * Purpose:
 *   Thin axios wrapper that:
 *     - Points at the FastAPI citosmart (proxied in dev).
 *     - Attaches the JWT from localStorage when present.
 *     - Surfaces citosmart errors in a normalized shape.
 * ============================================================================
 */

import axios, { AxiosError, AxiosInstance } from "axios";

const TOKEN_STORAGE_KEY = "smartcito.jwt";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const LOCATION_API_BASE_URL =
  import.meta.env.VITE_LOCATION_API_BASE_URL ?? "/api/location";
const GPS_API_BASE_URL = import.meta.env.VITE_GPS_API_BASE_URL ?? "/api/gps";

function getStoredToken() {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

function attachAuth(
  config: Parameters<AxiosInstance["interceptors"]["request"]["use"]>[0] extends (arg: infer A) => unknown ? A : never,
) {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}

function normalizeApiError(error: AxiosError<{ detail?: string; error?: string }>) {
  const normalized: ApiError = {
    status: error.response?.status ?? 0,
    message:
      error.response?.data?.detail ??
      error.response?.data?.error ??
      error.message ??
      "Unknown network error",
  };
  return Promise.reject(normalized);
}

function unwrapApiEnvelope(response: { data: unknown }) {
  if (
    response.data &&
    typeof response.data === "object" &&
    "status" in response.data &&
    "data" in response.data &&
    "meta" in response.data
  ) {
    response.data = (response.data as { data: unknown }).data;
  }
  return response;
}

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
});

export const locationApi: AxiosInstance = axios.create({
  baseURL: LOCATION_API_BASE_URL,
  timeout: 10_000,
});

export const gpsApi: AxiosInstance = axios.create({
  baseURL: GPS_API_BASE_URL,
  timeout: 10_000,
});

api.interceptors.request.use(attachAuth);
locationApi.interceptors.request.use(attachAuth);
gpsApi.interceptors.request.use(attachAuth);

/** Normalized error shape used across the UI. */
export interface ApiError {
  status: number;
  message: string;
}

api.interceptors.response.use(unwrapApiEnvelope, normalizeApiError);
locationApi.interceptors.response.use(unwrapApiEnvelope, normalizeApiError);
gpsApi.interceptors.response.use(unwrapApiEnvelope, normalizeApiError);

export const tokenStorage = {
  get: () => getStoredToken(),
  set: (token: string) => localStorage.setItem(TOKEN_STORAGE_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_STORAGE_KEY),
};
