import { execFileSync } from "node:child_process";

// 構築ごとの設定。アカウント・リソースの ID はここに書かず、構築するアカウントの
// SSM パラメータ /diary/deploy/config に JSON で置く(形は infra/aws.example.json)。使い回す既存のリソースの ID が無ければ、
// スタックがそのリソースを作る。ai-novel-core の RDS・踏み台を使い回すなら、その ID を existing に書く(.docs/aws-deploy.md)
export interface DeployConfig {
  // subClaimPrefix は GitHub の OIDC の sub の前半。immutable subject を使うリポジトリは sub が `repo:<owner>@<ID>/<repo>@<ID>` で始まるので、
  // `gh api repos/<owner>/<repo>/actions/oidc/customization/sub` の sub_claim_prefix を置く。無ければ `repo:<repository>`
  github: { repository: string; branch: string; subClaimPrefix?: string };
  existing: {
    vpcId?: string;
    dbInstanceIdentifier?: string;
    bastion?: { instanceId: string; instanceConnectEndpointId: string };
    functionSubnetIds?: string[];
    githubOidcProviderArn?: string;
  };
}

export const parameterPrefix = "/diary";
const deployConfigParameter = `${parameterPrefix}/deploy/config`;

export function loadDeployConfig(): DeployConfig {
  let raw: string;
  try {
    raw = execFileSync("aws", [
      "ssm", "get-parameter", "--name", deployConfigParameter, "--query", "Parameter.Value", "--output", "text",
    ], { encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] });
  } catch {
    throw new Error(`SSM の ${deployConfigParameter} が読めない。infra/aws.example.json を埋めて置く: `
      + `aws ssm put-parameter --name ${deployConfigParameter} --type String --value file://aws.json`);
  }
  const config = JSON.parse(raw) as DeployConfig;
  if (!config.github?.repository || !config.github?.branch) {
    throw new Error(`${deployConfigParameter} に github.repository と github.branch が要る`);
  }
  config.existing ??= {};
  return config;
}

export interface ExistingDb {
  vpcId: string;
  endpoint: string;
  port: number;
  securityGroupId: string;
  resourceId: string;
  masterSecretArn: string;
}

// CDK には RDS のインスタンスを引く仕組みが無いので、synth のときに AWS CLI で引く
export function describeDbInstance(instanceIdentifier: string): ExistingDb {
  const [instance] = JSON.parse(execFileSync("aws", [
    "rds", "describe-db-instances", "--db-instance-identifier", instanceIdentifier,
    "--query", "DBInstances", "--output", "json",
  ], { encoding: "utf-8" }));
  if (!instance.MasterUserSecret?.SecretArn) {
    throw new Error(`${instanceIdentifier} のマスターのパスワードを RDS の管理(--manage-master-user-password)にしてから使う`);
  }
  // 暗号化は作ったあとに切り替えられない(暗号化したスナップショットから建て直す)ので、止めずに知らせるだけにする
  if (!instance.StorageEncrypted) {
    console.warn(`${instanceIdentifier} のストレージが暗号化されていない(.docs/security.md の「残っている課題」)`);
  }
  return {
    vpcId: instance.DBSubnetGroup.VpcId,
    endpoint: instance.Endpoint.Address,
    port: instance.Endpoint.Port,
    securityGroupId: instance.VpcSecurityGroups[0].VpcSecurityGroupId,
    resourceId: instance.DbiResourceId,
    masterSecretArn: instance.MasterUserSecret.SecretArn,
  };
}

// API のイメージは CI(.github/workflows/deploy-api.yml)が <sha> と main の tag で push する。CDK は main を指すだけで建てない
export const api = {
  functionName: "diary-api",
  repositoryName: "diary-api",
  imageTag: "main",
};

// 同じ RDS のインスタンスを ai-novel-core と使い回しても混ざらないよう、db を分ける
export const databaseName = "diary";
// アプリが使う db のロール。行の読み書きだけを許す(infra/sql/diary_app.sql)
export const appDatabaseUser = "diary_app";
