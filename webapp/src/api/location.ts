import { useMutation, useQuery } from "@tanstack/react-query";
import { locationApi } from "./client";

export interface Country {
  iso2: string;
  iso3: string;
  name: string;
  dialCode: string;
}

export interface Region {
  code: string;
  name: string;
}

export interface FusedLocation {
  source: string;
  confidence: number;
  country: string | null;
  region: string | null;
  city: string | null;
  latitude: number | null;
  longitude: number | null;
  timestamp: string;
}

export interface FuseLocationInput {
  gps?: {
    latitude: number;
    longitude: number;
    accuracy?: number;
    timestamp?: string;
  } | null;
  ip?: Record<string, unknown> | null;
  userSelected?: {
    country?: string;
    region?: string;
    areaCode?: string;
  };
}

export async function fetchCountries(): Promise<Country[]> {
  const { data } = await locationApi.get<Country[]>("/countries");
  return data;
}

export async function fetchRegions(country: string): Promise<Region[]> {
  const { data } = await locationApi.get<Region[]>(`/regions/${country}`);
  return data;
}

export async function fetchAreaCodes(country: string) {
  const { data } = await locationApi.get<Record<string, unknown>>(
    `/area-codes/${country}`,
  );
  return data;
}

export async function fuseLocation(input: FuseLocationInput) {
  const { data } = await locationApi.post<{
    fused: FusedLocation | null;
    sources: Array<{ source: string; confidence: number; data: unknown }>;
  }>("/fuse", input);
  return data;
}

export function useCountries() {
  return useQuery({
    queryKey: ["location", "countries"],
    queryFn: fetchCountries,
  });
}

export function useRegions(country: string) {
  return useQuery({
    queryKey: ["location", "regions", country],
    queryFn: () => fetchRegions(country),
    enabled: Boolean(country),
  });
}

export function useAreaCodes(country: string) {
  return useQuery({
    queryKey: ["location", "area-codes", country],
    queryFn: () => fetchAreaCodes(country),
    enabled: Boolean(country),
  });
}

export function useFuseLocation() {
  return useMutation({
    mutationFn: fuseLocation,
  });
}
