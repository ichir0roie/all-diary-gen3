# 機密情報と守り

日記は書いた人の最も私的な記録で、このリポジトリは公開されている。ここには、どの秘密がどこにあって誰が読めるか、
どの層で何を守っているか、公開する前に手で整える設定、まだ残っている課題をまとめる。
AWS の構成と建て方は [aws-deploy.md](aws-deploy.md)、CI は [ci-cd.md](ci-cd.md)。

## 守るもの

| 守るもの | 重さ | 置き場所 |
| --- | --- | --- |
| 日記・コメントの本文 | 最も重い | RDS(db `diary`)だけ。リポジトリ・ログ・CI には出さない |
| ログインの手段 | 重い | Cognito(パスワード)と、ブラウザのクッキー(トークン) |
| AWS への入口 | 重い | 合言葉、RDS のマスターのパスワード、CI のロール |
| 構築の値(アカウント ID・リソースの ID・関数 URL など) | 秘密ではないが足掛かりになる | SSM の `/diary/*`。リポジトリには書かない([aws-deploy.md](aws-deploy.md#構築ごとの設定)) |

## 秘密の置き場所

| 秘密 | 本体の置き場所 | 写しがある所 | 読める者 | 替え方 |
| --- | --- | --- | --- | --- |
| API の合言葉(`gui`) | SSM `/diary/api-keys/gui`(SecureString) | Lambda の環境変数 `DIARY_API_KEYS`(CloudFormation の template にも平文で載る)、Amplify の環境変数 `DIARY_API_KEY`、Amplify のビルドが作る `.env.production` | AWS で SSM・Lambda・CloudFormation・Amplify を読める人 | [aws-deploy.md](aws-deploy.md#守り)の「合言葉を替える」 |
| RDS のマスターのパスワード | Secrets Manager(RDS の管理。自動で替わる) | 無し(`tool.aws.rds --` がその場で読み、子のプロセスにだけ渡す) | `secretsmanager:GetSecretValue` を持つ人 | RDS が替える |
| `diary_app` の db への鍵 | 無し(パスワードを持たない) | IAM データベース認証のトークン(15 分) | `rds-db:connect` を持つ Lambda の実行ロールと手元の人 | 不要 |
| 使う人のパスワード | Cognito | 無し | 無し | 画面の「パスワードを忘れた」か `aws cognito-idp admin-set-user-password` |
| ログインのトークン | ブラウザのクッキー(スクリプトから読める) | 無し | そのブラウザ(と、そのページで動くスクリプト) | 画面でサインアウト。全端末から追い出すなら `aws cognito-idp admin-user-global-sign-out` |
| GitHub から AWS への権限 | 無し(OIDC で毎回一時的な鍵をもらう) | 無し | `main` への push で動くワークフロー | 不要 |
| CI のロールの ARN・関数 URL | GitHub の Secrets(`AWS_DEPLOY_ROLE_ARN`・`API_BASE_URL`) | 無し(ログでは `***`) | リポジトリの管理者 | Secrets を書き直す |

- 秘密の値はリポジトリ・コミット・ログ・PR・Claude への報告に出さない。`.env*`・`*.csv`・`*.db` は `.gitignore` で弾いている
- 日記の CSV や以前の SQLite のファイルを手元で扱ったら、使い終わったときに消す(`tmp/` は git に入らないが、手元の disk には残る)
- Claude Code on the web のセッションは db に繋がない(`CLAUDE.md`)。その環境の変数や secrets に、AWS の鍵や `DIARY_DATABASE_URL` を置かない

## 層ごとの守り

```
ブラウザ ─①─▶ 画面(Amplify の SSR)─②─▶ API(Lambda の関数 URL)─③─▶ RDS
```

| 層 | 守り | 置き場所 |
| --- | --- | --- |
| ① ブラウザ → 画面 | Cognito にログインするまで中身を出さない。画面からの登録は閉じている | `AuthGate.tsx`・`DiaryAuth` |
| | route handler がクッキーのトークンの署名を Cognito の公開鍵で確かめ、その人の sub を `x-diary-user` に入れる。ブラウザが付けた `x-diary-user` は流さない | `app/api/[...path]/route.ts` |
| | ブラウザが別のサイトからと告げる要求(`Sec-Fetch-Site` が `cross-site`・`same-site`)は 403 にする(CSRF 除け) | 同上 |
| | どのページにも、よそへの埋め込みを禁じる・型の推し量りを禁じる・リファラを出さない・HTTPS を強いる見出しを付ける | `next.config.ts` |
| | ユーザープールの変数が欠けていれば、ビルドを止め、route handler も流さない | `amplify.yml`・`route.ts` |
| ② 画面 → API | 関数 URL は `AWS_IAM`。Amplify の SSR のコンピュートロールの署名が無い要求は、Lambda が起きる前に弾かれる | `DiaryApi` |
| | その上で合言葉(`x-diary-api-key`)を比べる(時間の一定な比較) | `gui/api/app.py` |
| | 同時実行を 3 に絞り、呼ぶ側が暴れても費用と db の接続数が膨らまない | `DiaryApi` |
| ③ API → db | Lambda は NAT の無い VPC の中。外へ出る道が無い | `DiaryData`・`DiaryApi` |
| | db のロール `diary_app` は行の読み書きだけ(DDL 無し)。パスワードを持たず IAM 認証で繋ぐ | `infra/sql/diary_app.sql` |
| | 任意の SQL を受ける口は無い。入口は必ず `user_id` で行を絞る | `data_access_logic/` |
| | RDS は公開せず、バックアップ 7 日・削除保護 | `DiaryData` |
| 誤りの知らせ | db やドライバの文言・関数 URL は画面に返さず、サーバーのログにだけ出す。ログには本文を出さない | `gui/api/app.py`・`route.ts` |
| CI | ロールは `main` の push だけが引き受けられ、できるのは ECR への push と関数のコードの差し替えだけ。action は SHA で固定し、Dependabot が上げる | `DiaryCi`・`deploy-api.yml` |

## 公開する前に手で整えること

コードでは持てない、アカウントやリポジトリの設定。

GitHub(リポジトリの Settings):

- [ ] `main` を保護する(ルールセットで、PR を通す・force push と削除を禁じる)。`main` への push はそのまま本番の Lambda と Amplify に出て、
  CI のロールも `main` を信じるので、`main` に入るものが本番になる
- [ ] Code security で、Secret scanning・Push protection・Dependabot alerts・Private vulnerability reporting を有効にする
- [ ] Actions → General で、外部の人のフォークからの PR のワークフローは承認を要るようにし、`GITHUB_TOKEN` の既定の権限を読み取りだけにする

AWS:

- [ ] ルートユーザーに MFA を掛け、日々の作業はルートでしない
- [ ] AWS Budgets で月の上限の知らせを置く(関数 URL を叩かれても署名が無ければ料金は出ないが、念のため)
- [ ] Amplify の PR のプレビューは切ったままにする(公開リポジトリでは、プレビューのビルドに環境変数の合言葉が渡る)
- [ ] 使い回す RDS がストレージを暗号化しているか確かめる(`aws rds describe-db-instances --query 'DBInstances[].StorageEncrypted'`。
  暗号化していなければ `cdk synth` も知らせる)
- [ ] 合言葉は `openssl rand -hex 32` で作り、人に見せたり、どこかに貼ったりしたら替える

コミットの前:

- [ ] `.claude/docs/aws.md` の「公開リポジトリ」の grep で、構築の値が紛れていないか見る

## 残っている課題

重いものから。どれも構成や使い勝手を変えるので、まだ入れていない。

1. **二段階認証が無い。** パスワードが漏れれば日記を全部読まれる。Cognito の Lite でも TOTP(認証アプリ)は使える。
   `mfa: REQUIRED` はユーザープールを作るときにしか選べないので、今のプールでは `OPTIONAL` と `mfaSecondFactor: { otp: true, sms: false }` にし、
   画面に TOTP を登録する所(aws-amplify の `setUpTOTP`・`verifyTOTPSetup`・`updateMFAPreference`)を足す
2. **トークンがスクリプトから読めるクッキーにあり、更新のトークンが 365 日もつ。** 画面に XSS があれば、1 年使える鍵を持ち出される。
   更新のトークンを 30〜90 日に縮めるか、nonce を使った `script-src` の Content-Security-Policy を足す(Next.js の proxy で nonce を振る)。
   今の見出しは埋め込みなどを禁じるだけで、スクリプトの出所は絞っていない
3. **CDK が作る RDS のストレージが暗号化されていない。** `storageEncrypted` を足すとインスタンスの作り直しになる(削除保護で deploy が止まる)。
   スナップショットを取り、暗号化して写し、そこから建て直して付け替える。使い回す RDS は上のチェックリストで確かめる
4. **合言葉の写しが多い。** Lambda の環境変数(CloudFormation の template にも平文)、Amplify の環境変数、`.env.production` にある。
   Lambda には鍵の SHA-256 だけを渡して比べる形にすれば、template から本体が消える
5. **db への TLS が証明書を確かめていない(`sslmode=require`)。** VPC の中なので差し迫ってはいないが、RDS の CA の束を Lambda のイメージに入れ、
   `sslmode=verify-full` にできる
6. **気付く仕組みが無い。** Lambda の 4xx・5xx の増え方、Cognito のログインの失敗、CloudTrail の root の使用に、CloudWatch のアラームを付ける
