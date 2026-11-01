import type { components } from "./api-types";

type Schemas = components["schemas"];
export type Recipient = Schemas["RecipientOut"];
export type RecipientInput = Schemas["RecipientIn"];
export type DocumentRow = Schemas["DocumentOut"];
export type DocumentInput = Schemas["DocumentIn"];
export type CopyIssued = Schemas["CopyIssued"];
export type CopyRow = Schemas["CopyOut"];
export type IntakeResult = Schemas["IntakeResult"];
export type LedgerEntry = Schemas["LedgerEntryOut"];
export type VerifyResult = Schemas["VerifyOut"];

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ACTOR_KEY = "sidik.actor";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

/** Nama petugas yang dikirim sebagai X-Actor dan tercatat di buku besar audit. */
export function getActor(): string {
  try {
    return localStorage.getItem(ACTOR_KEY) || "anonim";
  } catch {
    return "anonim";
  }
}

export function setActor(name: string): void {
  try {
    localStorage.setItem(ACTOR_KEY, name);
  } catch {
    /* penyimpanan diblokir: nama petugas tidak diingat antar sesi */
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      cache: "no-store",
      ...init,
      headers: { "Content-Type": "application/json", "X-Actor": getActor(), ...init.headers },
    });
  } catch {
    throw new ApiError("Tidak dapat terhubung ke server API.", 0);
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
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

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
