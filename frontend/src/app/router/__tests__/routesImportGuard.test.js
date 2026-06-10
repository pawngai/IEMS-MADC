import fs from "fs";
import path from "path";

describe("App router import guard", () => {
  test("app routes.jsx is a pure route-module composition root", () => {
    const routesPath = path.join(__dirname, "..", "routes.jsx");
    const source = fs.readFileSync(routesPath, "utf8");

    expect(source).toMatch(/from\s+["']@\/app\/router\/publicRoutes["']/);
    expect(source).toMatch(/from\s+["']@\/app\/router\/adminRoutes["']/);
    expect(source).toMatch(/from\s+["']@\/app\/router\/departmentRoutes["']/);
    expect(source).toMatch(/from\s+["']@\/app\/router\/employeeRoutes["']/);
    expect(source).toMatch(/from\s+["']@\/app\/router\/essRoutes["']/);

    expect(source).not.toMatch(/@\/app\/pages\//);
    expect(source).not.toMatch(/from\s+["']\.\.\/\.\.\/app\/pages\//);
    expect(source).not.toMatch(/@\/modules\//);
    expect(source).not.toMatch(/@\/app\/contexts\//);
  });

  test("legacy src/pages root is removed", () => {
    const legacyPagesRoot = path.join(__dirname, "..", "..", "..", "pages");
    expect(fs.existsSync(legacyPagesRoot)).toBe(false);
  });
});
