const js = require("@eslint/js");
const globals = require("globals");
const reactHooks = require("eslint-plugin-react-hooks");

module.exports = [
  {
    ignores: ["build/**", "node_modules/**"],
  },
  js.configs.recommended,
  {
    files: ["src/{lib,hooks,shared}/**/*.{js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/features/*", "@/features/**"],
              message:
                "Import via context-owned entrypoints (`@/contexts/*`) instead of direct feature paths.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/platform/**/*.{js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/contexts/*", "@/contexts/**"],
              message:
                "Platform must not import bounded contexts. Keep platform services domain-neutral.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/portals/**/*.{js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/contexts/*/*", "@/contexts/*/**"],
              message:
                "Portals may compose contexts only through public context index contracts.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/app/{providers,router,layouts}/**/*.{js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/contexts/*/api/*", "@/contexts/*/api/**"],
              message:
                "App layer must not import context APIs directly. Use context model/ui adapters.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/hooks/**/*.{js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/contexts/*/api/*", "@/contexts/*/api/**"],
              message:
                "Hooks layer must not import context APIs directly. Use context model adapters.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/contexts/**/__tests__/*.{js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/features/*", "@/features/**"],
              message:
                "Context tests must mock/use context contracts, not feature modules.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/contexts/**/*.{js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/features/*", "@/features/**"],
              message:
                "Context modules must not import feature modules directly.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/shared/**/*.{js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/contexts/*/api/*", "@/contexts/*/api/**"],
              message:
                "Shared layer must not import context APIs directly. Use context model/ui adapters.",
            },
            {
              group: ["@/contexts/*/ui/*", "@/contexts/*/ui/**"],
              message:
                "Shared layer must not import context UI directly. Keep shared components context-agnostic.",
            },
            {
              group: ["@/features/*", "@/features/**"],
              message:
                "Shared layer must not import feature modules. Keep shared components dumb and reusable.",
            },
            {
              group: ["@/platform/api/*", "@/platform/api/**", "@/platform/auth/*", "@/platform/auth/**"],
              message:
                "Shared layer must not depend on authenticated platform services. Keep transport concerns in platform.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/shared/ui/**/*.{js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/contexts/*", "@/contexts/**"],
              message:
                "shared/ui must stay dumb. Do not import context modules directly.",
            },
            {
              group: ["@/features/*", "@/features/**"],
              message:
                "shared/ui must stay dumb. Do not import feature modules directly.",
            },
            {
              group: ["@/platform/api/*", "@/platform/api/**", "@/platform/auth/*", "@/platform/auth/**"],
              message:
                "shared/ui must not import authenticated platform services.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/**/*.{js,jsx}"],
    plugins: {
      "react-hooks": reactHooks,
    },
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.jest,
        ...globals.es2015,
      },
    },
    rules: {
      "no-console": "off",
      "no-unused-vars": "off",
      "no-empty": "off",
      "react-hooks/exhaustive-deps": "off",
    },
  },
  {
    files: ["src/**/*.{test,spec}.{js,jsx,ts,tsx}"],
    languageOptions: {
      globals: {
        vi: "readonly",
        expect: "readonly",
        describe: "readonly",
        it: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
        beforeAll: "readonly",
        afterAll: "readonly",
      },
    },
  },
];
