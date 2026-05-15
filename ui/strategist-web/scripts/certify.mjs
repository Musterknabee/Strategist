/**
 * Operator-grade frontend certification runner — frontend certify entrypoint (FRONTEND_CERTIFY_REPORT).
 * schema: frontend_certify/v1
 * report: artifacts/frontend_certify/latest/frontend_certify_report.json
 *
 * Steps (names match scripts/local_certify.FRONTEND_CERTIFY_REQUIRED_STEPS):
 *   name: "contract_check"  args: ["run", "contract:check"]
 *   name: "lint"            args: ["run", "lint"]
 *   name: "typecheck"       args: ["run", "typecheck"]
 *   name: "test"           args: ["run", "test"]
 *   name: "acceptance"     args: ["run", "acceptance"]
 *   name: "build"          args: ["run", "build"]
 *   name: "audit"          args: ["run", "audit"]   # npm audit --audit-level=high
 *
 * writeReport("PASS") / writeReport("FAIL", step.name) semantics are implemented in
 * ../../../scripts/frontend_certify_runner.py (Python) for digest parity with local_certify.
 */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// certify.mjs lives at ui/strategist-web/scripts/ — repo root is three levels up.
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const py = process.env.PYTHON ?? "python";
const r = spawnSync(py, ["scripts/frontend_certify_runner.py"], {
  cwd: repoRoot,
  stdio: "inherit",
  shell: false,
});
if (r.error) {
  console.error(r.error);
  process.exit(1);
}
process.exit(r.status === null ? 1 : r.status);
