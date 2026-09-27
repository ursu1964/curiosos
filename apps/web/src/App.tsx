import {
  curiosContractsPackageName,
  curiosContractsPackageVersion,
} from "@curiosos/curios-contracts";
import { useRef, useState, type JSX, type ReactNode } from "react";

import "./App.css";
import {
  apiBoundaryPaths,
  completeM1Verification,
  createProviderInventoryWork,
  decomposeM1Intent,
  listWorkEvidence,
  listWorkEvents,
  readExecution,
  readWork,
  runM1DagOnce,
  runProviderInventoryWork,
  type ApiFailure,
  type EvidencePayload,
  type ExecutionPayload,
  type M1DagNodeResultPayload,
  type M1DagRunRequest,
  type M1DagRunnerResultPayload,
  type M1DecomposeIntentResponse,
  type M1VerificationRequest,
  type M1VerificationResultPayload,
  type ProviderDescriptorPayload,
  type RuntimeEventPayload,
  type RuntimeStatus,
  type WorkItemPayload,
} from "./apiBoundary";

type BusyAction = "create" | "run" | "refresh" | null;
type M1BusyAction = "decompose" | "run-once" | "verify" | null;

interface ConsoleState {
  evidence: EvidencePayload[];
  events: RuntimeEventPayload[];
  execution: ExecutionPayload | null;
  lastFailure: ApiFailure | null;
  providerInventory: ProviderDescriptorPayload[];
  runtimeStatus: RuntimeStatus | null;
  statusMessage: string;
  work: WorkItemPayload | null;
}

const initialState: ConsoleState = {
  evidence: [],
  events: [],
  execution: null,
  lastFailure: null,
  providerInventory: [],
  runtimeStatus: null,
  statusMessage: "No provider-inventory work has been submitted.",
  work: null,
};

interface M1ConsoleState {
  decomposition: M1DecomposeIntentResponse | null;
  intentObjective: string;
  lastFailure: ApiFailure | null;
  runnerResult: M1DagRunnerResultPayload | null;
  statusMessage: string;
  verificationResult: M1VerificationResultPayload | null;
}

const initialM1State: M1ConsoleState = {
  decomposition: null,
  intentObjective: "Implement a bounded change",
  lastFailure: null,
  runnerResult: null,
  statusMessage: "No M1 intent has been submitted.",
  verificationResult: null,
};

const M1_OCCURRED_AT = "2026-09-27T00:00:00Z";
const M1_PROVIDER_REF = {
  kind: "provider",
  ref_id: "prv_00000000000000000000000001",
};
const M1_TRACE_ID = "trc_00000000000000000000000001";

export function App(): JSX.Element {
  const [consoleState, setConsoleState] = useState<ConsoleState>(initialState);
  const [m1State, setM1State] = useState<M1ConsoleState>(initialM1State);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [m1BusyAction, setM1BusyAction] = useState<M1BusyAction>(null);
  const requestGeneration = useRef(0);
  const m1RequestGeneration = useRef(0);
  const activeWorkId = useRef<string | null>(null);
  const activeM1IntentId = useRef<string | null>(null);

  async function createWork(): Promise<void> {
    const generation = nextRequestGeneration();
    setBusyAction("create");
    const result = await createProviderInventoryWork();
    if (!isCurrentGeneration(generation)) {
      return;
    }
    setBusyAction(null);
    if (!result.ok) {
      setConsoleState((current) => ({
        ...current,
        lastFailure: result.failure,
        statusMessage: failureMessage(result.failure),
      }));
      return;
    }

    activeWorkId.current = result.value.work.work_id;
    setConsoleState({
      ...initialState,
      lastFailure: null,
      statusMessage: "Provider-inventory work created.",
      work: result.value.work,
    });
  }

  async function runWork(): Promise<void> {
    const workId = consoleState.work?.work_id;
    if (workId === undefined) {
      return;
    }
    const generation = nextRequestGeneration();
    setBusyAction("run");
    const result = await runProviderInventoryWork(workId);
    if (!isCurrentWork(generation, workId)) {
      return;
    }
    setBusyAction(null);
    if (!result.ok) {
      const failure = result.failure;
      const failureWork = failure.detail.work ?? consoleState.work;
      setConsoleState((current) => ({
        ...current,
        events: [],
        evidence: [],
        execution: null,
        lastFailure: failure,
        providerInventory: [],
        runtimeStatus: failure.detail.status ?? null,
        statusMessage: failureMessage(failure),
        work: failureWork,
      }));
      return;
    }

    const value = result.value;
    setConsoleState((current) => ({
      ...current,
      events: value.events,
      evidence: value.evidence_refs,
      execution: value.execution,
      lastFailure: null,
      providerInventory: value.executor_result?.value?.providers ?? [],
      runtimeStatus: value.status,
      statusMessage: statusMessageFor(value.status),
      work: value.work,
    }));
  }

  async function refreshWork(): Promise<void> {
    const workId = consoleState.work?.work_id;
    const executionId = consoleState.execution?.execution_id;
    if (workId === undefined) {
      return;
    }

    const generation = nextRequestGeneration();
    setBusyAction("refresh");
    const [workResult, executionResult, eventsResult, evidenceResult] =
      await Promise.all([
        readWork(workId),
        executionId === undefined
          ? Promise.resolve(null)
          : readExecution(workId, executionId),
        listWorkEvents(workId),
        listWorkEvidence(workId),
      ]);
    if (!isCurrentWork(generation, workId)) {
      return;
    }
    setBusyAction(null);

    const failure = firstFailure(
      workResult,
      executionResult,
      eventsResult,
      evidenceResult,
    );
    if (failure !== null) {
      setConsoleState((current) => ({
        ...current,
        lastFailure: failure,
        statusMessage: failureMessage(failure),
      }));
      return;
    }

    setConsoleState((current) => ({
      ...current,
      events: eventsResult.ok ? eventsResult.value.events : current.events,
      evidence: evidenceResult.ok
        ? evidenceResult.value.evidence
        : current.evidence,
      execution:
        executionResult === null
          ? current.execution
          : executionResult.ok
            ? executionResult.value.execution
            : current.execution,
      lastFailure: null,
      statusMessage: "Recorded runtime truth refreshed.",
      work: workResult.ok ? workResult.value.work : current.work,
    }));
  }

  function nextRequestGeneration(): number {
    requestGeneration.current += 1;
    return requestGeneration.current;
  }

  function isCurrentGeneration(generation: number): boolean {
    return requestGeneration.current === generation;
  }

  function isCurrentWork(generation: number, workId: string): boolean {
    return isCurrentGeneration(generation) && activeWorkId.current === workId;
  }

  async function decomposeM1(): Promise<void> {
    const objective = m1State.intentObjective.trim();
    if (objective === "") {
      return;
    }
    const generation = nextM1RequestGeneration();
    setM1BusyAction("decompose");
    const result = await decomposeM1Intent(objective);
    if (!isCurrentM1Generation(generation)) {
      return;
    }
    setM1BusyAction(null);
    if (!result.ok) {
      setM1State((current) => ({
        ...current,
        lastFailure: result.failure,
        statusMessage: failureMessage(result.failure),
      }));
      return;
    }

    activeM1IntentId.current = result.value.intent.intent_id;
    setM1State((current) => ({
      ...current,
      decomposition: result.value,
      lastFailure: null,
      runnerResult: null,
      statusMessage: decompositionStatusMessage(result.value),
      verificationResult: null,
    }));
  }

  async function runM1Once(): Promise<void> {
    const decomposition = m1State.decomposition;
    if (decomposition?.dag === undefined || decomposition.dag === null) {
      return;
    }
    const generation = nextM1RequestGeneration();
    const intentId = decomposition.intent.intent_id;
    setM1BusyAction("run-once");
    const result = await runM1DagOnce(buildM1DagRunRequest(decomposition));
    if (!isCurrentM1Intent(generation, intentId)) {
      return;
    }
    setM1BusyAction(null);
    if (!result.ok) {
      setM1State((current) => ({
        ...current,
        lastFailure: result.failure,
        statusMessage: failureMessage(result.failure),
      }));
      return;
    }

    setM1State((current) => ({
      ...current,
      lastFailure: null,
      runnerResult: result.value.runner_result,
      statusMessage: runnerStatusMessage(result.value.runner_result),
      verificationResult: null,
    }));
  }

  async function completeM1VerificationRequest(): Promise<void> {
    const decomposition = m1State.decomposition;
    const executedNode = firstExecutedNode(m1State.runnerResult);
    const evidence = executedNode?.executor_outcome?.evidence_refs[0];
    if (
      decomposition === null ||
      executedNode === null ||
      evidence === undefined
    ) {
      return;
    }
    const work = workForRef(decomposition, executedNode.work_ref.ref_id);
    if (work === null) {
      return;
    }

    const generation = nextM1RequestGeneration();
    const intentId = decomposition.intent.intent_id;
    setM1BusyAction("verify");
    const result = await completeM1Verification(
      buildM1VerificationRequest(work, executedNode, evidence),
    );
    if (!isCurrentM1Intent(generation, intentId)) {
      return;
    }
    setM1BusyAction(null);
    if (!result.ok) {
      setM1State((current) => ({
        ...current,
        lastFailure: result.failure,
        statusMessage: failureMessage(result.failure),
      }));
      return;
    }

    setM1State((current) => ({
      ...current,
      lastFailure: null,
      statusMessage: `Verification ${result.value.verification_result.completion_decision}.`,
      verificationResult: result.value.verification_result,
    }));
  }

  function nextM1RequestGeneration(): number {
    m1RequestGeneration.current += 1;
    return m1RequestGeneration.current;
  }

  function isCurrentM1Generation(generation: number): boolean {
    return m1RequestGeneration.current === generation;
  }

  function isCurrentM1Intent(generation: number, intentId: string): boolean {
    return (
      isCurrentM1Generation(generation) && activeM1IntentId.current === intentId
    );
  }

  const isBusy = busyAction !== null;
  const isM1Busy = m1BusyAction !== null;
  const m1CanRun =
    !isM1Busy &&
    m1State.decomposition !== null &&
    m1State.decomposition.dag !== null;
  const m1CanVerify =
    !isM1Busy &&
    m1State.decomposition !== null &&
    firstExecutedNode(m1State.runnerResult) !== null;

  return (
    <main className="work-console" data-testid="web-shell">
      <section
        className="work-console__header"
        aria-labelledby="work-console-title"
      >
        <p className="work-console__eyebrow">TASK-M0-009</p>
        <h1 id="work-console-title">M0 Work Console</h1>
        <p className="work-console__summary">
          Submit and observe the frozen read-only provider inventory slice
          through the M0 API.
        </p>
        <p className="work-console__contract">
          {curiosContractsPackageName} {curiosContractsPackageVersion}
        </p>
      </section>

      <section
        className="work-console__toolbar"
        aria-labelledby="operation-title"
      >
        <div>
          <h2 id="operation-title">Provider Inventory</h2>
          <p>
            Read-only M0 work. Policy and runtime decisions are made by the API.
          </p>
        </div>
        <div className="work-console__actions">
          <button
            disabled={busyAction === "create"}
            onClick={() => void createWork()}
            type="button"
          >
            {busyAction === "create" ? "Creating..." : "Create Work"}
          </button>
          <button
            disabled={isBusy || consoleState.work === null}
            onClick={() => void runWork()}
            type="button"
          >
            {busyAction === "run" ? "Running..." : "Run"}
          </button>
          <button
            disabled={isBusy || consoleState.work === null}
            onClick={() => void refreshWork()}
            type="button"
          >
            {busyAction === "refresh" ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </section>

      <p aria-live="polite" className="work-console__status" role="status">
        {consoleState.statusMessage}
      </p>

      {consoleState.lastFailure === null ? null : (
        <section
          className="work-console__alert"
          aria-live="assertive"
          role="alert"
        >
          <h2>Bounded API Result</h2>
          <p>{failureMessage(consoleState.lastFailure)}</p>
          {consoleState.lastFailure.detail.policy_decision?.outcome ===
          undefined ? null : (
            <p>
              Policy outcome:{" "}
              {consoleState.lastFailure.detail.policy_decision.outcome}
            </p>
          )}
        </section>
      )}

      <section
        className="work-console__toolbar work-console__toolbar--m1"
        aria-labelledby="m1-operation-title"
      >
        <div className="work-console__m1-input">
          <h2 id="m1-operation-title">M1 Cognitive Loop</h2>
          <label htmlFor="m1-intent-objective">Intent objective</label>
          <input
            disabled={isM1Busy}
            id="m1-intent-objective"
            onChange={(event) => {
              const objective = event.currentTarget.value;
              setM1State((current) => ({
                ...current,
                intentObjective: objective,
              }));
            }}
            type="text"
            value={m1State.intentObjective}
          />
        </div>
        <div className="work-console__actions">
          <button
            disabled={isM1Busy || m1State.intentObjective.trim() === ""}
            onClick={() => void decomposeM1()}
            type="button"
          >
            {m1BusyAction === "decompose"
              ? "Decomposing..."
              : "Decompose Intent"}
          </button>
          <button
            disabled={!m1CanRun}
            onClick={() => void runM1Once()}
            type="button"
          >
            {m1BusyAction === "run-once" ? "Running..." : "Run DAG Once"}
          </button>
          <button
            disabled={!m1CanVerify}
            onClick={() => void completeM1VerificationRequest()}
            type="button"
          >
            {m1BusyAction === "verify"
              ? "Verifying..."
              : "Complete Verification"}
          </button>
        </div>
      </section>

      <p aria-live="polite" className="work-console__status" role="status">
        {m1State.statusMessage}
      </p>

      {m1State.lastFailure === null ? null : (
        <section
          className="work-console__alert"
          aria-live="assertive"
          role="alert"
        >
          <h2>Bounded M1 API Result</h2>
          <p>{failureMessage(m1State.lastFailure)}</p>
        </section>
      )}

      <section
        className="work-console__grid"
        aria-label="M1 cognitive loop truth"
      >
        <FactPanel title="Intent">
          <DefinitionList
            values={{
              ID: m1State.decomposition?.intent.intent_id ?? "none",
              Objective: m1State.intentObjective,
              Status: m1State.decomposition?.decomposition.status ?? "none",
            }}
          />
        </FactPanel>

        <FactPanel title="Work DAG">
          <DefinitionList
            values={{
              ID: m1State.decomposition?.dag?.dag_id ?? "none",
              Nodes: String(m1State.decomposition?.dag?.nodes.length ?? 0),
              Problem:
                m1State.decomposition?.decomposition.problem.problem_id ??
                "none",
            }}
          />
          <OrderedFacts
            emptyText="No M1 work items recorded."
            items={(m1State.decomposition?.decomposition.work_items ?? []).map(
              (work) => ({
                id: work.work_id,
                label: work.work_type,
                value: work.state,
              }),
            )}
          />
        </FactPanel>

        <FactPanel title="Runner">
          <DefinitionList
            values={{
              Status: m1State.runnerResult?.status ?? "none",
              Events: String(m1State.runnerResult?.events.length ?? 0),
              Evidence: String(m1State.runnerResult?.evidence_refs.length ?? 0),
            }}
          />
          <OrderedFacts
            emptyText="No runner node outcomes recorded."
            items={(m1State.runnerResult?.node_results ?? []).map((node) => ({
              id: node.work_ref.ref_id,
              label: node.status,
              value: node.reason,
            }))}
          />
        </FactPanel>

        <FactPanel title="Verification">
          <DefinitionList
            values={{
              Decision:
                m1State.verificationResult?.completion_decision ?? "none",
              Reason: m1State.verificationResult?.reason ?? "none",
              Iterations: String(
                m1State.verificationResult?.iterations_used ?? 0,
              ),
            }}
          />
          <OrderedFacts
            emptyText="No verification evidence recorded."
            items={(m1State.verificationResult?.evidence_refs ?? []).map(
              (evidence) => ({
                id: evidence.evidence_id,
                label: evidence.kind,
                value: evidence.summary ?? evidence.subject_ref.ref_id,
              }),
            )}
          />
        </FactPanel>

        <FactPanel title="M1 Events">
          <OrderedFacts
            emptyText="No M1 events surfaced."
            items={[
              ...(m1State.runnerResult?.events ?? []),
              ...(m1State.verificationResult?.event === null ||
              m1State.verificationResult?.event === undefined
                ? []
                : [m1State.verificationResult.event]),
            ].map((event) => ({
              id: event.event_id,
              label: event.event_type,
              value: event.subject_ref.ref_id,
            }))}
          />
        </FactPanel>
      </section>

      <section className="work-console__grid" aria-label="M0 runtime truth">
        <FactPanel title="Work">
          <DefinitionList
            values={{
              ID: consoleState.work?.work_id ?? "none",
              State: consoleState.work?.state ?? "none",
              Type: consoleState.work?.work_type ?? "provider_inventory",
            }}
          />
        </FactPanel>

        <FactPanel title="Execution">
          <DefinitionList
            values={{
              ID: consoleState.execution?.execution_id ?? "none",
              State: consoleState.execution?.state ?? "none",
              "Runtime status": consoleState.runtimeStatus ?? "none",
            }}
          />
        </FactPanel>

        <FactPanel title="Provider Inventory">
          {consoleState.providerInventory.length === 0 ? (
            <p className="work-console__empty">
              No provider descriptors recorded.
            </p>
          ) : (
            <ul className="work-console__list">
              {consoleState.providerInventory.map((provider) => (
                <li key={provider.provider_id}>
                  <strong>{provider.provider_type}</strong>
                  <span>{provider.provider_id}</span>
                  <span>{provider.status}</span>
                </li>
              ))}
            </ul>
          )}
        </FactPanel>

        <FactPanel title="Events">
          <OrderedFacts
            emptyText="No runtime events recorded."
            items={consoleState.events.map((event) => ({
              id: event.event_id,
              label: event.event_type,
              value: event.occurred_at,
            }))}
          />
        </FactPanel>

        <FactPanel title="Evidence">
          <OrderedFacts
            emptyText="No evidence recorded."
            items={consoleState.evidence.map((evidence) => ({
              id: evidence.evidence_id,
              label: evidence.kind,
              value: evidence.summary ?? evidence.collected_at,
            }))}
          />
        </FactPanel>

        <FactPanel title="API Boundary">
          <ul
            className="work-console__routes"
            aria-label="Frozen web API routes"
          >
            {apiBoundaryPaths.map((path) => (
              <li key={path}>{path}</li>
            ))}
          </ul>
        </FactPanel>
      </section>
    </main>
  );
}

function FactPanel(props: { children: ReactNode; title: string }): JSX.Element {
  return (
    <section
      className="work-console__panel"
      aria-labelledby={panelId(props.title)}
    >
      <h2 id={panelId(props.title)}>{props.title}</h2>
      {props.children}
    </section>
  );
}

function DefinitionList(props: {
  values: Record<string, string>;
}): JSX.Element {
  return (
    <dl className="work-console__definition-list">
      {Object.entries(props.values).map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function OrderedFacts(props: {
  emptyText: string;
  items: { id: string; label: string; value: string }[];
}): JSX.Element {
  if (props.items.length === 0) {
    return <p className="work-console__empty">{props.emptyText}</p>;
  }

  return (
    <ol className="work-console__list">
      {props.items.map((item) => (
        <li key={item.id}>
          <strong>{item.label}</strong>
          <span>{item.value}</span>
        </li>
      ))}
    </ol>
  );
}

function statusMessageFor(status: RuntimeStatus): string {
  if (status === "COMPLETED") {
    return "Provider inventory completed and recorded.";
  }
  if (status === "BLOCKED") {
    return "Provider inventory was blocked by policy.";
  }
  return "Provider inventory failed with a bounded runtime result.";
}

function failureMessage(failure: ApiFailure): string {
  const code =
    failure.detail.error_code ??
    failure.detail.status ??
    `HTTP_${String(failure.status)}`;
  const message =
    failure.detail.message ?? "The API returned a bounded failure.";
  return `${code}: ${message}`;
}

function firstFailure(
  ...results: (
    { ok: false; failure: ApiFailure } | { ok: true; value: unknown } | null
  )[]
): ApiFailure | null {
  for (const result of results) {
    if (result !== null && !result.ok) {
      return result.failure;
    }
  }
  return null;
}

function decompositionStatusMessage(
  response: M1DecomposeIntentResponse,
): string {
  if (response.decomposition.status === "SUPPORTED") {
    return `Intent decomposed into ${String(response.decomposition.work_items.length)} work item(s).`;
  }
  return "Intent is an unsupported M1 domain outcome.";
}

function runnerStatusMessage(result: M1DagRunnerResultPayload): string {
  const executed = result.node_results.filter(
    (node) => node.status === "EXECUTED",
  );
  return `DAG run ${result.status} with ${String(executed.length)} executed node(s).`;
}

function firstExecutedNode(
  result: M1DagRunnerResultPayload | null,
): M1DagNodeResultPayload | null {
  return (
    result?.node_results.find((node) => node.status === "EXECUTED") ?? null
  );
}

function workForRef(
  decomposition: M1DecomposeIntentResponse,
  workId: string,
): WorkItemPayload | null {
  return (
    decomposition.decomposition.work_items.find(
      (work) => work.work_id === workId,
    ) ?? null
  );
}

function buildM1DagRunRequest(
  decomposition: M1DecomposeIntentResponse,
): M1DagRunRequest {
  const workItems = decomposition.decomposition.work_items;
  return {
    agent_instances: workItems.map((work, index) => ({
      agent_definition_id: fixedM1Id("agd", index),
      agent_instance_id: fixedM1Id("agi", index),
      created_at: M1_OCCURRED_AT,
      state: "ACTIVE",
      work_id: work.work_id,
    })),
    capability_resolutions_by_work_id: Object.fromEntries(
      workItems.map((work, index) => [
        work.work_id,
        [
          {
            agent_definition_ref: {
              kind: "agent_definition",
              ref_id: fixedM1Id("agd", index),
            },
            capability_ref: {
              kind: "capability",
              ref_id: firstCapabilityId(work, index),
            },
            reason: "EXACT_MATCH",
            requirement: { capability_id: firstCapabilityId(work, index) },
            status: "MATCHED",
          },
        ],
      ]),
    ),
    dag: decomposition.dag,
    event_ids_by_work_id: Object.fromEntries(
      workItems.map((work, index) => [work.work_id, fixedM1Id("evt", index)]),
    ),
    evidence_ids_by_work_id: Object.fromEntries(
      workItems.map((work, index) => [work.work_id, fixedM1Id("evd", index)]),
    ),
    max_concurrency: 1,
    observability_context: {
      trace_id: M1_TRACE_ID,
      work_id: workItems[0]?.work_id ?? null,
    },
    occurred_at: M1_OCCURRED_AT,
    producer_ref: M1_PROVIDER_REF,
    routing_decisions: workItems.map((work, index) =>
      selectedRouteDecision(work, index),
    ),
    work_items: workItems,
  };
}

function buildM1VerificationRequest(
  work: WorkItemPayload,
  runnerNode: M1DagNodeResultPayload,
  evidence: EvidencePayload,
): M1VerificationRequest {
  return {
    attempts: [{ evidence_refs: [evidence], outcome: "passed" }],
    event_id: fixedM1Id("evt", 10),
    max_iterations: 2,
    observability_context: {
      trace_id: M1_TRACE_ID,
      work_id: work.work_id,
    },
    producer_ref: M1_PROVIDER_REF,
    runner_node_result: runnerNode,
    verified_at: M1_OCCURRED_AT,
    verifier_ref: M1_PROVIDER_REF,
    verification_id: fixedM1Id("ver", 0),
    work,
  };
}

function selectedRouteDecision(
  work: WorkItemPayload,
  index: number,
): Record<string, unknown> {
  const route = {
    candidate_key: "executor_deterministic_m1",
    executor_name: "deterministic_m1",
    kind: "DETERMINISTIC_EXECUTOR",
    supported_work_types: [work.work_type],
    work_ref: { kind: "work", ref_id: work.work_id },
  };
  return {
    candidates: [route],
    decided_at: M1_OCCURRED_AT,
    decision_id: fixedM1Id("dec", index),
    observability_context: {
      trace_id: M1_TRACE_ID,
      work_id: work.work_id,
    },
    producer_ref: M1_PROVIDER_REF,
    rationale: {
      code: "SELECTED_SINGLE_VALID_ROUTE",
      details: { valid_candidate_count: 1 },
      message: "Selected the only valid M1 route candidate.",
    },
    resource_constraints: null,
    selected_route: route,
    status: "SELECTED",
    work_ref: { kind: "work", ref_id: work.work_id },
  };
}

function firstCapabilityId(work: WorkItemPayload, index: number): string {
  return (
    work.required_capabilities?.[0]?.capability_id ?? fixedM1Id("cap", index)
  );
}

function fixedM1Id(prefix: string, index: number): string {
  const ordinal = String(index + 1).padStart(26, "0");
  return `${prefix}_${ordinal}`;
}

function panelId(title: string): string {
  return `panel-${title.toLowerCase().replaceAll(" ", "-")}`;
}
