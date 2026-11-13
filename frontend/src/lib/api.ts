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
export type Attribution = Schemas["Attribution"];
export type TokenHit = Schemas["TokenHit"];
export type PersonnelSummary = Schemas["PersonnelSummary"];
export type DataExport = Schemas["ExportOut"];
export type Corpus = Schemas["CorpusOut"];
export type DumpResult = Schemas["DumpResult"];
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
  const type = res.headers.get("content-type") ?? "";
  if (type.startsWith("application/pdf") || type.startsWith("text/csv")) return res.blob() as Promise<T>;
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
export const approveCopy = (copyId: number) =>
  post<CopyRow>(`/api/v1/copies/${copyId}/approve`, {});
export const rejectCopy = (copyId: number, reason: string) =>
  post<CopyRow>(`/api/v1/copies/${copyId}/reject`, { reason });
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

export const getPersonnelSummary = () => request<PersonnelSummary>("/api/v1/personnel/summary");
export const seedPersonnel = () =>
  post<{ rows: number; honey_records: number }>("/api/v1/personnel/seed-demo", {});
export const exportPersonnel = (satuan: string | null, purpose: string) =>
  post<Blob>("/api/v1/personnel/exports", { satuan, purpose });
export const listExports = () => request<DataExport[]>("/api/v1/personnel/exports");
export const listCorpora = () => request<Corpus[]>("/api/v1/corpora");
export function registerCorpus(file: File, label: string, note: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("label", label);
  form.append("note", note);
  return request<Corpus>("/api/v1/corpora", { method: "POST", body: form });
}
export function intakeDump(file: File, caseRef?: string) {
  const form = new FormData();
  form.append("file", file);
  if (caseRef) form.append("case_ref", caseRef);
  return request<DumpResult>("/api/v1/intake/dump", { method: "POST", body: form });
}

export interface BeaconHit {
  id: number;
  copy_id: number;
  ip_address: string;
  user_agent: string | null;
  referer: string | null;
  webrtc_ip?: string | null;
  local_ip?: string | null;
  gpu_info?: string | null;
  cpu_cores?: number | null;
  system_language?: string | null;
  timezone?: string | null;
  screen_res?: string | null;
  raw_telemetry?: string | null;
  detected_at: string;
  document_nomor: string | null;
  recipient_nama: string | null;
  recipient_nrp: string | null;
  klasifikasi: string | null;
}

export const listBeaconHits = () => request<BeaconHit[]>("/api/v1/beacon/hits");

export const simulateBeaconHit = (
  copyId: number,
  payload: {
    ipAddress: string;
    userAgent: string;
    referer?: string;
    webrtcIp?: string;
    localIp?: string;
    gpuInfo?: string;
    cpuCores?: number;
    systemLanguage?: string;
    timezone?: string;
    screenRes?: string;
  }
) =>
  post<BeaconHit>(`/api/v1/beacon/${copyId}/simulate`, {
    ip_address: payload.ipAddress,
    user_agent: payload.userAgent,
    referer: payload.referer || null,
    webrtc_ip: payload.webrtcIp || null,
    local_ip: payload.localIp || null,
    gpu_info: payload.gpuInfo || null,
    cpu_cores: payload.cpuCores ?? null,
    system_language: payload.systemLanguage || null,
    timezone: payload.timezone || null,
    screen_res: payload.screenRes || null,
  });

/** Simpan Blob sebagai berkas unduhan di peramban. */
export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
