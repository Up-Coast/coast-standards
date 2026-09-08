// ESLint flat config (eslint.org: the recommended rules, plus typescript-eslint's
// TYPE-CHECKED recommended set and, when the plugin is installed, the React hooks rules).
// Installed by Coast; yours to edit. Needs, in devDependencies:
//   eslint @eslint/js typescript typescript-eslint
//   eslint-plugin-react-hooks   (React projects only — without it the two hook rules are skipped)
// Type-checked linting (typescript-eslint.io/getting-started/typed-linting):
// projectService asks TypeScript's project service for each file's types, so
// rules such as no-floating-promises can see what a call returns.
// Rules held here (enforcement/README.md section 5.2), each named on its own
// line so the config states them rather than inheriting them:
//   C-2 (Web, React Native) — react-hooks/rules-of-hooks, react-hooks/exhaustive-deps
//   C-3 (Web, React Native) — @typescript-eslint/no-floating-promises
//   A-3 (advisory)          — max-lines, a warning at the type-size threshold
import { createRequire } from "node:module";
import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

// The hooks plugin is loaded only when the project has it: a web project without React
// must not fail its lint seat on an import it has no reason to install.
const require = createRequire(import.meta.url);
let reactHooks = null;
try {
  const loaded = require("eslint-plugin-react-hooks");
  reactHooks = loaded.default ?? loaded;
} catch (error) {
  if (error.code !== "MODULE_NOT_FOUND") throw error;
}

export default defineConfig([
  { ignores: ["node_modules/**", "dist/**", "build/**", "coverage/**"] },
  {
    files: ["**/*.{js,mjs,cjs,ts,tsx}"],
    extends: [js.configs.recommended, tseslint.configs.recommendedTypeChecked],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: reactHooks ? { "react-hooks": reactHooks } : {},
    rules: {
      ...(reactHooks
        ? {
            "react-hooks/rules-of-hooks": "error",
            "react-hooks/exhaustive-deps": "error",
          }
        : {}),
      "@typescript-eslint/no-floating-promises": "error",
      "max-lines": ["warn", { max: 400, skipBlankLines: true, skipComments: true }],
    },
  },
  {
    // Plain JavaScript files carry no types; the type-checked rules would only error on them.
    files: ["**/*.{js,mjs,cjs}"],
    extends: [tseslint.configs.disableTypeChecked],
  },
]);
