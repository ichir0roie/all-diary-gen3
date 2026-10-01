import { App, Tags } from "aws-cdk-lib";
import { DiaryApiStack } from "../lib/api-stack.js";
import { DiaryAuthStack } from "../lib/auth-stack.js";
import { DiaryCiStack } from "../lib/ci-stack.js";
import { loadDeployConfig } from "../lib/config.js";
import { DiaryDataStack } from "../lib/data-stack.js";

// アカウントとリージョンは、cdk を動かす人の AWS CLI のプロファイルから取る
const env = { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION };
const config = loadDeployConfig();

const app = new App();
Tags.of(app).add("project", "all-diary");

const dataStack = new DiaryDataStack(app, "DiaryData", { env, existing: config.existing });
// 関数は ECR に main の tag のイメージがある前提で作るので、DiaryCi を先に deploy して push してから DiaryApi を deploy する
new DiaryCiStack(app, "DiaryCi", { env, github: config.github, existing: config.existing });
new DiaryApiStack(app, "DiaryApi", { env, data: dataStack.data, functionSubnetIds: config.existing.functionSubnetIds });
new DiaryAuthStack(app, "DiaryAuth", { env });
