import { act, type ReactElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "./App";
import { apiBoundaryPaths, apiBoundaryUrl } from "./apiBoundary";

const mountedRoots: { container: HTMLDivElement; root: Root }[] = [];

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
  for (const { container, root } of mountedRoots.splice(0)) {
    act(() => {
      root.unmount();
    });
    container.remove();
  }
});

describe("TASK-BOOT-024 web bootstrap", () => {
  it("renders the application shell without product workflow behavior", () => {
    const container = render(<App />);

    const shell = container.querySelector("[data-testid='web-shell']");
    expect(shell).not.toBeNull();
    expect(shell?.textContent).toContain("CuriosOS Web");
    expect(shell?.textContent).toContain("@curiosos/curios-contracts");
  });

  it("keeps API usage bounded to the frozen TASK-BOOT-022 HTTP surface", () => {
    expect(apiBoundaryPaths).toEqual([
      "/health/live",
      "/health/ready",
      "/providers",
    ]);
    expect(apiBoundaryUrl("/providers", "http://localhost:8000")).toBe(
      "http://localhost:8000/providers",
    );
  });
});
