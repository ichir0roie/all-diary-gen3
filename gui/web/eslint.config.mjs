import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // 画面を開いたときに API を読む(effect から fetch → 状態へ入れる)のが主な仕事なので、
      // effect 内の setState を一律に禁じるこのルールは切る
      "react-hooks/set-state-in-effect": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    // テストで起こす画面のビルド先(next.config.ts の DIARY_WEB_DIST_DIR)
    ".next-test/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
