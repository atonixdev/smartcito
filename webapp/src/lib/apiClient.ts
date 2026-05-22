/**
 * ============================================================================
 * File: webapp/src/lib/apiClient.ts
 * Purpose:
 *   Single SmartCito frontend API client: token injection, retry, envelope
 *   unwrapping, normalized errors, and WebSocket URL construction.
 * ============================================================================
 */

import axios, { type AxiosRequestConfig } from "axios";

const TOKEN_STORAGE_KEY = "smartcito.jwt";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export interface ApiEnvelope<T> {
  status: "success" | "error";
  timestamp: string;
  request_id: string;
  data: T;
  meta: {
    version: "v1";
    source: "smartcito-backend";
  };
}

export interface ApiClientError {
  status: number;
  message: string;
  requestId?: string;
}

function token() {
  return typeof localStorage === "undefined" ? null : localStorage.getItem(TOKEN_STORAGE_KEY);
}

function unwrap<T>(payload: T | ApiEnvelope<T>): T {
  if (
    payload &&
    typeof payload === "object" &&
    "status" in payload &&
    "data" in payload &&
    "meta" in payload
  ) {
    return (payload as ApiEnvelope<T>).data;
  }
  return payload as T;
}

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
});

http.interceptors.request.use((config) => {
  config.headers["x-request-id"] = crypto.randomUUID();
  const storedToken = token();
  if (storedToken) {
    config.headers.Authorization = `Bearer ${storedToken}`;
  }
  return config;
});

async function requestWithRetry<T>(config: AxiosRequestConfig, attempts = 2): Promise<T> {
  try {
    const response = await http.request<T | ApiEnvelope<T>>(config);
    return unwrap<T>(response.data);
  } catch (error: any) {
    if (attempts > 0 && (!error.response || error.response.status >= 500)) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      return requestWithRetry<T>(config, attempts - 1);
    }

    const normalized: ApiClientError = {
      status: error.response?.status ?? 0,
      message:
        error.response?.data?.data?.error ??
        error.response?.data?.detail ??
        error.response?.data?.error ??
        error.message ??
        "Unknown API error",
      requestId: error.response?.headers?.["x-request-id"],
    };
    throw normalized;
  }
}

export const apiClient = {
  get: <T>(url: string, config?: AxiosRequestConfig) => requestWithRetry<T>({ ...config, url, method: "GET" }),
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    requestWithRetry<T>({ ...config, url, data, method: "POST" }),
  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    requestWithRetry<T>({ ...config, url, data, method: "PATCH" }),
};

export function buildWebSocketUrl(path: string) {
  const base = new URL(API_BASE_URL, window.location.origin);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  base.pathname = `${base.pathname.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  const storedToken = token();
  if (storedToken) base.searchParams.set("token", storedToken);
  return base.toString();
}

export const tokenStorage = {
  get: token,
  set: (nextToken: string) => localStorage.setItem(TOKEN_STORAGE_KEY, nextToken),
  clear: () => localStorage.removeItem(TOKEN_STORAGE_KEY),
};
