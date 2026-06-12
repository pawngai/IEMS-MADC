import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const FRONTEND_ROOT = process.cwd();
const SRC_ROOT = path.join(FRONTEND_ROOT, "src");
const MODULES_ROOT = path.join(SRC_ROOT, "modules");
const OUT_PATH = path.join(
  SRC_ROOT,
  "modules",
  "__tests__",
  "fixtures",
  "context-boundary-allowlist.json"
);

function walkJsFiles(root) {
  if (!fs.existsSync(root)) return [];
  const stack = [root];
  const files = [];
  while (stack.length > 0) {
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

function collectCrossModuleViolations() {
  const files = walkJsFiles(MODULES_ROOT).filter(
    (filePath) => !filePath.includes(`${path.sep}__tests__${path.sep}`)
  );
  const violations = [];

  for (const filePath of files) {
    const source = fs.readFileSync(filePath, "utf8");
    const relative = path.relative(MODULES_ROOT, filePath).replace(/\\/g, "/");
    const currentModule = relative.split("/")[0];
    const imports = source.match(/from\s+["']@\/modules\/[^"']+["']/g) || [];

    for (const imp of imports) {
      const match = imp.match(/@\/modules\/([^/]+)/);
      if (!match) continue;
      const targetModule = match[1];
      if (targetModule !== currentModule) {
        violations.push(`${relative} -> ${targetModule}`);
      }
    }
  }

  return [...new Set(violations)].sort();
}

const violations = collectCrossModuleViolations();
fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
fs.writeFileSync(OUT_PATH, `${JSON.stringify(violations, null, 2)}\n`, "utf8");
process.stdout.write(`Updated ${OUT_PATH} with ${violations.length} entries.\n`);
