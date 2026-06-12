import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, test } from "vitest";

describe("serviceBookAPI boundary", () => {
  test("does not post mutations to Service Book endpoints", () => {
    const source = fs.readFileSync(
      path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../serviceBookApi.js"),
      "utf8",
    );

    expect(source).not.toMatch(/api\.post\(`\/service-book/);
    expect(source).toContain("Service Book is projection-only");
  });

  test("service book UI does not call mutation helpers", () => {
    const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
    const violations = [];

    const visit = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (entry.name !== "__tests__") visit(fullPath);
          continue;
        }
        if (!/\.(js|jsx)$/.test(entry.name)) continue;
        const source = fs.readFileSync(fullPath, "utf8");
        if (/serviceBookAPI\.(createEntry|submitEntry|verifyEntry|approveEntry|lockEntry)\(/.test(source)) {
          violations.push(path.relative(root, fullPath));
        }
      }
    };

    visit(root);

    expect(violations).toEqual([]);
  });
});
