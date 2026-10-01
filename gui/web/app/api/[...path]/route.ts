import { Sha256 } from "@aws-crypto/sha256-js";
import { createServerRunner } from "@aws-amplify/adapter-nextjs";
import { defaultProvider } from "@aws-sdk/credential-provider-node";
import { SignatureV4 } from "@smithy/signature-v4";
import { fetchAuthSession } from "aws-amplify/auth/server";
import { cookies } from "next/headers";
import type { NextRequest } from "next/server";
import { amplifyConfig, loginRequired } from "@/lib/auth";
import { T } from "@/lib/text";

// ブラウザは同じオリジンの `/api/*` を叩き、ここがサーバー側で API(FastAPI)へ流す。
// 公開の API(Lambda の関数 URL)に置くときの合言葉 `DIARY_API_KEY` はここでだけ足し、ブラウザには渡さない
const apiUrl = (process.env.DIARY_API_URL ?? "http://127.0.0.1:8766").replace(/\/+$/, "");
const apiKey = process.env.DIARY_API_KEY ?? "";
const API_KEY_HEADER = "x-diary-api-key";
// 誰の日記かを API に伝える見出し。ブラウザから来た同じ名前の見出しは流さず(REQUEST_HEADERS に無い)、ここで確かめた人だけを入れる
const USER_HEADER = "x-diary-user";
// ログインを掛けない手元の gui.dev で、日記を書く人として扱う id
const localUserId = process.env.DIARY_LOCAL_USER_ID ?? "local";

// クッキーのトークンは、adapter-nextjs が Cognito の公開鍵で署名を確かめてから読む
const { runWithAmplifyServerContext } = createServerRunner({ config: amplifyConfig });

const REQUEST_HEADERS = ["content-type", "accept"];
const RESPONSE_HEADERS = ["content-type", "cache-control", "location", "content-disposition"];

// Lambda の関数 URL は認証が AWS_IAM なので、Amplify の SSR のコンピュートロールで SigV4 の署名を付ける。手元の API には付けない
const lambdaUrlRegion = /\.lambda-url\.([a-z0-9-]+)\.on\.aws$/.exec(new URL(apiUrl).hostname)?.[1];
const signer = lambdaUrlRegion
  ? new SignatureV4({ service: "lambda", region: lambdaUrlRegion, credentials: defaultProvider(), sha256: Sha256, applyChecksum: true })
  : null;

export const dynamic = "force-dynamic";

/** 要求を出した人の Cognito の sub。ログインしていなければ null */
async function signedInUser(): Promise<string | null> {
  try {
    return await runWithAmplifyServerContext({
      nextServerContext: { cookies },
      operation: async (context) => {
        const sub = (await fetchAuthSession(context)).tokens?.accessToken.payload.sub;
        return typeof sub === "string" ? sub : null;
      },
    });
  } catch {
    return null;
  }
}

// 署名は問い合わせを RFC 3986 で符号化し直した形で計算するので、送る方も同じ形に揃える(`+` と `%20` の食い違いで署名が外れる)
function encodeQuery(params: URLSearchParams): string {
  const rfc3986 = (value: string) => encodeURIComponent(value).replace(/[!'()*]/g, (c) => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);
  const pairs = [...params].map(([key, value]) => `${rfc3986(key)}=${rfc3986(value)}`);
  return pairs.length ? `?${pairs.join("&")}` : "";
}

async function sign(target: URL, method: string, headers: Headers, body: Uint8Array | undefined): Promise<Headers> {
  if (!signer) return headers;
  const query: Record<string, string[]> = {};
  for (const [key, value] of target.searchParams) (query[key] ??= []).push(value);
  const signed = await signer.sign({
    method,
    protocol: target.protocol,
    hostname: target.hostname,
    path: target.pathname,
    query,
    headers: { ...Object.fromEntries(headers), host: target.hostname },
    body,
  });
  // host は fetch が URL から付ける
  return new Headers(Object.entries(signed.headers).filter(([name]) => name.toLowerCase() !== "host"));
}

async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }): Promise<Response> {
  // ログインを掛けずに localUserId として流してよいのは手元の API だけ。署名や合言葉の要る公開の API に置いたのにユーザープールの
  // 変数が欠けていたら、誰でも localUserId の日記を読み書きできてしまうので、流さずに止める
  if (!loginRequired && (signer || apiKey)) {
    console.error("NEXT_PUBLIC_DIARY_USER_POOL_ID / NEXT_PUBLIC_DIARY_USER_POOL_CLIENT_ID が無いので、公開の API へは流さない");
    return Response.json({ detail: T.signInRequired }, { status: 401 });
  }
  const userId = loginRequired ? await signedInUser() : localUserId;
  if (!userId) return Response.json({ detail: T.signInRequired }, { status: 401 });
  // ログインのクッキーは別のサイトからの要求にも付きうるので、ブラウザが別のサイトからと告げる要求は流さない(CSRF 除け)。
  // 見出しの無い要求(古いブラウザ・手元の curl)はクッキーの SameSite に任せる
  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite && fetchSite !== "same-origin" && fetchSite !== "none") {
    return Response.json({ detail: T.crossSiteRejected }, { status: 403 });
  }
  const { path } = await context.params;
  const target = new URL(`${apiUrl}/api/${path.map(encodeURIComponent).join("/")}`);
  target.search = encodeQuery(request.nextUrl.searchParams);
  const headers = new Headers();
  for (const name of REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  headers.set(USER_HEADER, userId);
  if (apiKey) headers.set(API_KEY_HEADER, apiKey);
  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const body = hasBody ? new Uint8Array(await request.arrayBuffer()) : undefined;
  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers: await sign(target, request.method, headers, body),
      body,
      cache: "no-store",
      redirect: "manual",
    });
  } catch (e) {
    // 流し先の URL(関数 URL)はブラウザに見せず、サーバーのログにだけ出す
    console.error(`API(${apiUrl})に届かない: ${e instanceof Error ? e.message : String(e)}`);
    return Response.json({ detail: T.apiUnreachable }, { status: 502 });
  }
  const responseHeaders = new Headers();
  for (const name of RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }
  return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export { forward as GET, forward as POST, forward as PATCH, forward as PUT, forward as DELETE };
