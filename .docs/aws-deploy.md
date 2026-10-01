# AWS に置く

画面(`gui/web`)を Amplify Hosting、API(`gui/api`)を Lambda + Lambda Web Adapter、db を RDS for PostgreSQL、ログインを Cognito に置く。
リソースは `infra/` の CDK(TypeScript)で持つ。費用を抑えるため、アカウントに既にあるリソース(ai-novel-core の RDS・踏み台など)は
作り直さずに参照できる。全体の図は [README.md](README.md)。

## 構成と決めたこと

| 部品 | 置き場所 | 決めたこと |
| --- | --- | --- |
| 画面 | Amplify Hosting(SSR) | モノレポの `gui/web` だけを建てる(`amplify.yml`)。ブラウザは同じオリジンの `/api/*` を叩き、Next.js の route handler(`gui/web/app/api/[...path]/route.ts`)がサーバー側で API へ流す |
| ログイン | Cognito のユーザープール(`DiaryAuth`) | 画面は Amplify の Auth で入る。画面からの登録は閉じ、使う人は CLI で作る |
| API | Lambda(コンテナ)+ 関数 URL(`AWS_IAM`) | `infra/lambda/Dockerfile`。Lambda Web Adapter が Lambda のイベントを HTTP に直すので、アプリは uvicorn で起こすだけ。コードに Lambda 専用の分岐を持たない |
| db | RDS for PostgreSQL(db.t4g.micro 程度) | private subnet に置き、公開しない。手元からは踏み台越しにだけ繋ぐ(下の「手元から db へ繋ぐ」)。ai-novel-core の RDS を使い回すなら、同じインスタンスに db `diary` を作る |
| リソースの管理 | `infra/`(AWS CDK) | コンソールで手で作らない。構築ごとの設定はリポジトリに書かず、SSM の `/diary/deploy/config` に置く(下の「構築ごとの設定」) |

### 構築ごとの設定

このリポジトリは公開で、誰がクローンしても自分の AWS アカウントに建てられる形にしてある。そのため、アカウント ID やリソースの ID は
リポジトリのどこにも書かない。

- アカウントとリージョンは、`cdk` を動かす人の AWS CLI のプロファイルから取る
- 構築ごとの設定は、構築するアカウントの SSM パラメータ `/diary/deploy/config` に JSON で置く(標準のパラメータなので料金は掛からない)。
  `infra/` は synth のときにこれを読む(無ければ止まる)。形の見本は `infra/aws.example.json`。埋めたものを置くには:
  `aws ssm put-parameter --name /diary/deploy/config --type String --value file://aws.json`(直すときは `--overwrite` を足す)

  ```json
  {
    "github": { "repository": "<owner>/<repo>", "branch": "main" },
    "existing": {
      "vpcId": "vpc-…",
      "dbInstanceIdentifier": "<RDS のインスタンス名>",
      "bastion": { "instanceId": "i-…", "instanceConnectEndpointId": "eice-…" },
      "functionSubnetIds": ["subnet-…", "subnet-…"]
    }
  }
  ```

  | 項目 | 中身 |
  | --- | --- |
  | `github` | 必須。CI のロールを引き受けられる、自分のリポジトリとブランチ |
  | `github.subClaimPrefix` | 任意。GitHub の OIDC の sub の前半。リポジトリが immutable subject なら要る。`gh api repos/<owner>/<repo>/actions/oidc/customization/sub` の `sub_claim_prefix` をそのまま置く。無ければ `repo:<repository>` |
  | `existing` | 全部任意。無いものはスタックが作る |
  | `existing.vpcId` | 無く、`dbInstanceIdentifier` があれば、その db の VPC を使う |
  | `existing.dbInstanceIdentifier` | 使い回す RDS。マスターのパスワードは RDS の管理(`--manage-master-user-password`)にしておく。エンドポイント・セキュリティグループ・秘密の ARN は、synth のときにこの名前から引く |
  | `existing.bastion` | 使い回す踏み台と EC2 Instance Connect Endpoint。ai-novel-core の SSM の `/novel/bastion/*` の値と同じものを書けばよい |
  | `existing.functionSubnetIds` | Lambda を置く subnet。無ければ VPC の isolated subnet を全部使う |
  | `existing.githubOidcProviderArn` | 使い回す GitHub の OIDC プロバイダ(`token.actions.githubusercontent.com`)。アカウントに一つしか置けないので、ai-novel-core の `NovelCi` が作り済みならその ARN を書く(`aws iam list-open-id-connect-providers`)。無ければ `DiaryCi` が作る |

- 使い回すリソースの ID が無ければ、`DiaryData` が次を作る。作った値も SSM の `/diary/*` に置く
- deploy のあとに決まる値(関数 URL など)は SSM の `/diary/*` に置き、手元の道具や Amplify の設定はそこから引く
- CDK が手元に貯める `infra/cdk.context.json` は、アカウントやリソースの ID を含むので git に入れない

| リソース | 役目 |
| --- | --- |
| VPC | 2 AZ の isolated subnet だけ。NAT ゲートウェイもインターネットゲートウェイも置かないので、外(インターネット)へは出られない |
| RDS for PostgreSQL(db.t4g.micro・20 GB) | IAM データベース認証・バックアップ 7 日・削除保護を有効にし、消すときはスナップショットを残す。セキュリティグループは、踏み台と Lambda のセキュリティグループからの 5432 だけを通す |
| EC2 の踏み台(t4g.nano・公開 IP 無し) | ふだんは止めておき、使うときだけ起こす |
| EC2 Instance Connect Endpoint | 公開 IP の無い踏み台へ、AWS の API 越しに SSH を通す(料金は掛からない) |

## infra(CDK)

`infra` で動かす。bootstrap(`CDKToolkit`)は済んでいる前提。

```
cd infra
npm install
npx cdk diff      # 変わるものを見る
npx cdk deploy    # 当てる
```

| スタック | 中身 |
| --- | --- |
| `DiaryData` | 手元の道具とほかのスタックが引く値を、SSM パラメータ `/diary/*` に置く(db のエンドポイント・ポート・db 名・マスターの秘密の ARN、踏み台と EC2 Instance Connect Endpoint の ID) |
| `DiaryCi` | ECR リポジトリ `diary-api`、GitHub の OIDC プロバイダ、CI のロール `github-all-diary-deploy`([ci-cd.md](ci-cd.md)) |
| `DiaryApi` | Lambda `diary-api`(VPC の中)・関数 URL・セキュリティグループ・実行ロール・ログの出し先(保存 2 週間)・Amplify の SSR が関数 URL を呼ぶロール。関数 URL は SSM の `/diary/api/function-url` にも出す |
| `DiaryAuth` | 画面のログインに使う Cognito のユーザープール(料金区分 Lite)と、画面用のアプリクライアント。ID は SSM の `/diary/auth/user-pool-id`・`/diary/auth/user-pool-client-id` に出す |

GitHub の OIDC プロバイダはアカウントに一つしか作れない。ai-novel-core の `NovelCi` が作り済みなら、`existing.githubOidcProviderArn` に
その ARN を書いてから `DiaryCi` を deploy する(書かないと、プロバイダを作れずに止まる)。

## 手元から db へ繋ぐ

```
手元 ──ssh(EC2 Instance Connect Endpoint の open-tunnel)──▶ 踏み台 ──5432──▶ RDS
```

`tool.aws.rds` が、踏み台を起こすところから転送を張るところまでを行う。リポジトリのルートで:

```
.venv/bin/python -m tool.aws.rds --serve   # ふだん用。127.0.0.1:25432 に転送を張り続ける
.venv/bin/python -m tool.aws.rds -- .venv/bin/python -m alembic -c db/alembic/alembic.ini upgrade head   # マスターで流す
.venv/bin/python -m tool.aws.rds --database postgres -- psql
.venv/bin/python -m tool.aws.rds          # マスターで繋いだまま $SHELL を開く。exit で閉じる
```

| 使い方 | 繋ぐ db のロール | 認証 |
| --- | --- | --- |
| `--serve`(ふだんの読み書き。SessionStart フックと VS Code のタスク「db tunnel」が起こす) | `diary_app`(行の読み書きだけ) | IAM データベース認証。`DIARY_DATABASE_URL=postgresql+psycopg://diary_app@127.0.0.1:25432/diary?sslmode=require` と `DIARY_DATABASE_IAM_AUTH=1` を渡した python が、繋ぐたびにトークンを作る。トークンは RDS の本来のエンドポイント(SSM の `/diary/db/endpoint`)に宛てて作る |
| `-- <コマンド>`(マイグレーション・表の権限を変える SQL など、DDL が要る作業) | マスター | RDS が管理する秘密からパスワードを読み、`DIARY_DATABASE_URL`・`PG*` にして渡す。既定のポートは 25433 |

- 要るもの: AWS CLI v2、ssh、AWS の権限(`ssm:GetParametersByPath`・`ssm:GetParameters`・`ec2:DescribeInstances`・`ec2:StartInstances`・`ec2:StopInstances`・
  `ec2-instance-connect:SendSSHPublicKey`・`ec2-instance-connect:OpenTunnel`・`rds-db:connect`(`diary_app`)・`secretsmanager:GetSecretValue`(マスター))
- 自分で起こした踏み台は、終わるときに止める。踏み台を ai-novel-core と使い回していると、向こうの転送も切れる

## 最初に建てる手順

1. API の合言葉を SSM の SecureString に作る。`infra/` は synth のときにこれを読むので、一番初めに作る

   ```
   aws ssm put-parameter --name /diary/api-keys/gui --type SecureString --value "$(openssl rand -hex 32)"
   ```

2. 構築ごとの設定(`/diary/deploy/config`)を置く(上の「構築ごとの設定」)
3. `npx cdk deploy DiaryData`
4. db `diary` と表を作り、アプリのロール `diary_app` を作る(マスターで)

   ```
   .venv/bin/python -m tool.aws.rds --database diary -- .venv/bin/python -m db.postgres.init_db --create-database
   .venv/bin/python -m tool.aws.rds --database diary -- psql -v ON_ERROR_STOP=1 -f infra/sql/diary_app.sql
   ```

5. `npx cdk deploy DiaryCi`([ci-cd.md](ci-cd.md#aws-側の用意一度だけ))
6. 最初のイメージを手元で建て、`main` の tag で push する(`infra/lambda/push-image.sh`)。以降は GitHub Actions が `<sha>` と `main` で push する
7. `npx cdk deploy DiaryApi DiaryAuth`
8. 画面(Amplify)を建てる(下の「画面(Amplify)」)

確かめ: 関数 URL は `AWS_IAM` なので、SigV4 の署名を付けて `curl --aws-sigv4 "aws:amz:<リージョン>:lambda" … <関数 URL>/api/ping` が `{"ok":true}`。

## 画面(Amplify)

1. Amplify Hosting で、自分のリポジトリの `main` を繋ぐ。モノレポとして `gui/web` を指定する
   (ビルド設定はリポジトリのルートの `amplify.yml` が使われる)
2. SSR のコンピュートロールに、SSM の `/diary/amplify/compute-role-arn` のロールを付ける
   (`aws amplify update-app --app-id <アプリの ID> --compute-role-arn <ロールの ARN>`)
3. 環境変数

| 変数 | 値 |
| --- | --- |
| `AMPLIFY_MONOREPO_APP_ROOT` | `gui/web` |
| `DIARY_API_URL` | SSM の `/diary/api/function-url`(末尾の `/` は無くてよい) |
| `DIARY_API_KEY` | SSM の `/diary/api-keys/gui` |
| `NEXT_PUBLIC_DIARY_USER_POOL_ID` | SSM の `/diary/auth/user-pool-id` |
| `NEXT_PUBLIC_DIARY_USER_POOL_CLIENT_ID` | SSM の `/diary/auth/user-pool-client-id` |

`amplify.yml` がビルドのときに `DIARY_API_URL`・`DIARY_API_KEY` を `.env.production` に写す(SSR のサーバーは実行時にコンソールの環境変数を
読めないため)。`NEXT_PUBLIC_*` は秘密ではなく、`next build` がブラウザ向けのコードにも埋め込む。
`AMPLIFY_APP_ORIGIN` は置かない(置くと adapter-nextjs がサーバー側でログインする形に切り替わり、画面の Authenticator が使えなくなる)。

4. 画面に入る人を Cognito に作る(画面からの登録は閉じてある)。仮のパスワードがメールで届き、最初のログインで替える:
   `aws cognito-idp admin-create-user --user-pool-id <ユーザープールの ID> --username <メールアドレス> --user-attributes Name=email,Value=<メールアドレス> Name=email_verified,Value=true`
5. 以前の日記を移す([migration.md](migration.md#データを移す))
6. 以降は `main` への push で Amplify が建て直す

## 守り

秘密の置き場所の一覧、公開する前に手で整える設定、残っている課題は [security.md](security.md)。

1. 画面: Cognito(`DiaryAuth`)にログインするまで中身を出さない(`gui/web/components/AuthGate.tsx`)。トークンはクッキーに置き、
   `/api/*` の route handler が adapter-nextjs で Cognito の公開鍵による署名を確かめてから、その人の sub を `x-diary-user` に入れて流す。
   ブラウザが付けた `x-diary-user` は流さず、ブラウザが別のサイトからと告げる要求(`Sec-Fetch-Site`)は 403 にする。`NEXT_PUBLIC_DIARY_USER_POOL_*` が欠けていると、`amplify.yml` がビルドを失敗させる。
   それでも欠けたまま建った場合、流し先が公開の API(署名か合言葉の要る先)なら、route handler はログインなしで流さず 401 を返す
2. API: 関数 URL は `AWS_IAM` で、Amplify の SSR のコンピュートロールの署名が無い要求は Lambda が起きる前に弾く。
   その上で合言葉(`x-diary-api-key`。Lambda の `DIARY_API_KEYS` の `gui=`)が合わない要求を 401 にする(`/api/ping` だけは通す)
3. db: Lambda が使うロール `diary_app` には行の読み書き(DML)だけを許す。API に任意の SQL を受ける口は作らず、入口は必ず `user_id` で行を絞る。
   RDS の自動バックアップを 7 日保ち、削除保護を掛ける

合言葉を替える:

1. `aws ssm put-parameter --name /diary/api-keys/gui --type SecureString --overwrite --value "$(openssl rand -hex 32)"`
2. `infra` で `npx cdk deploy DiaryApi`。Lambda の環境変数が替わり、古い鍵はその時点で通らなくなる
3. Amplify の `DIARY_API_KEY` を替えて建て直す

## ローカルとの違い

| | ローカル(`gui.dev`) | AWS |
| --- | --- | --- |
| db | 同じ RDS(踏み台越しの転送、`diary_app` の IAM 認証)か、手元の開発用の db | RDS for PostgreSQL(db `diary`。VPC の中から、`diary_app` の IAM 認証) |
| `/api/*` の流し先 | `DIARY_API_URL` 既定 `http://127.0.0.1:8766` | Lambda の関数 URL(SigV4 の署名付き) |
| ログイン | 無し(`NEXT_PUBLIC_DIARY_USER_POOL_*` が空)。`DIARY_LOCAL_USER_ID` の人として流す | Cognito |
| 合言葉 | 無し(`DIARY_API_KEY` 空) | 有り |
