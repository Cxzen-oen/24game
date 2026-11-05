#!/usr/bin/env bash
# 在服务器仓库目录执行：./deploy/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env.prod ]; then
  echo "缺少 .env.prod，请先复制 .env.prod.example 并填写" >&2
  exit 1
fi

# 2C2G 模式使用预构建 jar，缺文件时直接报错，避免在服务器上跑 Maven/Node
if grep -q "Dockerfile.runtime" .env.prod 2>/dev/null && [ ! -f deploy/build/game24-demo.jar ]; then
  echo "缺少 deploy/build/game24-demo.jar：请先在本地执行 deploy/build-local.ps1 后上传" >&2
  exit 1
fi

# 升级前先备份（数据库容器未启动则跳过）
if docker compose --env-file .env.prod -f compose.prod.yaml ps db 2>/dev/null | grep -q "Up"; then
  ./deploy/backup.sh
fi

docker compose --env-file .env.prod -f compose.prod.yaml up -d --build
docker compose --env-file .env.prod -f compose.prod.yaml ps
