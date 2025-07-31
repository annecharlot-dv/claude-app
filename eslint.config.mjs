import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";
import json from "@eslint/json";
import markdown from "@eslint/markdown";
import css from "@eslint/css";

export default [
  {
    ignores: [
      ".kiro/",
      "node_modules/",
      "dist/",
      "build/",
      "coverage/",
      ".next/",
      "out/"
    ]
  },

  // JavaScript/TypeScript base configuration
  {
    files: ["**/*.{js,mjs,cjs,ts,mts,cts}"],
    ...js.configs.recommended,
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node
      }
    }
  },

  // TypeScript configuration
  ...tseslint.configs.recommended.map(config => ({
    ...config,
    files: ["**/*.{ts,mts,cts,tsx}"]
  })),

  // React configuration - more explicit setup
  {
    files: ["**/*.{jsx,tsx}"],
    plugins: {
      react: pluginReact
    },
    languageOptions: {
      ...pluginReact.configs.flat.recommended.languageOptions,
      globals: {
        ...globals.browser
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true
        }
      }
    },
    settings: {
      react: {
        version: "18.3"
      }
    },
    rules: {
      ...pluginReact.configs.flat.recommended.rules,
      // Common React rule adjustments for modern React
      "react/react-in-jsx-scope": "off", // Not needed in React 17+
      "react/prop-types": "off", // Often disabled when using TypeScript
      "react/display-name": "off" // Often too strict for functional components
    }
  },

  // JSON files
  {
    files: ["**/*.json"],
    ...json.configs.recommended
  },

  // JSONC files (JSON with comments)
  {
    files: ["**/*.jsonc"],
    language: "json/jsonc",
    ...json.configs.recommended
  },

  // JSON5 files
  {
    files: ["**/*.json5"],
    language: "json/json5",
    ...json.configs.recommended
  },

  // Markdown files
  {
    files: ["**/*.md"],
    ...markdown.configs.recommended
  },

  // CSS files
  {
    files: ["**/*.css"],
    ...css.configs.recommended
  },

  // Project-specific overrides - more lenient rules
  {
    files: ["**/*.{ts,tsx}"],
    rules: {
      // TypeScript-specific rule adjustments
      "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/no-explicit-any": "warn", // Warning instead of error
      "@typescript-eslint/ban-ts-comment": "warn"
    }
  },

  // Payload CMS specific overrides
  {
    files: ["**/payload.config.{js,ts}", "**/collections/**/*.{js,ts}", "**/globals/**/*.{js,ts}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off", // Payload often uses any types
      "@typescript-eslint/ban-ts-comment": "off"
    }
  }
];
