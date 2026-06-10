import fs from "fs";
import path from "path";

const ROUTER_DIR = path.join(__dirname, "..");
const REPO_ROOT = path.join(ROUTER_DIR, "..", "..", "..", "..");

const ROUTE_FILES = [
  "adminRoutes.jsx",
  "departmentRoutes.jsx",
  "employeeRoutes.jsx",
  "essRoutes.jsx",
  "publicRoutes.jsx",
  "routes.jsx",
];

/**
 * Aliases removed during the post-migration cleanup. The router and supporting
 * code must not reintroduce any of these literal paths.
 */
const REMOVED_ALIAS_PATTERNS = [
  /["']\/service-events(?:\/[^"']*)?["']/,
  /["']\/portal\/service-events(?:\/[^"']*)?["']/,
  /["']\/department\/change-requests["']/,
  /["']\/department\/workflow\/queue["']/,
  /["']\/department\/employees(?:\/[^"']*)?["']/,
];

const readRouter = (file) =>
  fs.readFileSync(path.join(ROUTER_DIR, file), "utf8");

describe("Route alias allowlist guard", () => {
  test("removed legacy aliases are not reintroduced in router files", () => {
    const violations = [];
    for (const file of ROUTE_FILES) {
      const source = readRouter(file);
      for (const pattern of REMOVED_ALIAS_PATTERNS) {
        const match = source.match(pattern);
        if (match) {
          violations.push(`${file}: ${match[0]}`);
        }
      }
    }
    expect(violations).toEqual([]);
  });

  test("frontend ROUTE_ALIAS_ALLOWLIST.md exists and documents the /portal/* scope", () => {
    const allowlistPath = path.join(REPO_ROOT, "frontend", "ROUTE_ALIAS_ALLOWLIST.md");
    expect(fs.existsSync(allowlistPath)).toBe(true);
    const allowlist = fs.readFileSync(allowlistPath, "utf8");
    expect(allowlist).toMatch(/\/portal\/\*/);
    expect(allowlist).toMatch(/Removed Aliases/);
  });

  test("placeholder redirects.jsx stays removed", () => {
    const removedPlaceholder = path.join(ROUTER_DIR, "redirects.jsx");
    expect(fs.existsSync(removedPlaceholder)).toBe(false);
  });
});
