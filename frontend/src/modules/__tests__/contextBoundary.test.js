import fs from "fs";
import path from "path";

const SRC_ROOT = path.join(__dirname, "..", "..");
const CONTEXTS_ROOT = path.join(SRC_ROOT, "modules");
const PLATFORM_ROOT = path.join(SRC_ROOT, "platform");
const SHARED_UI_ROOT = path.join(SRC_ROOT, "shared", "ui");
const SHARED_ROOT = path.join(SRC_ROOT, "shared");
const NON_WRAPPER_LAYER_PREFIXES = [
  "app/",
  "components/",
  "pages/",
  "lib/",
  "hooks/",
  "shared/",
];
const API_RESTRICTED_LAYER_PREFIXES = ["app/", "hooks/", "shared/"];
const FEATURE_WRAPPER_ALLOWLIST_PREFIXES = ["app/router/"];
const SPLIT_FRONTEND_SHELL_MAX_LINES = 1200;
const SPLIT_FRONTEND_SHELLS = [
  "modules/reporting_analytics/pages/AnalyticsDashboardPage.jsx",
  "modules/service_book/records/components/RecordServiceBookRecordDialog.jsx",
  "modules/employee_master/components/EmployeeProfileExtensionEditor.jsx",
  "modules/employee_master/pages/EmployeeDirectoryPage.jsx",
];
const FORM_SCHEMA_CONTEXTS = ["employee_master", "service_book/records", "service_book/opening"];

function walkJsFiles(root) {
  if (!fs.existsSync(root)) return [];
  const stack = [root];
  const files = [];
  while (stack.length) {
    const current = stack.pop();
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const entryPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(entryPath);
        continue;
      }
      if (/\.(js|jsx)$/.test(entry.name)) {
        files.push(entryPath);
      }
    }
  }
  return files;
}

describe("Frontend context boundaries", () => {
  test("every bounded context exposes a public index contract", () => {
    const missingIndexes = fs
      .readdirSync(CONTEXTS_ROOT, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .filter((name) => !name.startsWith("__"))
      .filter((name) => !fs.existsSync(path.join(CONTEXTS_ROOT, name, "index.js")));

    expect(missingIndexes).toEqual([]);
  });

  test("large frontend shells stay split by context-owned helpers", () => {
    const violations = [];

    for (const relativePath of SPLIT_FRONTEND_SHELLS) {
      const filePath = path.join(SRC_ROOT, relativePath);
      const lineCount = fs.readFileSync(filePath, "utf8").split(/\r?\n/).length;
      if (lineCount > SPLIT_FRONTEND_SHELL_MAX_LINES) {
        violations.push(`${relativePath}: ${lineCount} lines`);
      }
    }

    expect(violations).toEqual([]);
  });

  test("context modules do not import other context modules", () => {
    const violations = [];
    const files = walkJsFiles(CONTEXTS_ROOT).filter((filePath) =>
      !filePath.includes(`${path.sep}__tests__${path.sep}`)
    );

    for (const filePath of files) {
      const source = fs.readFileSync(filePath, "utf8");
      const relative = path.relative(CONTEXTS_ROOT, filePath).replace(/\\/g, "/");
      const currentContext = relative.split("/")[0];

      const imports = source.match(/from\s+["']@\/modules\/[^"']+["']/g) || [];
      for (const imp of imports) {
        const match = imp.match(/@\/modules\/([^/"']+)(\/[^"']*)?/);
        if (!match) continue;
        const targetContext = match[1];
        const isPrivateImport = Boolean(match[2]);
        if (targetContext !== currentContext && isPrivateImport) {
          violations.push(`${relative} -> ${targetContext}`);
        }
      }
    }

    expect([...new Set(violations)].sort()).toEqual([]);
  });

  test("shared/ui stays dumb and context-agnostic", () => {
    const violations = [];
    const files = walkJsFiles(SHARED_UI_ROOT);
    for (const filePath of files) {
      const source = fs.readFileSync(filePath, "utf8");
      const relative = path.relative(SRC_ROOT, filePath).replace(/\\/g, "/");
      if (/@\/modules\//.test(source) || /@\/features\//.test(source)) {
        violations.push(relative);
      }
    }
    expect(violations).toEqual([]);
  });

  test("shared and platform do not import bounded contexts", () => {
    const violations = [];
    const files = [...walkJsFiles(SHARED_ROOT), ...walkJsFiles(PLATFORM_ROOT)].filter(
      (filePath) => !filePath.includes(`${path.sep}__tests__${path.sep}`)
    );

    for (const filePath of files) {
      const source = fs.readFileSync(filePath, "utf8");
      const relative = path.relative(SRC_ROOT, filePath).replace(/\\/g, "/");
      if (/@\/modules\//.test(source)) {
        violations.push(relative);
      }
    }

    expect(violations).toEqual([]);
  });

  test("authenticated transport is owned by platform, not shared", () => {
    expect(fs.existsSync(path.join(SRC_ROOT, "shared", "lib", "httpClient.js"))).toBe(false);
    expect(fs.existsSync(path.join(SRC_ROOT, "platform", "api", "httpClient.js"))).toBe(true);

    const sharedViolations = walkJsFiles(SHARED_ROOT)
      .filter((filePath) => {
        const source = fs.readFileSync(filePath, "utf8");
        return /@\/platform\/(api|auth)\//.test(source);
      })
      .map((filePath) => path.relative(SRC_ROOT, filePath).replace(/\\/g, "/"));

    expect(sharedViolations).toEqual([]);
  });

  test("non-wrapper layers do not import feature modules directly", () => {
    const violations = [];
    const files = walkJsFiles(SRC_ROOT).filter(
      (filePath) =>
        !filePath.includes(`${path.sep}__tests__${path.sep}`) &&
        !filePath.includes(`${path.sep}modules${path.sep}`) &&
        !filePath.includes(`${path.sep}features${path.sep}`)
    );

    for (const filePath of files) {
      const source = fs.readFileSync(filePath, "utf8");
      const relative = path.relative(SRC_ROOT, filePath).replace(/\\/g, "/");
      const inScopedLayer = NON_WRAPPER_LAYER_PREFIXES.some((prefix) =>
        relative.startsWith(prefix)
      );
      if (!inScopedLayer) {
        continue;
      }

      const isAllowedWrapper = FEATURE_WRAPPER_ALLOWLIST_PREFIXES.some((prefix) =>
        relative.startsWith(prefix)
      );
      if (isAllowedWrapper) {
        continue;
      }

      if (/@\/features\//.test(source)) {
        violations.push(relative);
      }
    }

    expect(violations).toEqual([]);
  });

  test("app/hooks/shared do not import context APIs directly", () => {
    const violations = [];
    const files = walkJsFiles(SRC_ROOT).filter(
      (filePath) => !filePath.includes(`${path.sep}__tests__${path.sep}`)
    );

    for (const filePath of files) {
      const source = fs.readFileSync(filePath, "utf8");
      const relative = path.relative(SRC_ROOT, filePath).replace(/\\/g, "/");
      const inScopedLayer = API_RESTRICTED_LAYER_PREFIXES.some((prefix) =>
        relative.startsWith(prefix)
      );
      if (!inScopedLayer) {
        continue;
      }

      if (/@\/modules\/[^/]+\/api\//.test(source)) {
        violations.push(relative);
      }
    }

    expect(violations).toEqual([]);
  });

  test("context pages and components do not use raw transport clients", () => {
    const violations = [];
    const files = walkJsFiles(CONTEXTS_ROOT).filter((filePath) => {
      const normalized = filePath.replace(/\\/g, "/");
      return (
        !normalized.includes("/__tests__/") &&
        (normalized.includes("/pages/") || normalized.includes("/components/"))
      );
    });

    for (const filePath of files) {
      const source = fs.readFileSync(filePath, "utf8");
      const relative = path.relative(SRC_ROOT, filePath).replace(/\\/g, "/");
      if (
        /from\s+["']@\/shared\/lib\/httpClient["']/.test(source) ||
        /from\s+["']@\/platform\/api/.test(source) ||
        /from\s+["']axios["']/.test(source) ||
        /\bfetch\s*\(/.test(source)
      ) {
        violations.push(relative);
      }
    }

    expect(violations).toEqual([]);
  });

  test("high-risk form contexts keep schema-driven forms", () => {
    const missingSchemaFolders = FORM_SCHEMA_CONTEXTS.filter(
      (contextName) => !fs.existsSync(path.join(CONTEXTS_ROOT, contextName, "schemas"))
    );
    const missingSchemas = FORM_SCHEMA_CONTEXTS.filter((contextName) => {
      const schemaRoot = path.join(CONTEXTS_ROOT, contextName, "schemas");
      return !walkJsFiles(schemaRoot).some((filePath) => /schema/i.test(path.basename(filePath)));
    });

    expect(missingSchemaFolders).toEqual([]);
    expect(missingSchemas).toEqual([]);
  });

  test("Service Book Opening stays separate from Service Book records", () => {
    const openingRoot = path.join(CONTEXTS_ROOT, "service_book", "opening");
    expect(fs.existsSync(openingRoot)).toBe(true);

    const openingFiles = walkJsFiles(openingRoot);
    const recordDialogImports = openingFiles
      .filter((filePath) =>
        /RecordServiceBookRecordDialog/.test(fs.readFileSync(filePath, "utf8"))
      )
      .map((filePath) => path.relative(SRC_ROOT, filePath).replace(/\\/g, "/"));

    expect(recordDialogImports).toEqual([]);
  });
});
