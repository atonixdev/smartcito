/**
 * ============================================================================
 * File: webapp/src/api/events.ts
 * Purpose:
 *   Typed client for live events, historical analytics, and alerts exposed by
 *   the Orca backend event pipeline.
 * ============================================================================
 */

import { useQuery } from "@tanstack/react-query";

import { api } from "./client";

export interface NormalizedEvent {
  event_id: string;
  source: string;
  entity_id: string;
  event_type: string;
  occurred_at: string;
  received_at: string;
  payload: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface HistoricalAnalyticsPoint {
  sensor_id: string;
  samples: number;
  average_value: number;
  latest_observed_at: string;
}

export interface AlertEvent {
  id: string;
  severity: string;
  title: string;
  message: string;
  created_at: string;
  payload: Record<string, unknown>;
}

export async function fetchLiveEvents(): Promise<NormalizedEvent[]> {
  const { data } = await api.get<NormalizedEvent[]>("/events/live");
  return data;
}

export async function fetchHistoricalAnalytics(): Promise<HistoricalAnalyticsPoint[]> {
  const { data } = await api.get<HistoricalAnalyticsPoint[]>("/events/history");
  return data;
}

export async function fetchAlerts(): Promise<AlertEvent[]> {
  const { data } = await api.get<AlertEvent[]>("/events/alerts");
  return data;
}

export function useLiveEvents() {
  return useQuery({
    queryKey: ["events", "live"],
    queryFn: fetchLiveEvents,
    refetchInterval: 5_000,
  });
}

export function useHistoricalAnalytics() {
  return useQuery({
    queryKey: ["events", "history"],
    queryFn: fetchHistoricalAnalytics,
    refetchInterval: 15_000,
  });
}

export function useAlerts() {
  return useQuery({
    queryKey: ["events", "alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 5_000,
  });
}