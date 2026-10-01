import type { MetadataRoute } from "next";
import { T } from "@/lib/text";

// マニフェストが無いと、スマホでホーム画面に入れたとき入れた時点の URL(`/similar?diary=ID` など)から開くので、
// 開く所を `/` に決める。アイコンの PNG(public/)は app/icon.svg から書き出したもの
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: T.appName,
    short_name: T.appName,
    description: T.appDescription,
    id: "/",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#f6f5f1",
    theme_color: "#f6f5f1",
    icons: [
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml" },
      { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
