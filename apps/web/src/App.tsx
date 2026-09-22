import {
  curiosContractsPackageName,
  curiosContractsPackageVersion,
} from "@curiosos/curios-contracts";
import type { JSX } from "react";

import "./App.css";
import { apiBoundaryPaths } from "./apiBoundary";

export function App(): JSX.Element {
  return (
    <main className="web-shell" data-testid="web-shell">
      <section className="web-shell__inner" aria-labelledby="web-shell-title">
        <p className="web-shell__eyebrow">TASK-BOOT-024</p>
        <h1 id="web-shell-title">CuriosOS Web</h1>
        <p className="web-shell__summary">
          Bootstrap surface active. Canonical Curios semantics remain behind the
          API and contract boundaries.
        </p>

        <section
          className="web-shell__panel"
          aria-labelledby="api-boundary-title"
        >
          <div className="web-shell__panel-header">
            <h2 className="web-shell__panel-title" id="api-boundary-title">
              API Boundary
            </h2>
            <p className="web-shell__contract">
              {curiosContractsPackageName} {curiosContractsPackageVersion}
            </p>
          </div>
          <ul
            className="web-shell__endpoints"
            aria-label="Frozen TASK-BOOT-022 endpoints"
          >
            {apiBoundaryPaths.map((path) => (
              <li className="web-shell__endpoint" key={path}>
                {path}
              </li>
            ))}
          </ul>
        </section>
      </section>
    </main>
  );
}
