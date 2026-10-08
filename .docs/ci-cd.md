# 自動デプロイ(GitHub → Lambda / Amplify)

| 何を | きっかけ | 仕組み |
| --- | --- | --- |
| API(Lambda) | `main` への push のうち、API が読むコード(`data_access_logic/` `db/` `gui/api/` `requirements.txt` `infra/lambda/`)が変わったとき。手で回すなら Actions の「Run workflow」 | `.github/workflows/deploy-api.yml` |
| 画面(Amplify) | `main` への push | Amplify が GitHub を見て `amplify.yml` で建てる(GitHub Actions は使わない) |
| db のマイグレーション | 手で | 下の「マイグレーション」 |

## API の流れ

1. `ruff check`(実行時の誤りだけを見る設定。`ruff.toml`)
2. OIDC で AWS のロールを引き受ける(鍵を GitHub に置かない)
3. `infra/lambda/Dockerfile` を `linux/arm64` で建て、ECR に `<commit の sha>` と `main` の二つの tag で push
   (`--provenance=false`。Lambda は複数アーキの目録を受け付けない)
4. `aws lambda update-function-code`(`<commit の sha>` の tag)→ 反映を待つ
5. 秘密の `API_BASE_URL` があれば、SigV4 の署名を付けて `/api/ping` を叩いて確かめる

変数 `LAMBDA_FUNCTION_NAME` が無ければ、ジョブは飛ばされる(フォークや設定前に落ちないようにしている)。
公開リポジトリの Actions のログは誰でも読め、変数(Variables)はログに伏せ字にならない。
アカウント ID を含むロールの ARN と関数 URL は秘密(Secrets)に置く(ログでは `***` になる)。アカウント ID も `mask-aws-account-id` で伏せる。

Settings → Secrets and variables → Actions の **Variables**:

| 変数 | 例 |
| --- | --- |
| `AWS_REGION` | `ap-northeast-1` |
| `ECR_REPOSITORY` | `diary-api` |
| `LAMBDA_FUNCTION_NAME` | `diary-api` |

同じ画面の **Secrets**:

| 秘密 | 例 |
| --- | --- |
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::<アカウント ID>:role/github-all-diary-deploy` |
| `API_BASE_URL` | Lambda の関数 URL(任意。煙の確かめ用。末尾の `/` は除く) |

## CDK との分担

関数は `infra/` の CDK(`DiaryApi`)で持つが、関数のコード(イメージ)だけは CI が差し替える。

| 持ち主 | 持つもの |
| --- | --- |
| CDK(手元から `cdk deploy`) | ECR リポジトリ `diary-api`(ライフサイクルで新しい 30 個を残す)、関数の設定(環境変数・VPC・実行ロール・関数 URL)、GitHub Actions の OIDC のロール |
| CI(`deploy-api.yml`) | イメージを建てて push し、関数のコードを差し替える |

- CDK は関数を `diary-api:main` のイメージで作り、自分ではイメージを建てない。`cdk deploy` は template の `ImageUri` が変わらない限りコードに触れないので、
  CI が差し替えたイメージは、そのあとの `cdk deploy` でも戻らない
- CI からは `cdk deploy` を流さない。CI の権限を ECR への push とその関数のコードの差し替えだけに絞る
  (`cdk deploy` を許すと、bootstrap の実行ロールを通してアカウントを何でも変えられるようになり、synth のときに読む合言葉も CI に渡すことになる)
- 最初の一回は、関数を作る前に手元で建てて `main` の tag で push する(関数が無いと、CI の `update-function-code` が落ちる)。
  順番は、ECR を deploy → 手元で push → 関数を deploy

## AWS 側の用意(一度だけ)

ECR・OIDC・CI のロールは手で作らず、`infra/` の `DiaryCi` スタック(`infra/lib/ci-stack.ts`)で作る。

1. `infra` で `npx cdk deploy DiaryCi`
2. 出力の `DeployRoleArn` を、リポジトリの秘密 `AWS_DEPLOY_ROLE_ARN` に置く

CI のロールの信頼は、SSM の `/diary/deploy/config` に書いたリポジトリの `main` だけ(PR やフォークから引き受けられないようにする)。
権限は `diary-api` の ECR への push と読み取り、関数 `diary-api` の `UpdateFunctionCode`・`GetFunction`・`GetFunctionConfiguration` と、
差し替えたあとの確かめに関数 URL を呼ぶことだけ。

## マイグレーション

コードと db の形は揃えて出す必要がある。列を足す変更は **db を先に、コードを後に** 出す(古いコードは新しい列を知らないだけで動く)。
列を消す・名前を変える変更は、コードを先に消す側へ直してから db を変える。

AWS の db へは、作業する端末から踏み台越しに当てる([aws-deploy.md](aws-deploy.md#手元から-db-へ繋ぐ))。

```
.venv/bin/python -m alembic -c db/alembic/alembic.ini current                                   # 版を見るだけなら、ふだんの接続でよい
.venv/bin/python -m tool.aws.rds -- .venv/bin/python -m alembic -c db/alembic/alembic.ini upgrade head   # 当てるのはマスターで
```

GitHub Actions からは当てない(db への道をワークフローに開けたくない・マイグレーションは中身を見てから当てたい)。

## 画面(Amplify)

- Amplify のアプリを `main` に繋ぐと、push のたびに `amplify.yml` で建て直す。モノレポのアプリのパスを `gui/web` にしておく(`AMPLIFY_MONOREPO_APP_ROOT`)
- 型(`gui/web/lib/openapi.d.ts`)は API の OpenAPI から作ってコミットしてあるので、Amplify のビルドは python を要らない
- API を変えた PR は、Lambda の反映(数分)を待ってから画面が出るよう、API の変更を先に `main` へ入れるか、互換を保つ形にする
