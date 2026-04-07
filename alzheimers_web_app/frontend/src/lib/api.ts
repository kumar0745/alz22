/**
 * Central API client for the FastAPI backend. Uses same-origin `/api` in dev (Vite proxy).
 * Set `VITE_API_URL` for production when the UI is served from a different host.
 */

const apiOrigin = () => import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "";

export async function checkApiHealth(): Promise<boolean> {
  try {
    const url = apiOrigin() ? `${apiOrigin()}/api/health` : "/api/health";
    const res = await fetch(url, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function predictMri(file: File, explain: boolean): Promise<Response> {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("explain", explain ? "true" : "false");
  const url = apiOrigin() ? `${apiOrigin()}/api/predict` : "/api/predict";
  return fetch(url, { method: "POST", body: formData });
}
