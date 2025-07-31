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
      "coverage/"
    ]
  },

  // Base JavaScript configuration
  js.configs.recommended,

  // TypeScript configurations
  ...tseslint.configs.recommended,

  // JavaScript/TypeScript files
  {
    files: ["**/*.{js,mjs,cjs,ts,tsx}"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node
      }
    }
  },

  // React configuration
  {
    files: ["**/*.{jsx,tsx}"],
    ...pluginReact.configs.flat.recommended,
    settings: {
      react: {
        version: "18.3"
      }
    },
    rules: {
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off"
    }
  },

  // JSON configuration
  {
    files: ["**/*.json"],
    language: "json/json",
    ...json.configs.recommended
  },

  // Markdown configuration
  {
    files: ["**/*.md"],
    language: "markdown/gfm",
    ...markdown.configs.recommended
  },

  // CSS configuration
  {
    files: ["**/*.css"],
    language: "css/css",
    ...css.configs.recommended
  },

  // Lenient overrides
  {
    files: ["**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-unused-vars": "warn",
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/ban-ts-comment": "warn"
    }
  }
];
