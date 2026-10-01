-- アプリ(Lambda の API)が使う db のロール diary_app。行の読み書き(DML)だけを許し、表を作る・変える権限(DDL)は与えない。
-- パスワードは持たせず、IAM データベース認証(rds_iam)で繋ぐ。何度流しても同じ結果になる。
-- マスター(表の持ち主。マイグレーションもマスターで流す)で、db diary に繋いで、リポジトリのルートから:
--   .venv/bin/python -m tool.aws.rds -- psql -v ON_ERROR_STOP=1 -f infra/sql/diary_app.sql

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'diary_app') THEN
    CREATE ROLE diary_app LOGIN;
  END IF;
END
$$;
ALTER ROLE diary_app LOGIN NOCREATEDB NOCREATEROLE PASSWORD NULL;
GRANT rds_iam TO diary_app;

GRANT CONNECT ON DATABASE :"DBNAME" TO diary_app;
GRANT USAGE ON SCHEMA public TO diary_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO diary_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO diary_app;

-- これからマイグレーションで増える表・連番にも同じ権限が付くようにする
ALTER DEFAULT PRIVILEGES FOR ROLE :"USER" IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO diary_app;
ALTER DEFAULT PRIVILEGES FOR ROLE :"USER" IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO diary_app;
