import type { NextConfig } from "next";

// どのページにも付ける守りの見出し。ログインのトークンはスクリプトから読めるクッキーにあるので、
// よそのページに埋め込ませない・型を推し量らせない・URL をよそへ漏らさない
const SECURITY_HEADERS = [
  { key: "Content-Security-Policy", value: "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "no-referrer" },
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
];

// `/api/*` は `app/api/[...path]/route.ts` が API(FastAPI、`DIARY_API_URL`)へ流す
const nextConfig: NextConfig = {
  // next dev はビルド先ごとに 1 つしか動かせないので、テストで起こすときは別のビルド先(`.next-test`)を渡す
  distDir: process.env.DIARY_WEB_DIST_DIR ?? ".next",
  // dev 起動のたびに AGENTS.md / CLAUDE.md を生やさない
  agentRules: false,
  poweredByHeader: false,
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
};

export default nextConfig;
