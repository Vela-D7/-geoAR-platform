/** Browser-side API helpers — everything goes through the server proxy. */

export const api = (path: string) => `/api/proxy/${path.replace(/^\//, "")}`;

export async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(api(path), { cache: "no-store" });
  if (!res.ok) throw new Error(`${path}: ${res.status} ${await res.text()}`);
  return res.json();
}

export type Site = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  recognition_target_status: string;
  model_asset_path: string | null;
  last_outcome: string | null;
  session_count: number;
};

export type Thresholds = {
  site_id: string;
  version: number;
  gps_accuracy_good_m: number;
  visual_confidence_min: number;
  changed_by: string;
  reason: string;
};

export type UploadResult = {
  filename: string;
  size_bytes: number;
  accepted: boolean;
  checks: { name: string; passed: boolean; detail: string }[];
};
