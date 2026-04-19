export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBaseUrl()}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `GET ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${apiBaseUrl()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `POST ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${apiBaseUrl()}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `PATCH ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function apiDelete(path: string): Promise<void> {
  const res = await fetch(`${apiBaseUrl()}${path}`, { method: "DELETE", cache: "no-store" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `DELETE ${path} failed (${res.status})`);
  }
}
