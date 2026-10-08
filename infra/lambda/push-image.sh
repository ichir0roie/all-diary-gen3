#!/bin/bash
# API のイメージを手元で建て、ECR の diary-api に main の tag で push する。関数(DiaryApi)を初めて作る前に一度だけ使う。
# 以降は GitHub Actions(.github/workflows/deploy-api.yml)が push する。リポジトリのルートから: infra/lambda/push-image.sh
# x86 の機械では arm64 を建てられるビルダーが要る。Docker Desktop なら desktop-linux を使う(BUILDER で替えられる)
set -euo pipefail

region=$(aws configure get region || echo "${AWS_REGION:?AWS のリージョンが決まらない}")
registry=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$region.amazonaws.com
builder=${BUILDER:-}
if [ -z "$builder" ] && docker buildx inspect desktop-linux >/dev/null 2>&1; then
  builder=desktop-linux
fi

aws ecr get-login-password --region "$region" | docker login --username AWS --password-stdin "$registry" >&2
docker buildx build ${builder:+--builder "$builder"} --platform linux/arm64 --provenance=false \
  -f infra/lambda/Dockerfile -t "$registry/diary-api:main" --push .
