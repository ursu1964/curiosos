import {
  curiosContractsPackageName,
  curiosContractsPackageVersion,
} from "@curiosos/curios-contracts";
import { useRef, useState, type JSX, type ReactNode } from "react";

import "./App.css";
import {
  apiBoundaryPaths,
  createProviderInventoryWork,
  listWorkEvidence,
  listWorkEvents,
  readExecution,
  readWork,
  runProviderInventoryWork,
  type ApiFailure,
  type EvidencePayload,
  type ExecutionPayload,
  type ProviderDescriptorPayload,
  type RuntimeEventPayload,
  type RuntimeStatus,
  type WorkItemPayload,
} from "./apiBoundary";

type BusyAction = "create" | "run" | "refresh" | null;

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

export function App(): JSX.Element {
  const [consoleState, setConsoleState] = useState<ConsoleState>(initialState);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const requestGeneration = useRef(0);
  const activeWorkId = useRef<string | null>(null);

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

  const isBusy = busyAction !== null;

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
            aria-label="Frozen M0 API routes"
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

function panelId(title: string): string {
  return `panel-${title.toLowerCase().replaceAll(" ", "-")}`;
}
