import { CfnOutput, Duration, RemovalPolicy, Stack, type StackProps } from "aws-cdk-lib";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as iam from "aws-cdk-lib/aws-iam";
import type { Construct } from "constructs";
import { grantInvokeViaFunctionUrl } from "./api-stack.js";
import { api, type DeployConfig } from "./config.js";

// API のイメージの置き場と、GitHub Actions が引き受けるロール。ロールは main の push だけが引き受けられ、
// できることは diary-api の ECR への push(と、push や関数の差し替えに要るイメージの読み取り)と、diary-api 関数のコードの差し替え、
// 差し替えたあとの確かめに関数 URL を呼ぶことだけにする(cdk deploy はさせない)
interface DiaryCiStackProps extends StackProps {
  github: DeployConfig["github"];
  existing: DeployConfig["existing"];
}

export class DiaryCiStack extends Stack {
  constructor(scope: Construct, id: string, props: DiaryCiStackProps) {
    super(scope, id, props);
    const { github, existing } = props;
    const subClaimPrefix = github.subClaimPrefix ?? `repo:${github.repository}`;

    const repository = new ecr.Repository(this, "ApiRepository", {
      repositoryName: api.repositoryName,
      removalPolicy: RemovalPolicy.RETAIN,
      lifecycleRules: [
        { description: "tag の無いイメージは 1 日で消す", tagStatus: ecr.TagStatus.UNTAGGED, maxImageAge: Duration.days(1) },
        { description: "新しい 30 個を残す", maxImageCount: 30 },
      ],
    });

    // GitHub の OIDC プロバイダはアカウントに一つしか置けないので、既にあれば(ai-novel-core の NovelCi が作ったものなど)それを使う
    const providerArn = existing.githubOidcProviderArn
      ?? new iam.OidcProviderNative(this, "GitHubOidc", {
        url: "https://token.actions.githubusercontent.com",
        clientIds: ["sts.amazonaws.com"],
      }).oidcProviderArn;
    const deployRole = new iam.Role(this, "GitHubDeployRole", {
      roleName: "github-all-diary-deploy",
      assumedBy: new iam.WebIdentityPrincipal(providerArn, {
        StringEquals: {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": `${subClaimPrefix}:ref:refs/heads/${github.branch}`,
        },
      }),
    });
    // buildx の push は既にある目録を読み(BatchGetImage)、関数の差し替えもイメージを読むので、push だけでは足りない
    repository.grantPullPush(deployRole);
    deployRole.addToPolicy(new iam.PolicyStatement({
      actions: ["lambda:UpdateFunctionCode", "lambda:GetFunction", "lambda:GetFunctionConfiguration"],
      resources: [`arn:aws:lambda:${this.region}:${this.account}:function:${api.functionName}`],
    }));

    grantInvokeViaFunctionUrl(deployRole, `arn:aws:lambda:${this.region}:${this.account}:function:${api.functionName}`);

    new CfnOutput(this, "RepositoryUri", { value: repository.repositoryUri });
    new CfnOutput(this, "DeployRoleArn", { value: deployRole.roleArn });
  }
}
