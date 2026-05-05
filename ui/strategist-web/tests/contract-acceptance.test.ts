import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import contract from "@/lib/contracts/ui-facade-routes.json";
import { demoReadPlanePaths } from "@/lib/demo/demo-mode";
import { LOCAL_OPS_COMMAND_REGISTRY } from "@/lib/operator/local-ops-command-hints";

type FacadeRoute = {
  method: string;
  path: string;
  kind: string;
  auth_required: boolean;
  payload_schema: string;
};

const here = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(here, "..");
const repoRoot = resolve(webRoot, "../..");
const routes = (contract.routes as FacadeRoute[]).filter((route) => route.method === "GET" || route.method === "POST");

const allowedProbeOrExternal = new Set(["/", "/healthz", "/livez", "/readyz", "/readiness/deployment"]);
const explicitMutationPaths = new Set(["/ui/commands/{action}", "/ui/strategy-intake"]);

function walk(dir: string, predicate: (path: string) => boolean): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const stat = statSync(path);
    if (stat.isDirectory()) out.push(...walk(path, predicate));
    else if (predicate(path)) out.push(path);
  }
  return out;
}

function stripQuery(path: string): string {
  return path.split("?", 1)[0].replace(/\$\{[^}]+\}/g, "{param}").replace(/\{param\}$/, "");
}

function routeMatches(path: string, route: FacadeRoute): boolean {
  if (path === route.path) return true;
  if (!route.path.includes("{")) return false;
  const prefix = route.path.slice(0, route.path.indexOf("{"));
  return path.startsWith(prefix);
}

function assertFacadeRoute(path: string, method: "GET" | "POST"): FacadeRoute {
  const normalized = stripQuery(path);
  const match = routes.find((route) => route.method === method && routeMatches(normalized, route));
  expect(match, `${method} ${normalized} is absent from ui-facade-routes.json`).toBeTruthy();
  expect(match?.payload_schema, `${method} ${normalized} must declare payload_schema`).toBeTruthy();
  return match as FacadeRoute;
}

function hookFiles(): string[] {
  return walk(join(webRoot, "hooks"), (path) => /\.(ts|tsx)$/.test(path) && !/\.test\.(ts|tsx)$/.test(path));
}

function webRelative(path: string): string {
  return relative(webRoot, path).replace(/\\/g, "/");
}

function textFilesUnder(relativeDir: string): string[] {
  return walk(join(webRoot, relativeDir), (path) => /\.(ts|tsx|json|md|example)$/.test(path));
}

function stringLiterals(source: string): string[] {
  return [...source.matchAll(/["'`]((?:\/|GET \/|POST \/)(?:ui|healthz|livez|readyz|readiness)[^"'`]*)["'`]/g)].map((m) =>
    m[1].replace(/^GET\s+/, "").replace(/^POST\s+/, ""),
  );
}

describe("cockpit acceptance pack: contract and route safety", () => {
  it("aligns frontend read hooks with facade routes or explicit probes", () => {
    const used = new Set<string>();
    for (const file of hookFiles()) {
      const src = readFileSync(file, "utf8");
      for (const literal of stringLiterals(src)) {
        const normalized = stripQuery(literal);
        if (literal.includes("/ui/commands/") || explicitMutationPaths.has(normalized)) continue;
        used.add(normalized);
      }
    }

    expect(used.size).toBeGreaterThan(20);
    for (const path of used) {
      if (allowedProbeOrExternal.has(path)) continue;
      assertFacadeRoute(path, "GET");
    }
  });

  it("keeps frontend mutation endpoints isolated and auth-required in the facade contract", () => {
    const mutationHookFiles = hookFiles().filter((file) => readFileSync(file, "utf8").includes("strategistPostJson"));
    expect(mutationHookFiles.map((file) => webRelative(file)).sort()).toEqual([
      "hooks/useUiOperatorCommand.ts",
      "hooks/useUiStrategyIntake.ts",
    ]);

    const postRoutes = ["/ui/commands/{action}", "/ui/strategy-intake"];
    for (const path of postRoutes) {
      const route = assertFacadeRoute(path, "POST");
      expect(route.auth_required).toBe(true);
      expect(route.kind).toBe("mutation");
    }
  });

  it("keeps cockpit pane components free of direct fetch and mutation client imports", () => {
    const paneFiles = textFilesUnder("components/cockpit").filter((path) => /\.(ts|tsx)$/.test(path));
    for (const file of paneFiles) {
      const src = readFileSync(file, "utf8");
      expect(src, relative(webRoot, file)).not.toMatch(/\bfetch\s*\(/);
      if (!file.endsWith("StrategyLifecycleIntakeForm.tsx")) {
        expect(src, relative(webRoot, file)).not.toContain("strategistPostJson");
      }
    }
  });

  it("maps every demo read-plane route to a schema-bearing facade route or explicit probe", () => {
    for (const path of demoReadPlanePaths) {
      if (allowedProbeOrExternal.has(path)) continue;
      assertFacadeRoute(path, "GET");
    }
  });
});

describe("cockpit acceptance pack: command truth", () => {
  const pyproject = readFileSync(join(repoRoot, "pyproject.toml"), "utf8");

  it("maps all local command hints to real console scripts or repository scripts", () => {
    expect(LOCAL_OPS_COMMAND_REGISTRY.length).toBeGreaterThan(10);
    for (const entry of LOCAL_OPS_COMMAND_REGISTRY) {
      if (entry.primaryConsoleScript) {
        expect(pyproject, entry.id).toContain(`${entry.primaryConsoleScript} =`);
      }
      for (const scriptPath of entry.pythonScriptPaths) {
        expect(existsSync(join(repoRoot, scriptPath)), entry.id).toBe(true);
      }
      expect(existsSync(join(repoRoot, entry.docPath)), entry.id).toBe(true);
    }
  });

  it("keeps command hints copy-only and secret-free with warnings for production-sensitive entries", () => {
    for (const entry of LOCAL_OPS_COMMAND_REGISTRY) {
      expect(entry.commandText).not.toMatch(/Bearer\s+[A-Za-z0-9._-]+|API[_-]?KEY=|TOKEN=|SECRET=/i);
      expect(entry.commandText).not.toMatch(/&&|\|\||;\s*\S/);
      if (entry.safetyClass === "PRODUCTION_SENSITIVE") {
        expect(entry.productionWarning, entry.id).toBeTruthy();
      }
    }
  });
});
