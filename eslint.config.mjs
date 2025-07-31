# Create a minimal config to test
cat > eslint.config.mjs << 'EOF'
import js from "@eslint/js";

export default [
  {
    ignores: ["node_modules/", "dist/"]
  },
  js.configs.recommended,
  {
    files: ["**/*.{js,ts,jsx,tsx}"],
    rules: {
      "no-unused-vars": "warn"
    }
  }
];
EOF
