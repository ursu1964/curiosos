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
      "/m1/intents/decompose",
      "/m1/dag/run-once",
      "/m1/verification/complete",
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

describe("TASK-M1-014 web cognitive loop console", () => {
  it("decomposes a supported intent through the exact M1 API boundary", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/m1/intents/decompose", created(m1DecompositionResponse())],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));

    expect(calls.map((call) => call.path)).toEqual(["/m1/intents/decompose"]);
    expect(JSON.parse(calls[0]?.body ?? "{}")).toEqual({
      objective: "Implement a bounded change",
    });
    expect(text(container)).toContain("Intent decomposed into 3 work item(s).");
    expect(text(container)).toContain("SUPPORTED");
    expect(text(container)).toContain("inspect_current_state");
  });

  it("renders unsupported decomposition as a bounded domain outcome", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      [
        "/m1/intents/decompose",
        created({
          ...m1DecompositionResponse(),
          dag: null,
          decomposition: {
            ...m1DecompositionResponse().decomposition,
            status: "UNSUPPORTED",
            work_items: [],
          },
        }),
      ],
    ]);
    const container = render(<App />);
    changeInput(container, "Address a philosophical question.");

    await click(button(container, "Decompose Intent"));

    expect(text(container)).toContain("UNSUPPORTED");
    expect(text(container)).toContain("unsupported M1 domain outcome");
    expect(text(container)).not.toContain("M1_API_MALFORMED_REQUEST");
  });

  it("runs the DAG through BoundedM1DagRunner request authority", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/m1/intents/decompose", created(m1DecompositionResponse())],
      ["/m1/dag/run-once", ok(m1RunnerResponse())],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));
    await click(button(container, "Run DAG Once"));

    const request = JSON.parse(calls[1]?.body ?? "{}") as Record<
      string,
      unknown
    >;
    expect(calls.map((call) => call.path)).toEqual([
      "/m1/intents/decompose",
      "/m1/dag/run-once",
    ]);
    expect(request["max_concurrency"]).toBe(1);
    expect(request["work_items"]).toBeInstanceOf(Array);
    expect(request["routing_decisions"]).toBeInstanceOf(Array);
    expect(text(container)).toContain(
      "DAG run COMPLETED with 1 executed node(s).",
    );
    expect(text(container)).toContain("EXECUTED");
    expect(text(container)).toContain("execution.completed");
  });

  it("preserves ROUTE_NOT_EXECUTABLE as domain truth without executor artifacts", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/m1/intents/decompose", created(m1DecompositionResponse())],
      [
        "/m1/dag/run-once",
        ok(m1RunnerResponse("BLOCKED", "ROUTE_NOT_EXECUTABLE")),
      ],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));
    await click(button(container, "Run DAG Once"));

    expect(text(container)).toContain("ROUTE_NOT_EXECUTABLE");
    expect(text(container)).toContain("Evidence0");
    expect(text(container)).not.toContain("verification.completed");
  });

  it("completes verification through the bounded verification loop", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/m1/intents/decompose", created(m1DecompositionResponse())],
      ["/m1/dag/run-once", ok(m1RunnerResponse())],
      ["/m1/verification/complete", ok(m1VerificationResponse("APPROVED"))],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));
    await click(button(container, "Run DAG Once"));
    await click(button(container, "Complete Verification"));

    expect(calls.map((call) => call.path)).toEqual([
      "/m1/intents/decompose",
      "/m1/dag/run-once",
      "/m1/verification/complete",
    ]);
    expect(JSON.parse(calls[2]?.body ?? "{}")).toMatchObject({
      attempts: [{ outcome: "passed" }],
      max_iterations: 2,
    });
    expect(text(container)).toContain("Verification APPROVED.");
    expect(text(container)).toContain("verification.completed");
  });

  it("renders REJECTED and DEFERRED verification decisions as domain outcomes", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/m1/intents/decompose", created(m1DecompositionResponse())],
      ["/m1/dag/run-once", ok(m1RunnerResponse())],
      ["/m1/verification/complete", ok(m1VerificationResponse("REJECTED"))],
      ["/m1/verification/complete", ok(m1VerificationResponse("DEFERRED"))],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));
    await click(button(container, "Run DAG Once"));
    await click(button(container, "Complete Verification"));
    await click(button(container, "Complete Verification"));

    expect(text(container)).toContain("Verification DEFERRED.");
    expect(text(container)).toContain("DEFERRED");
    expect(text(container)).not.toContain("HTTP_");
  });

  it("renders bounded API errors without raw secret-shaped details", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      [
        "/m1/intents/decompose",
        boundedFailure(400, {
          detail: secretProbe(),
          error_code: "M1_API_MALFORMED_REQUEST",
          message: "M1 API request is malformed.",
        }),
      ],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));

    expect(text(container)).toContain("M1_API_MALFORMED_REQUEST");
    expect(text(container)).toContain("M1 API request is malformed.");
    expect(text(container)).not.toContain(secretProbe());
  });

  it("prevents double-submit while an M1 request is in flight", async () => {
    const pending = deferredResponse();
    const calls: FetchCall[] = [];
    installFetchMock(calls, [["/m1/intents/decompose", pending.promise]]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));
    await click(button(container, "Decomposing..."));
    pending.resolve({ body: m1DecompositionResponse(), status: 201 });
    await flush();

    expect(calls).toHaveLength(1);
  });

  it("replaces prior M1 results when a new intent is selected", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/m1/intents/decompose", created(m1DecompositionResponse())],
      ["/m1/dag/run-once", ok(m1RunnerResponse())],
      [
        "/m1/intents/decompose",
        created(m1DecompositionResponse(2, "Implement another bounded change")),
      ],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));
    await click(button(container, "Run DAG Once"));
    changeInput(container, "Implement another bounded change");
    await click(button(container, "Decompose Intent"));

    expect(text(container)).toContain("int_00000000000000000000000002");
    expect(panelText(container, "Intent")).toContain(
      "Implement another bounded change",
    );
    expect(text(container)).not.toContain("DAG run COMPLETED");
  });

  it("does not combine selected intent identity with unsubmitted objective text", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/m1/intents/decompose", created(m1DecompositionResponse())],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));
    changeInput(container, "Implement another bounded change");

    const intentPanel = panelText(container, "Intent");
    expect(intentPanel).toContain("int_00000000000000000000000001");
    expect(intentPanel).toContain("Implement a bounded change");
    expect(intentPanel).not.toContain("Implement another bounded change");
  });

  it("keeps canonical A visible when draft B decomposition fails", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/m1/intents/decompose", created(m1DecompositionResponse())],
      [
        "/m1/intents/decompose",
        boundedFailure(400, {
          error_code: "M1_API_MALFORMED_REQUEST",
          message: "M1 API request is malformed.",
        }),
      ],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));
    changeInput(container, "Implement another bounded change");
    await click(button(container, "Decompose Intent"));

    const intentPanel = panelText(container, "Intent");
    expect(intentPanel).toContain("int_00000000000000000000000001");
    expect(intentPanel).toContain("Implement a bounded change");
    expect(intentPanel).not.toContain("Implement another bounded change");
    expect(text(container)).toContain("M1_API_MALFORMED_REQUEST");
  });

  it("does not leak unsubmitted draft text into run or verification requests", async () => {
    const calls: FetchCall[] = [];
    installFetchMock(calls, [
      ["/m1/intents/decompose", created(m1DecompositionResponse())],
      ["/m1/dag/run-once", ok(m1RunnerResponse())],
      ["/m1/verification/complete", ok(m1VerificationResponse("APPROVED"))],
    ]);
    const container = render(<App />);

    await click(button(container, "Decompose Intent"));
    changeInput(container, "Implement another bounded change");
    await click(button(container, "Run DAG Once"));
    await click(button(container, "Complete Verification"));

    expect(calls[1]?.path).toBe("/m1/dag/run-once");
    expect(calls[1]?.body).not.toContain("Implement another bounded change");
    expect(calls[2]?.path).toBe("/m1/verification/complete");
    expect(calls[2]?.body).not.toContain("Implement another bounded change");
    expect(panelText(container, "Runner")).toContain("EXECUTED");
    expect(panelText(container, "Verification")).toContain("APPROVED");
    expect(panelText(container, "M1 Events")).not.toContain(
      "Implement another bounded change",
    );
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

function created(body: unknown): Promise<Response> {
  return Promise.resolve(response(body, 201));
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

function changeInput(container: HTMLElement, value: string): void {
  const input = container.querySelector("#m1-intent-objective");
  if (!(input instanceof HTMLInputElement)) {
    throw new Error("M1 intent input not found");
  }
  act(() => {
    const descriptor = Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    );
    if (descriptor?.set === undefined) {
      throw new Error("HTML input value setter not found");
    }
    // eslint-disable-next-line @typescript-eslint/unbound-method
    Reflect.apply(descriptor.set, input, [value]);
    input.dispatchEvent(new Event("input", { bubbles: true }));
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

function panelText(container: HTMLElement, title: string): string {
  const headings = [...container.querySelectorAll("h2")];
  const heading = headings.find((item) => item.textContent === title);
  const panel = heading?.closest("section");
  if (panel === null || panel === undefined) {
    throw new Error(`panel not found: ${title}`);
  }
  return panel.textContent;
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

function m1DecompositionResponse(
  ordinal = 1,
  objective = "Implement a bounded change",
): {
  dag: {
    created_at: string;
    dag_id: string;
    nodes: {
      dependencies: string[];
      node_id: string;
      work_ref: { kind: string; ref_id: string };
    }[];
  };
  decomposition: {
    problem: {
      intent_ref: { kind: string; ref_id: string };
      problem_id: string;
      statement: string;
    };
    status: string;
    work_items: ReturnType<typeof m1Work>[];
  };
  intent: {
    context_refs: unknown[];
    intent_id: string;
    objective: string;
    source_ref: null;
    submitted_at: string;
  };
} {
  const work = [
    m1Work("inspect_current_state", ordinal),
    m1Work("apply_bounded_change", ordinal + 1),
    m1Work("verify_bounded_change", ordinal + 2),
  ];
  return {
    dag: {
      created_at: "2026-09-27T00:00:00Z",
      dag_id: fixedId("dag", ordinal),
      nodes: work.map((item, index) => ({
        dependencies: index === 0 ? [] : [work[index - 1]?.work_id ?? ""],
        node_id: item.work_id,
        work_ref: { kind: "work", ref_id: item.work_id },
      })),
    },
    decomposition: {
      problem: {
        intent_ref: { kind: "intent", ref_id: fixedId("int", ordinal) },
        problem_id: fixedId("prb", ordinal),
        statement: objective,
      },
      status: "SUPPORTED",
      work_items: work,
    },
    intent: {
      context_refs: [],
      intent_id: fixedId("int", ordinal),
      objective,
      source_ref: null,
      submitted_at: "2026-09-27T00:00:00Z",
    },
  };
}

function m1Work(
  workType: string,
  ordinal: number,
): {
  created_at: string;
  objective: string;
  required_capabilities: { capability_id: string }[];
  state: string;
  title: string;
  updated_at: string;
  work_id: string;
  work_type: string;
} {
  return {
    created_at: "2026-09-27T00:00:00Z",
    objective: `Run ${workType}.`,
    required_capabilities: [{ capability_id: fixedId("cap", ordinal) }],
    state: "READY",
    title: workType.replaceAll("_", " "),
    updated_at: "2026-09-27T00:00:00Z",
    work_id: fixedId("wrk", ordinal),
    work_type: workType,
  };
}

function m1RunnerResponse(
  status = "EXECUTED",
  reason = "EXECUTED",
): {
  runner_result: {
    dag_state: Record<string, unknown>;
    evidence_refs: ReturnType<typeof evidenceA>[];
    events: ReturnType<typeof eventA>[];
    node_results: unknown[];
    status: string;
  };
} {
  const executed = status === "EXECUTED";
  const nodeResult = {
    executor_outcome: executed
      ? {
          event: eventA("execution.completed"),
          evidence_refs: [evidenceA("M1 deterministic executor evidence.")],
          result: {
            errors: [],
            evidence_refs: [evidenceA("M1 deterministic executor evidence.")],
            status: "success",
            value: { work_type: "inspect_current_state" },
            warnings: [],
          },
          status: "COMPLETED",
        }
      : null,
    readiness: "READY",
    reason,
    routing_decision_ref: {
      kind: "routing_decision",
      ref_id: fixedId("dec", 1),
    },
    status,
    work_ref: { kind: "work", ref_id: fixedId("wrk", 1) },
  };
  return {
    runner_result: {
      dag_state: { status: executed ? "COMPLETED" : "BLOCKED" },
      evidence_refs: executed
        ? [evidenceA("M1 deterministic executor evidence.")]
        : [],
      events: executed ? [eventA("execution.completed")] : [],
      node_results: [nodeResult],
      status: executed ? "COMPLETED" : "BLOCKED",
    },
  };
}

function m1VerificationResponse(decision: string): {
  verification_result: {
    completion_decision: string;
    event: ReturnType<typeof eventA> | null;
    evidence_refs: ReturnType<typeof evidenceA>[];
    iterations_used: number;
    outcome: string;
    reason: string;
    verification_ref: {
      status: string;
      subject_ref: { kind: string; ref_id: string };
      verification_id: string;
    };
    work_ref: { kind: string; ref_id: string };
  };
} {
  return {
    verification_result: {
      completion_decision: decision,
      event: decision === "DEFERRED" ? null : eventA("verification.completed"),
      evidence_refs:
        decision === "DEFERRED" ? [] : [evidenceA("verified evidence")],
      iterations_used: decision === "DEFERRED" ? 2 : 1,
      outcome:
        decision === "APPROVED"
          ? "passed"
          : decision === "REJECTED"
            ? "failed"
            : "inconclusive",
      reason:
        decision === "DEFERRED"
          ? "VERIFICATION_EXHAUSTED"
          : "TERMINAL_ATTEMPT_RECORDED",
      verification_ref: {
        status: decision,
        subject_ref: { kind: "work", ref_id: fixedId("wrk", 1) },
        verification_id: fixedId("ver", 1),
      },
      work_ref: { kind: "work", ref_id: fixedId("wrk", 1) },
    },
  };
}

function fixedId(prefix: string, ordinal: number): string {
  return `${prefix}_${String(ordinal).padStart(26, "0")}`;
}

function secretProbe(): string {
  return ["tok", "en"].join("") + "=" + ["super", "secret"].join("-");
}
