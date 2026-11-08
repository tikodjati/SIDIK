import type { components } from "./api-types";

type Schemas = components["schemas"];
export type Recipient = Schemas["RecipientOut"];
export type RecipientInput = Schemas["RecipientIn"];
export type DocumentRow = Schemas["DocumentOut"];
export type DocumentInput = Schemas["DocumentIn"];
export type CopyIssued = Schemas["CopyIssued"];
export type CopyRow = Schemas["CopyOut"];
export type IntakeResult = Schemas["IntakeResult"];
export type LayerReading = Schemas["LayerReading"];
export type LedgerEntry = Schemas["LedgerEntryOut"];
export type VerifyResult = Schemas["VerifyOut"];
export type User = Schemas["UserOut"];
export type UserInput = Schemas["UserCreate"];
export type Role = User["role"];

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
/** Dipancarkan saat API menjawab 401, supaya AuthProvider mengarahkan ke halaman login. */
export const UNAUTHORIZED_EVENT = "sidik:unauthorized";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      cache: "no-store",
      credentials: "include", // cookie sesi HttpOnly
      ...init,
      // FormData (unggah foto) menetapkan Content-Type multipart sendiri.
      headers: {
        ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError("Tidak dapat terhubung ke server API.", 0);
  }
  if (res.status === 401 && !path.startsWith("/api/v1/auth/")) {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg: string }) => d.msg).join("; ");
    } catch {
      /* badan bukan JSON */
    }
    throw new ApiError(detail, res.status);
  }
  if (res.status === 204) return undefined as T;
  if (res.headers.get("content-type")?.startsWith("application/pdf")) return res.blob() as Promise<T>;
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

export const login = (username: string, password: string) =>
  post<User>("/api/v1/auth/login", { username, password });
export const logout = () => post<void>("/api/v1/auth/logout", {});
export const getMe = () => request<User>("/api/v1/auth/me");
export const changePassword = (currentPassword: string, newPassword: string) =>
  post<void>("/api/v1/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
export const listUsers = () => request<User[]>("/api/v1/users");
export const createUser = (body: UserInput) => post<User>("/api/v1/users", body);
export const setUserActive = (id: number, isActive: boolean) =>
  request<User>(`/api/v1/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
export const getHealth = () => request<{ status: string }>("/health");
export const listRecipients = () => request<Recipient[]>("/api/v1/recipients");
export const createRecipient = (body: RecipientInput) => post<Recipient>("/api/v1/recipients", body);
export const listDocuments = () => request<DocumentRow[]>("/api/v1/documents");
export const createDocument = (body: DocumentInput) => post<DocumentRow>("/api/v1/documents", body);
export const listCopies = () => request<CopyRow[]>("/api/v1/copies");
export const issueCopy = (documentId: number, recipientId: number) =>
  post<CopyIssued>(`/api/v1/documents/${documentId}/copies`, { recipient_id: recipientId });
export const getCopyText = (copyId: number) =>
  request<{ copy_id: number; text: string }>(`/api/v1/copies/${copyId}/text`);
export const intakeText = (text: string, caseRef?: string) =>
  post<IntakeResult>("/api/v1/intake/text", { text, case_ref: caseRef || null });
export const listLedger = (limit = 100, offset = 0) =>
  request<LedgerEntry[]>(`/api/v1/ledger?limit=${limit}&offset=${offset}&newest_first=true`);
export const verifyLedger = () => request<VerifyResult>("/api/v1/ledger/verify");
export const getCopyPdf = (copyId: number) => request<Blob>(`/api/v1/copies/${copyId}/pdf`);
export function intakePhoto(photo: File, caseRef?: string) {
  const form = new FormData();
  form.append("photo", photo);
  if (caseRef) form.append("case_ref", caseRef);
  return request<IntakeResult>("/api/v1/intake/photo", { method: "POST", body: form });
}

/** Simpan Blob sebagai berkas unduhan di peramban. */
export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
