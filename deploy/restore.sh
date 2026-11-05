#!/usr/bin/env bash
# 用法：./deploy/restore.sh backups/game24-20260101T030000Z.dump.gz
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
source .env.prod
set +a

if [ "$#" -ne 1 ]; then
  echo "用法: $0 <备份文件.dump.gz>" >&2
  exit 1
fi

echo "即将用 $1 覆盖数据库 $POSTGRES_DB，10 秒内 Ctrl+C 取消..."
sleep 10
docker compose --env-file .env.prod -f compose.prod.yaml stop app
gunzip -c "$1" | docker compose --env-file .env.prod -f compose.prod.yaml exec -T db \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner
docker compose --env-file .env.prod -f compose.prod.yaml start app
echo "恢复完成，检查 /api/health"
