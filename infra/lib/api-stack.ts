import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { CfnOutput, Duration, RemovalPolicy, Stack, type StackProps } from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as logs from "aws-cdk-lib/aws-logs";
import * as ssm from "aws-cdk-lib/aws-ssm";
import type { Construct } from "constructs";
import { api, appDatabaseUser, databaseName, parameterPrefix } from "./config.js";
import type { DiaryData } from "./data-stack.js";

interface DiaryApiStackProps extends StackProps {
  data: DiaryData;
  // 置く private subnet。省けば VPC の isolated subnet 全部
  functionSubnetIds?: string[];
}

// API(gui/api)の Lambda を VPC の中に置く。NAT も Secrets Manager・SSM の VPC エンドポイントも置かず、
// db へは IAM データベース認証のトークン(Lambda の中で署名する)で繋ぐ
export class DiaryApiStack extends Stack {
  constructor(scope: Construct, id: string, props: DiaryApiStackProps) {
    super(scope, id, props);
    const { vpc, db } = props.data;

    const functionSecurityGroup = new ec2.SecurityGroup(this, "FunctionSecurityGroup", {
      vpc,
      description: "diary-api Lambda",
      allowAllOutbound: true,
    });
    const dbSecurityGroup = ec2.SecurityGroup.fromSecurityGroupId(this, "DbSecurityGroup", db.securityGroupId, {
      mutable: true,
    });
    dbSecurityGroup.addIngressRule(functionSecurityGroup, ec2.Port.tcp(db.port), "diary-api Lambda");

    const functionRole = new iam.Role(this, "FunctionRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [iam.ManagedPolicy.fromAwsManagedPolicyName("service-role/AWSLambdaVPCAccessExecutionRole")],
    });
    functionRole.addToPolicy(new iam.PolicyStatement({
      actions: ["rds-db:connect"],
      resources: [
        `arn:aws:rds-db:${this.region}:${this.account}:dbuser:${db.resourceId}/${appDatabaseUser}`,
      ],
    }));

    // Lambda が自動で作る /aws/lambda/diary-api は保存期間が無期限で、CloudFormation の外にあるので、CDK が名前を振る方へ出す。
    // 保存の料金は溜まった量に掛かり続けるので、CloudWatch Logs の無料枠(月 5 GB)に収まるよう短く切る
    const logGroup = new logs.LogGroup(this, "FunctionLogGroup", {
      retention: logs.RetentionDays.TWO_WEEKS,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    const repository = ecr.Repository.fromRepositoryName(this, "ApiRepository", api.repositoryName);
    // CI が差し替えたイメージは、template の ImageUri(repo:main)が変わらない限り cdk deploy で戻らない
    const fn = new lambda.DockerImageFunction(this, "Function", {
      functionName: api.functionName,
      code: lambda.DockerImageCode.fromEcr(repository, { tagOrDigest: api.imageTag }),
      architecture: lambda.Architecture.X86_64,
      memorySize: 1024,
      timeout: Duration.seconds(30),
      // 署名を持つ呼ぶ側が暴れても、費用と db の接続数がこれ以上に膨らまないようにする
      reservedConcurrentExecutions: 3,
      role: functionRole,
      logGroup,
      vpc,
      vpcSubnets: props.functionSubnetIds
        ? { subnets: props.functionSubnetIds.map((subnetId, i) => ec2.Subnet.fromSubnetId(this, `Subnet${i}`, subnetId)) }
        : { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      securityGroups: [functionSecurityGroup],
      environment: {
        DIARY_DATABASE_URL:
          `postgresql+psycopg://${appDatabaseUser}@${db.endpoint}:${db.port}/${databaseName}?sslmode=require`,
        DIARY_DATABASE_IAM_AUTH: "1",
        // 鍵の本体は template に載せず、SHA-256 だけを渡す(gui/api/app.py が届いた鍵のハッシュと比べる)
        DIARY_API_KEYS: `gui=sha256:${createHash("sha256").update(readApiKey("gui")).digest("hex")}`,
      },
    });
    // 署名の無い要求は関数が起きる前に Lambda が弾くので、URL を叩かれ続けても料金もログも生まれない。
    // 画面は Amplify の SSR のコンピュートロールで署名して呼ぶ
    const url = fn.addFunctionUrl({ authType: lambda.FunctionUrlAuthType.AWS_IAM });
    // Amplify のアプリは CDK の外にあるので、このロールは aws amplify update-app --compute-role-arn で付ける
    const amplifyComputeRole = new iam.Role(this, "AmplifyComputeRole", {
      assumedBy: new iam.ServicePrincipal("amplify.amazonaws.com"),
      description: "Amplify SSR (gui/web) calls diary-api function URL",
    });
    grantInvokeViaFunctionUrl(amplifyComputeRole, fn.functionArn);
    // 画面のサーバー(route handler)は合言葉を実行時に SSM から読む。Amplify の環境変数やビルドの成果物に鍵を写さないため。
    // SecureString は AWS 管理の鍵(aws/ssm)で暗号化してあり、その鍵のポリシーが同じアカウントの SSM 越しの復号を許すので、kms の権限は要らない
    amplifyComputeRole.addToPolicy(new iam.PolicyStatement({
      actions: ["ssm:GetParameter"],
      resources: [`arn:aws:ssm:${this.region}:${this.account}:parameter${apiKeyParameter("gui")}`],
    }));

    new ssm.StringParameter(this, "FunctionUrlParameter", {
      parameterName: `${parameterPrefix}/api/function-url`,
      stringValue: url.url,
    });
    new CfnOutput(this, "FunctionUrl", { value: url.url });
    new ssm.StringParameter(this, "AmplifyComputeRoleParameter", {
      parameterName: `${parameterPrefix}/amplify/compute-role-arn`,
      stringValue: amplifyComputeRole.roleArn,
    });
    new CfnOutput(this, "AmplifyComputeRoleArn", { value: amplifyComputeRole.roleArn });
  }
}

// 関数 URL を AWS_IAM で呼ぶには、InvokeFunctionUrl と(2025 年 10 月から)InvokeFunction の両方が要る。
// InvokeFunction は関数 URL 越しに限り、関数を直に invoke する道には使わせない
export function grantInvokeViaFunctionUrl(role: iam.Role, functionArn: string): void {
  role.addToPolicy(new iam.PolicyStatement({
    actions: ["lambda:InvokeFunctionUrl"],
    resources: [functionArn],
    conditions: { StringEquals: { "lambda:FunctionUrlAuthType": "AWS_IAM" } },
  }));
  role.addToPolicy(new iam.PolicyStatement({
    actions: ["lambda:InvokeFunction"],
    resources: [functionArn],
    conditions: { Bool: { "lambda:InvokedViaFunctionUrl": "true" } },
  }));
}

// 鍵の値は SSM の SecureString に置き、git には入れない。deploy のときに読み、ハッシュにして Lambda の環境変数に渡す
// (VPC の中の Lambda は、エンドポイント無しでは SSM を読めないため)
function apiKeyParameter(caller: "gui"): string {
  return `${parameterPrefix}/api-keys/${caller}`;
}

function readApiKey(caller: "gui"): string {
  return execFileSync("aws", [
    "ssm", "get-parameter", "--name", apiKeyParameter(caller), "--with-decryption",
    "--query", "Parameter.Value", "--output", "text",
  ], { encoding: "utf-8" }).trim();
}
