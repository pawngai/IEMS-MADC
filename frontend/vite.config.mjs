import { defineConfig, loadEnv, transformWithOxc } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const reactAppEnv = Object.fromEntries(
    Object.entries(env).filter(([key]) => key.startsWith("REACT_APP_"))
  );

  return {
    plugins: [
      {
        name: "jsx-in-js",
        enforce: "pre",
        async transform(code, id) {
          // Vitest on Windows provides absolute ids with backslashes.
          if (!/[\\/]src[\\/].*\.js($|\?)/.test(id)) return null;
          return transformWithOxc(code, id, {
            lang: "jsx",
            jsx: { runtime: "automatic" },
          });
        },
      },
      {
        name: "jest-api-compat",
        enforce: "pre",
        transform(code, id) {
          if (!/[\\/]src[\\/].*\.(test|spec)\.[jt]sx?($|\?)/.test(id)) return null;
          if (!code.includes("jest.")) return null;
          return {
            code: code.replace(/\bjest\./g, "vi."),
            map: null,
          };
        },
      },
      react(),
    ],
    resolve: {
      alias: {
        "@": path.resolve(process.cwd(), "src"),
      },
    },
    envPrefix: ["VITE_", "REACT_APP_"],
    define: {
      "process.env": JSON.stringify({
        ...reactAppEnv,
        NODE_ENV: mode,
      }),
    },
    oxc: {
      jsx: { runtime: "automatic" },
    },
    optimizeDeps: {
      rolldownOptions: {
        moduleTypes: {
          ".js": "jsx",
        },
      },
    },
    server: {
      host: "0.0.0.0",
      watch: {
        ignored: ["**/node_modules/**", "**/.git/**", "**/build/**", "**/dist/**", "**/coverage/**"],
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/setupTests.js",
      css: true,
      include: ["src/**/*.{test,spec}.{js,jsx,ts,tsx}"],
      exclude: ["node_modules", "build", "dist"],
    },
  };
});
