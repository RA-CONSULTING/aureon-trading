import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      // Foundation tier (whole repo): informative, non-blocking. `eslint .` reports
      // these as warnings across the ~269 legacy components so the tree can only
      // improve (the ratchet), without gating CI on a mass one-pass cleanup.
      "@typescript-eslint/no-unused-vars": "warn",
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-require-imports": "off",
      "no-empty": "warn",
      "no-shadow-restricted-names": "warn",
      "no-useless-escape": "warn",
      "prefer-const": "warn",
    },
  },
  {
    // Strict tier — the unified shell (src/shell). This is the product surface
    // held to a real bar: the same rules as errors, so `lint:shell` blocks CI.
    // ESLint only reports on the files it lints (no transitive type-graph blow-up),
    // so this stays scoped even though the shell lazy-imports the legacy tree.
    files: ["src/shell/**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-unused-vars": "error",
      "@typescript-eslint/no-explicit-any": "error",
      "no-empty": "error",
      "prefer-const": "error",
    },
  }
);
