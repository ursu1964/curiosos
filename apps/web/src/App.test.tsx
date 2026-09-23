import { act, type ReactElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { apiBoundaryPaths, apiBoundaryUrl } from "./apiBoundary";

interface MountedRoot {
  container: HTMLDivElement;
  root: Root;
}

interface MockResponse {
  body: unknown;
  status?: number;
}

interface FetchCall {
  body: string | null;
  path: string;
}

interface DeferredResponse {
  promise: Promise<Response>;
  resolve: (response: MockResponse) => void;
}

const mountedRoots: MountedRoot[] = [];
const originalFetch = globalThis.fetch;

function render(element: ReactElement): HTMLDivElement {
  const container = document.createElement("div");
  document.body.append(container);
  const root = createRoot(container);
  mountedRoots.push({ container, root });

  act(() => {
    root.render(element);
  });

  return container;
}

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
  for (const { container, root } of mountedRoots.splice(0)) {
    act(() => {
      root.unmount();
    });
    container.remove();
  }
});

describe("TASK-M0-009 web work console", () => {
  it("renders the M0 console and exact frozen API route surface", () => {
    const container = render(<App />);

    expect(text(container)).toContain("M0 Work Console");
    expect(text(container)).toContain("@curiosos/curios-contracts");
    expect(apiBoundaryPaths).toEqual([
      "/health/live",
      "/health/ready",
      "/providers",
      "/work/provider-inventory",
      "/work/{work_id}",
      "/work/{work_id}/run",
      "/work/{work_id}/executions/{execution_id}",
      "/work/{work_id}/events",
      "/work/{work_id}/evidence",
    ]);
    expect(
      apiBoundaryUrl("/work/provider-inventory", "http://localhost:8000"),
    ).toBe("http://localhost:8000/work/provider-inventory");
  });

  it("creates and runs provider inventory work through the API boundary", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/work/provider-inventory", ok(workResponse(workA("CREATED")))],
      ["/work/wrk_00000000000000000000000001/run", ok(runResponse())],
    ]);
    const container = render(<App />);

    await click(button(container, "Create Work"));
    await click(button(container, "Run"));

    expect(calls.map((call) => call.path)).toEqual([
      "/work/provider-inventory",
      "/work/wrk_00000000000000000000000001/run",
    ]);
    expect(calls[1]?.body).toBe("{}");
    expect(text(container)).toContain(
      "Provider inventory completed and recorded.",
    );
    expect(text(container)).toContain("wrk_00000000000000000000000001");
    expect(text(container)).toContain("exe_00000000000000000000000001");
    expect(text(container)).toContain("prv_00000000000000000000000001");
    expect(text(container)).toContain("policy.evaluated");
    expect(text(container)).toContain("provider_report");
  });

  it("shows BLOCKED policy truth without treating it as success", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/work/provider-inventory", ok(workResponse(workA("CREATED")))],
      [
        "/work/wrk_00000000000000000000000001/run",
        boundedFailure(403, {
          policy_decision: { outcome: "UNKNOWN" },
          status: "BLOCKED",
          work: workA("CREATED"),
        }),
      ],
    ]);
    const container = render(<App />);

    await click(button(container, "Create Work"));
    await click(button(container, "Run"));

    expect(text(container)).toContain("BLOCKED");
    expect(text(container)).toContain("UNKNOWN");
    expect(text(container)).not.toContain(
      "Provider inventory completed and recorded.",
    );
  });

  it("renders bounded provider failures without native details", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/work/provider-inventory", ok(workResponse(workA("CREATED")))],
      [
        "/work/wrk_00000000000000000000000001/run",
        boundedFailure(502, {
          executor_result: {
            errors: [{ error_code: "PROVIDER_INVENTORY_CATALOG_FAILURE" }],
            evidence_refs: [],
            status: "failure",
            value: null,
            warnings: [],
          },
          status: "FAILED",
          work: workA("FAILED"),
        }),
      ],
    ]);
    const container = render(<App />);

    await click(button(container, "Create Work"));
    await click(button(container, "Run"));

    expect(text(container)).toContain("FAILED");
    expect(text(container)).not.toMatch(/traceback|sqlalchemy|psycopg/i);
  });

  it("refreshes work, execution, events, and evidence through observation routes", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/work/provider-inventory", ok(workResponse(workA("CREATED")))],
      ["/work/wrk_00000000000000000000000001/run", ok(runResponse())],
      [
        "/work/wrk_00000000000000000000000001",
        ok(workResponse(workA("COMPLETED"))),
      ],
      [
        "/work/wrk_00000000000000000000000001/executions/exe_00000000000000000000000001",
        ok({
          execution: executionA("SUCCEEDED"),
          version: "execution-version",
        }),
      ],
      [
        "/work/wrk_00000000000000000000000001/events",
        ok({ events: [eventA("execution.completed")] }),
      ],
      [
        "/work/wrk_00000000000000000000000001/evidence",
        ok({ evidence: [evidenceA("refreshed evidence")] }),
      ],
    ]);
    const container = render(<App />);

    await click(button(container, "Create Work"));
    await click(button(container, "Run"));
    await click(button(container, "Refresh"));

    expect(calls.map((call) => call.path)).toContain(
      "/work/wrk_00000000000000000000000001/events",
    );
    expect(text(container)).toContain("Recorded runtime truth refreshed.");
    expect(text(container)).toContain("refreshed evidence");
  });

  it("does not let stale observation responses overwrite newly selected work", async () => {
    const staleWork = deferredResponse();
    const staleExecution = deferredResponse();
    const staleEvents = deferredResponse();
    const staleEvidence = deferredResponse();
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/work/provider-inventory", ok(workResponse(workA("CREATED")))],
      ["/work/wrk_00000000000000000000000001/run", ok(runResponse())],
      ["/work/wrk_00000000000000000000000001", staleWork.promise],
      [
        "/work/wrk_00000000000000000000000001/executions/exe_00000000000000000000000001",
        staleExecution.promise,
      ],
      ["/work/wrk_00000000000000000000000001/events", staleEvents.promise],
      ["/work/wrk_00000000000000000000000001/evidence", staleEvidence.promise],
      ["/work/provider-inventory", ok(workResponse(workB("CREATED")))],
    ]);
    const container = render(<App />);

    await click(button(container, "Create Work"));
    await click(button(container, "Run"));
    await click(button(container, "Refresh"));
    await click(button(container, "Create Work"));
    staleWork.resolve({ body: workResponse(workA("COMPLETED")) });
    staleExecution.resolve({
      body: {
        execution: executionA("SUCCEEDED"),
        version: "execution-version",
      },
    });
    staleEvents.resolve({ body: { events: [eventA("execution.completed")] } });
    staleEvidence.resolve({
      body: { evidence: [evidenceA("stale evidence")] },
    });
    await flush();

    expect(text(container)).toContain("wrk_00000000000000000000000002");
    expect(text(container)).not.toContain("wrk_00000000000000000000000001");
    expect(text(container)).not.toContain("stale evidence");
  });
});

function installFetchMock(
  calls: FetchCall[],
  responses: [string, Promise<Response>][],
): void {
  const mockFetch: typeof fetch = async (
    input: RequestInfo | URL,
    init?: RequestInit,
  ) => {
    const path = requestPath(input);
    const next = responses.shift();
    calls.push({
      body: typeof init?.body === "string" ? init.body : null,
      path,
    });
    if (next === undefined) {
      return response({ detail: { error_code: "UNEXPECTED_FETCH" } }, 500);
    }
    expect(path).toBe(next[0]);
    return next[1];
  };
  globalThis.fetch = mockFetch;
}

function requestPath(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  if (input instanceof URL) {
    return input.pathname;
  }
  return new URL(input.url).pathname;
}

function ok(body: unknown): Promise<Response> {
  return Promise.resolve(response(body, 200));
}

function boundedFailure(status: number, detail: unknown): Promise<Response> {
  return Promise.resolve(response({ detail }, status));
}

function response(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    headers: { "content-type": "application/json" },
    status,
  });
}

function deferredResponse(): DeferredResponse {
  let resolveResponse: ((response: MockResponse) => void) | undefined;
  const promise = new Promise<Response>((resolve) => {
    resolveResponse = (mockResponse: MockResponse) => {
      resolve(response(mockResponse.body, mockResponse.status ?? 200));
    };
  });
  return {
    promise,
    resolve(mockResponse) {
      if (resolveResponse === undefined) {
        throw new Error("deferred response was not initialized");
      }
      resolveResponse(mockResponse);
    },
  };
}

async function click(element: HTMLButtonElement): Promise<void> {
  await act(async () => {
    element.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    await Promise.resolve();
  });
}

async function flush(): Promise<void> {
  await act(async () => {
    await Promise.resolve();
  });
}

function button(container: HTMLElement, label: string): HTMLButtonElement {
  const buttons = [...container.querySelectorAll("button")];
  const found = buttons.find((item) => item.textContent.includes(label));
  if (!(found instanceof HTMLButtonElement)) {
    throw new Error(`button not found: ${label}`);
  }
  return found;
}

function text(container: HTMLElement): string {
  return container.textContent;
}

function workResponse(work: ReturnType<typeof workA>): unknown {
  return { version: `${work.work_id}-version`, work };
}

function runResponse(): unknown {
  return {
    evidence_refs: [
      evidenceA("Provider inventory returned 1 provider descriptor(s)."),
    ],
    events: [
      eventA("policy.evaluated"),
      eventA("execution.started"),
      eventA("evidence.produced"),
      eventA("execution.completed"),
    ],
    execution: executionA("SUCCEEDED"),
    executor_result: {
      errors: [],
      evidence_refs: [
        evidenceA("Provider inventory returned 1 provider descriptor(s)."),
      ],
      status: "success",
      value: {
        provider_count: 1,
        providers: [
          {
            provider_id: "prv_00000000000000000000000001",
            provider_type: "model",
            status: "available",
            version: "1.0.0",
          },
        ],
        work_type: "provider_inventory",
      },
      warnings: [],
    },
    recording_errors: [],
    runtime_status: "COMPLETED",
    status: "COMPLETED",
    work: workA("COMPLETED"),
  };
}

function workA(state: string): {
  created_at: string;
  objective: string;
  state: string;
  title: string;
  updated_at: string;
  work_id: string;
  work_type: string;
} {
  return {
    created_at: "2026-09-23T00:00:00Z",
    objective: "Collect canonical provider descriptors.",
    state,
    title: "Provider inventory",
    updated_at: "2026-09-23T00:00:01Z",
    work_id: "wrk_00000000000000000000000001",
    work_type: "provider_inventory",
  };
}

function workB(state: string): ReturnType<typeof workA> {
  return {
    ...workA(state),
    work_id: "wrk_00000000000000000000000002",
  };
}

function executionA(state: string): {
  ended_at: string | null;
  execution_id: string;
  result: null;
  started_at: string;
  state: string;
  work_id: string;
} {
  return {
    ended_at: state === "SUCCEEDED" ? "2026-09-23T00:00:02Z" : null,
    execution_id: "exe_00000000000000000000000001",
    result: null,
    started_at: "2026-09-23T00:00:01Z",
    state,
    work_id: "wrk_00000000000000000000000001",
  };
}

function eventA(eventType: string): {
  event_id: string;
  event_type: string;
  occurred_at: string;
  payload: Record<string, unknown>;
  subject_ref: { kind: string; ref_id: string };
} {
  return {
    event_id: `evt_0000000000000000000000000${String(eventType.length % 10)}`,
    event_type: eventType,
    occurred_at: "2026-09-23T00:00:01Z",
    payload: {},
    subject_ref: { kind: "work", ref_id: "wrk_00000000000000000000000001" },
  };
}

function evidenceA(summary: string): {
  collected_at: string;
  evidence_id: string;
  kind: string;
  subject_ref: { kind: string; ref_id: string };
  summary: string;
} {
  return {
    collected_at: "2026-09-23T00:00:02Z",
    evidence_id: "evd_00000000000000000000000001",
    kind: "provider_report",
    subject_ref: { kind: "work", ref_id: "wrk_00000000000000000000000001" },
    summary,
  };
}
