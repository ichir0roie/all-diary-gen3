# AWS の db・資源と、API の形

AWS の db(RDS for PostgreSQL、db `diary`)と資源に触れる作業、API(Lambda)のコードを書く作業の決まり。
資源の構成と手順は `.docs/aws-deploy.md` にある。手元から db を読み書きする手順は `.claude/docs/db.md`。

## 公開リポジトリ

このリポジトリは公開で、誰がクローンしても、自分の AWS アカウントに自分用に建てて使える形でなければならない。

- コード・CDK・文書・テスト・コミットに、特定の構築の値を書かない。アカウント ID、リソースの ID(VPC・subnet・セキュリティグループ・
  インスタンス・EC2 Instance Connect Endpoint)、db のインスタンス名とエンドポイント、ARN、関数 URL、合言葉、Cognito のユーザープールの ID と
  ユーザーの sub、自分の GitHub のリポジトリ名。文書では `<アカウント ID>` のような置き場所の印を使う
- アカウントとリージョンは、`cdk` を動かす人の AWS CLI のプロファイルから取る(`CDK_DEFAULT_ACCOUNT` / `CDK_DEFAULT_REGION`)
- 構築ごとの設定(使い回す既存のリソースの ID、CI を許す GitHub のリポジトリなど)は、構築するアカウントの SSM パラメータ
  `/diary/deploy/config` に JSON で置き、`infra/` が synth のときに読む。どのリポジトリにも置かない。deploy のあとに決まる値(関数 URL など)も
  SSM の `/diary/*` に置き、使う側がそこから引く
- 既存のリソースの ID が設定に無ければ、`infra/` のスタックが自分で作る(NAT の無い VPC、小さな RDS、踏み台と EC2 Instance Connect Endpoint)
- CDK が手元に貯める `cdk.context.json` は、アカウントやリソースの ID を含むので git に入れない
- コミットする前に、差分を `grep -E '[0-9]{12}|vpc-|subnet-|sg-|i-0|eice-|arn:aws|rds\.amazonaws\.com|lambda-url|ap-northeast-1_'` などで見て、構築の値が紛れていないか確かめる

## 場所ごとの db への道

| 場所 | db への道 | db のロール | 持つ鍵 |
| --- | --- | --- | --- |
| 手元(CLI・VS Code) | 踏み台越しの転送(`tool.aws.rds --serve`、127.0.0.1:25432)。ふだんの読み書きは IAM データベース認証(`DIARY_DATABASE_IAM_AUTH=1`)。マイグレーションなど DDL が要る作業は `tool.aws.rds --` 越しにマスターで | `diary_app`(ふだん)/ マスター(DDL) | 手元の AWS CLI の権限(`rds-db:connect`・マスターの秘密の読み取り) |
| Lambda(`diary-api`) | VPC の中から psycopg で直に。IAM データベース認証(`DIARY_DATABASE_IAM_AUTH=1`) | `diary_app`(行の読み書きだけ) | 実行ロールの `rds-db:connect` |
| 画面(Amplify) | db には繋がない。route handler が Lambda の関数 URL を SigV4 の署名と合言葉で呼ぶ | 無し | Amplify の SSR のコンピュートロール(合言葉は実行時に SSM から読む) |

## 決まり

1. マイグレーション(`alembic upgrade`)を AWS の db に当てるのは、手元から `tool.aws.rds` 越しにだけ行う。
   Lambda・GitHub Actions からは当てない。当てるのはユーザに言われてからにし、前にマイグレーションの中身をユーザに見せる
2. API に、任意の SQL や、表を丸ごと消すような操作を受ける口を作らない。公開するのは `data_access_logic` の入口だけ
3. API は誰の行かを、画面の route handler が Cognito のトークンを確かめてから付ける `x-diary-user` で知る(`gui/api/user.py`)。
   ブラウザから来た `x-diary-user` は route handler が流さない。API の入口は必ず `user_id` で行を絞る
4. `diary_app` に表を作る・変える権限(DDL)を与えない。表の形を変えるのはマイグレーションだけで、マスターで流す。
   これから増える表への `diary_app` の権限は、マスターに掛けた既定の権限(`infra/sql/diary_app.sql`)で付くので、マイグレーションをマスター以外で流さない
5. AWS の資源は `infra/` の CDK で持つ。コンソールや CLI で直に作らない・変えない(状態を調べる読み取りはよい)。
   `cdk deploy` や資源を変える操作は、ユーザに承認を得てから行う。費用を抑えるため、NAT ゲートウェイや VPC のインターフェースエンドポイントを足さない
6. 関数 URL は SSM の `/diary/api/function-url`、合言葉は `/diary/api-keys/gui` から引く。合言葉の値はログや報告にも出さない。
   合言葉の本体は SSM にだけ置き、Lambda の環境変数・CloudFormation の template・Amplify の環境変数・ビルドの成果物に写さない(Lambda にはハッシュだけ)
