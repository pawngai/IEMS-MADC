import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const FRONTEND_ROOT = process.cwd();
const SRC_ROOT = path.join(FRONTEND_ROOT, "src");
const CONTEXTS_ROOT = path.join(SRC_ROOT, "contexts");
const OUT_PATH = path.join(
  SRC_ROOT,
  "contexts",
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

function collectCrossContextViolations() {
  const files = walkJsFiles(CONTEXTS_ROOT).filter(
    (filePath) => !filePath.includes(`${path.sep}__tests__${path.sep}`)
  );
  const violations = [];

  for (const filePath of files) {
    const source = fs.readFileSync(filePath, "utf8");
    const relative = path.relative(CONTEXTS_ROOT, filePath).replace(/\\/g, "/");
    const currentContext = relative.split("/")[0];
    const imports = source.match(/from\s+["']@\/contexts\/[^"']+["']/g) || [];

    for (const imp of imports) {
      const match = imp.match(/@\/contexts\/([^/]+)/);
      if (!match) continue;
      const targetContext = match[1];
      if (targetContext !== currentContext) {
        violations.push(`${relative} -> ${targetContext}`);
      }
    }
  }

  return [...new Set(violations)].sort();
}

const violations = collectCrossContextViolations();
fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
fs.writeFileSync(OUT_PATH, `${JSON.stringify(violations, null, 2)}\n`, "utf8");
process.stdout.write(`Updated ${OUT_PATH} with ${violations.length} entries.\n`);
