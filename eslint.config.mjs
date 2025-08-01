import js from "@eslint/js";
import globals from "globals";
import pluginReact from "eslint-plugin-react";
import tseslint from "typescript-eslint";

export default [
  {
    ignores: ["node_modules/", "dist/", "build/", "coverage/", "frontend/build/", "frontend/coverage/", "*.min.js"]
  },
  js.configs.recommended,
  
  {
    files: ["**/*.{js,jsx}"],
    ...pluginReact.configs.flat.recommended,
    languageOptions: {
      ...pluginReact.configs.flat.recommended.languageOptions,
      globals: {
        ...globals.browser, 
        ...globals.node,
        React: "readonly"
      }
    },
    settings: {react: {version: "18.3"}},
    rules: {
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "no-unused-vars": "off",
      "no-undef": "warn"
    }
  },
  
  ...tseslint.configs.recommended.map(config => ({
    ...config,
    files: ["**/*.{ts,tsx}"],
    rules: {
      ...config.rules,
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/ban-ts-comment": "off"
    }
  })),
  
  {
    files: ["**/*.{tsx}"],
    ...pluginReact.configs.flat.recommended,
    languageOptions: {
      ...pluginReact.configs.flat.recommended.languageOptions,
      globals: {...globals.browser}
    },
    settings: {react: {version: "18.3"}},
    rules: {
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off"
    }
  },
  
  {
    files: ["**/cypress.config.{js,ts}", "**/cypress/**/*.{js,ts}", "**/*.cy.{js,ts}"],
    languageOptions: {
      globals: {...globals.node, ...globals.browser, cy: "readonly", Cypress: "readonly"}
    },
    rules: {
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "@typescript-eslint/no-require-imports": "off"
    }
  },
  
  {
    files: ["**/*.test.{js,ts,jsx,tsx}", "**/*.spec.{js,ts,jsx,tsx}", "**/test/**/*.{js,ts}", "**/tests/**/*.{js,ts}", "**/__tests__/**/*.{js,ts}"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.jest,
        describe: "readonly",
        it: "readonly",
        test: "readonly",
        expect: "readonly",
        before: "readonly",
        after: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly"
      }
    },
    rules: {
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": "off"
    }
  },
  
  {
    files: ["**/payload.config.{js,ts}", "**/payload/**/*.{js,ts,tsx}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "off"
    }
  },
  
  {
    files: ["frontend/src/components/cms/CoworkingPageBuilder.js"],
    rules: {
      "no-case-declarations": "off"
    }
  }
];
