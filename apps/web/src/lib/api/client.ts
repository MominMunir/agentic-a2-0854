import type { paths } from "./schema";
import { DefaultService, OpenAPI } from "./generated";
OpenAPI.BASE = "";
OpenAPI.WITH_CREDENTIALS = true;
OpenAPI.CREDENTIALS = "include";
export const generatedAuth = {
  login: DefaultService.loginApiAuthLoginPost,
  register: DefaultService.registerApiAuthRegisterPost,
};
export type ApiPath = keyof paths;
export async function api<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch("/api" + path, {
    credentials: "include",
    ...options,
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      "X-Requested-With": "GigBid",
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: "Connection unavailable. Please retry." }));
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : JSON.stringify(body.detail);
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json();
}
export const post = (path: string, body: any = {}) =>
  api(path, { method: "POST", body: JSON.stringify(body) });
