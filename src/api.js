export async function api(path, options) {
  const body = options?.body;
  const isForm = typeof FormData !== 'undefined' && body instanceof FormData;
  const headers = isForm ? options?.headers : { 'Content-Type': 'application/json', ...(options?.headers || {}) };
  const response = await fetch(`/api${path}`, { ...options, headers });
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error || 'Request failed');
  return response.json();
}
