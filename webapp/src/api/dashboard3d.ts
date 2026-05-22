export type SmartCito3DDeviceType = "iot" | "gps" | "camera" | "edge";
export type SmartCito3DTrustStatus = "verified" | "unverified" | "blocked";
export type SmartCito3DThreatSeverity = "low" | "medium" | "high";

export interface SmartCito3DDevice {
  id: string;
  name: string;
  type: SmartCito3DDeviceType;
  status: SmartCito3DTrustStatus;
  trust_score: number;
  latitude: number;
  longitude: number;
  x: number;
  z: number;
  telemetry: string;
  camera_stream?: string | null;
}

export interface SmartCito3DThreat {
  id: string;
  label: string;
  severity: SmartCito3DThreatSeverity;
  x: number;
  z: number;
}

export interface SmartCito3DGpsPath {
  device_id: string;
  points: Array<{ x: number; z: number }>;
}

export interface SmartCito3DDashboardPayload {
  generated_at: string;
  map: {
    name: string;
    mode: "3d";
    center: { latitude: number; longitude: number };
  };
  devices: SmartCito3DDevice[];
  threats: SmartCito3DThreat[];
  gps_paths: SmartCito3DGpsPath[];
}

const fallbackPayload: SmartCito3DDashboardPayload = {
  generated_at: new Date().toISOString(),
  map: {
    name: "SmartCito Local Demo Map",
    mode: "3d",
    center: { latitude: -1.2921, longitude: 36.8219 },
  },
  devices: [],
  threats: [],
  gps_paths: [],
};

export async function fetchSmartCito3DDashboard(): Promise<SmartCito3DDashboardPayload> {
  const response = await fetch("/api/location/dashboard/3d", {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    return fallbackPayload;
  }

  return response.json();
}

export async function audit3DVisualizationEvent(payload: Record<string, unknown>) {
  await fetch("/api/location/dashboard/audit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  }).catch(() => undefined);
}
