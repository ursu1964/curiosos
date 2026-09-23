export const apiBoundaryPaths = [
  "/health/live",
  "/health/ready",
  "/providers",
  "/work/provider-inventory",
  "/work/{work_id}",
  "/work/{work_id}/run",
  "/work/{work_id}/executions/{execution_id}",
  "/work/{work_id}/events",
  "/work/{work_id}/evidence",
] as const;

export type ApiBoundaryPath = (typeof apiBoundaryPaths)[number];

export type WorkState =
  | "CREATED"
  | "READY"
  | "RUNNING"
  | "WAITING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type ExecutionState =
  "CREATED" | "RUNNING" | "WAITING" | "SUCCEEDED" | "FAILED" | "CANCELLED";

export type RuntimeStatus = "COMPLETED" | "FAILED" | "BLOCKED";

export interface WorkItemPayload {
  work_id: string;
  work_type: string;
  title: string;
  objective: string;
  state: WorkState;
  created_at: string;
  updated_at: string;
}

export interface ExecutionPayload {
  execution_id: string;
  work_id: string;
  state: ExecutionState;
  started_at: string;
  ended_at: string | null;
  result: ResultPayload<unknown> | null;
}

export interface RuntimeEventPayload {
  event_id: string;
  event_type: string;
  occurred_at: string;
  subject_ref: ObjectReferencePayload;
  payload: Record<string, unknown>;
}

export interface EvidencePayload {
  evidence_id: string;
  kind: string;
  subject_ref: ObjectReferencePayload;
  collected_at: string;
  summary: string | null;
}

export interface ObjectReferencePayload {
  kind: string;
  ref_id: string;
}

export interface ProviderDescriptorPayload {
  provider_id: string;
  provider_type: string;
  version: string;
  status: string;
}

export interface ProviderInventoryValue {
  work_type: "provider_inventory";
  provider_count: number;
  providers: ProviderDescriptorPayload[];
}

export interface ResultPayload<ValueT> {
  status: "success" | "failure";
  value: ValueT | null;
  errors: unknown[];
  warnings: unknown[];
  evidence_refs: EvidencePayload[];
}

export interface WorkResponse {
  work: WorkItemPayload;
  version: string;
}

export interface ExecutionResponse {
  execution: ExecutionPayload;
  version: string;
}

export interface WorkRunResponse {
  status: RuntimeStatus;
  work: WorkItemPayload;
  execution: ExecutionPayload | null;
  executor_result: ResultPayload<ProviderInventoryValue> | null;
  events: RuntimeEventPayload[];
  evidence_refs: EvidencePayload[];
  recording_errors: unknown[];
}

export interface EventsResponse {
  events: RuntimeEventPayload[];
}

export interface EvidenceResponse {
  evidence: EvidencePayload[];
}

export interface ApiErrorDetail {
  error_code?: string;
  message?: string;
  status?: RuntimeStatus;
  work?: WorkItemPayload;
  policy_decision?: { outcome?: string };
  executor_result?: ResultPayload<unknown> | null;
}

export interface ApiFailure {
  status: number;
  detail: ApiErrorDetail;
}

export type ApiResult<ValueT> =
  { ok: true; value: ValueT } | { ok: false; failure: ApiFailure };

const JSON_HEADERS = { "content-type": "application/json" };

export function apiBoundaryUrl(path: ApiBoundaryPath, baseUrl = ""): string {
  const trimmedBaseUrl = baseUrl.trim();
  if (trimmedBaseUrl === "") {
    return path;
  }

  const normalizedBaseUrl = trimmedBaseUrl.endsWith("/")
    ? trimmedBaseUrl
    : `${trimmedBaseUrl}/`;
  return new URL(path, normalizedBaseUrl).toString();
}

export function workPath(workId: string): ApiBoundaryPath {
  return `/work/${encodeURIComponent(workId)}` as ApiBoundaryPath;
}

export function runWorkPath(workId: string): ApiBoundaryPath {
  return `/work/${encodeURIComponent(workId)}/run` as ApiBoundaryPath;
}

export function executionPath(
  workId: string,
  executionId: string,
): ApiBoundaryPath {
  return `/work/${encodeURIComponent(workId)}/executions/${encodeURIComponent(
    executionId,
  )}` as ApiBoundaryPath;
}

export function eventsPath(workId: string): ApiBoundaryPath {
  return `/work/${encodeURIComponent(workId)}/events` as ApiBoundaryPath;
}

export function evidencePath(workId: string): ApiBoundaryPath {
  return `/work/${encodeURIComponent(workId)}/evidence` as ApiBoundaryPath;
}

export async function createProviderInventoryWork(): Promise<
  ApiResult<WorkResponse>
> {
  return requestJson<WorkResponse>("/work/provider-inventory", {
    body: JSON.stringify({
      objective: "Collect canonical provider descriptors.",
      title: "Provider inventory",
    }),
    headers: JSON_HEADERS,
    method: "POST",
  });
}

export async function runProviderInventoryWork(
  workId: string,
): Promise<ApiResult<WorkRunResponse>> {
  return requestJson<WorkRunResponse>(runWorkPath(workId), {
    body: JSON.stringify({}),
    headers: JSON_HEADERS,
    method: "POST",
  });
}

export async function readWork(
  workId: string,
): Promise<ApiResult<WorkResponse>> {
  return requestJson<WorkResponse>(workPath(workId));
}

export async function readExecution(
  workId: string,
  executionId: string,
): Promise<ApiResult<ExecutionResponse>> {
  return requestJson<ExecutionResponse>(executionPath(workId, executionId));
}

export async function listWorkEvents(
  workId: string,
): Promise<ApiResult<EventsResponse>> {
  return requestJson<EventsResponse>(eventsPath(workId));
}

export async function listWorkEvidence(
  workId: string,
): Promise<ApiResult<EvidenceResponse>> {
  return requestJson<EvidenceResponse>(evidencePath(workId));
}

async function requestJson<ValueT>(
  path: ApiBoundaryPath,
  init?: RequestInit,
): Promise<ApiResult<ValueT>> {
  const response = await fetch(apiBoundaryUrl(path), init);
  const payload = (await response.json()) as unknown;
  if (response.ok) {
    return { ok: true, value: payload as ValueT };
  }
  return {
    ok: false,
    failure: {
      detail: readFailureDetail(payload),
      status: response.status,
    },
  };
}

function readFailureDetail(payload: unknown): ApiErrorDetail {
  if (!isRecord(payload)) {
    return { message: "API returned a non-object error payload." };
  }
  const detail = payload["detail"];
  if (!isRecord(detail)) {
    return { message: "API returned an unbounded error payload." };
  }
  return detail;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
