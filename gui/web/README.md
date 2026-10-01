# gui/web

`gui/api`(FastAPI)を叩く日記の画面(Next.js)。使い方は `../readme.md`。

```
npm install
npm run dev        # http://localhost:3000(/api/* は DIARY_API_URL=http://127.0.0.1:8766 へ流す)
npm run types      # ../api/openapi.json から lib/openapi.d.ts を作り直す
npm run typecheck
npm run lint
```
