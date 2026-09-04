// ESLint flat config (eslint.org: the recommended rules, plus typescript-eslint's
// TYPE-CHECKED recommended set and the React hooks rules).
// Installed by Coast; yours to edit. Needs, in devDependencies:
//   eslint @eslint/js typescript typescript-eslint eslint-plugin-react-hooks
// Type-checked linting (typescript-eslint.io/getting-started/typed-linting):
// projectService asks TypeScript's project service for each file's types, so
// rules such as no-floating-promises can see what a call returns.
// Rules held here (enforcement/README.md section 5.2), each named on its own
// line so the config states them rather than inheriting them:
//   C-2 (Web, React Native) — react-hooks/rules-of-hooks, react-hooks/exhaustive-deps
//   C-3 (Web, React Native) — @typescript-eslint/no-floating-promises
//   A-3 (advisory)          — max-lines, a warning at the type-size threshold
import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

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
    plugins: { "react-hooks": reactHooks },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "error",
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
