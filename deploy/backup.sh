#!/usr/bin/env bash
# PostgreSQL 逻辑备份：每天凌晨 3 点由 cron 调用
# 0 3 * * * /opt/game24/deploy/backup.sh >> /var/log/game24-backup.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
source .env.prod
set +a

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DIR="backups"
mkdir -p "$DIR"
TARGET="$DIR/game24-$STAMP.dump"

# 先写临时文件，成功后改名，避免中断留下半个备份
docker compose --env-file .env.prod -f compose.prod.yaml exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$TARGET.part"
mv "$TARGET.part" "$TARGET"
gzip -f "$TARGET"

# 保留 14 天；需要异地容灾时取消注释并配置 rclone
find "$DIR" -name 'game24-*.dump.gz' -mtime +14 -delete
# rclone copy "$DIR" oss:game24-backup/ --include '*.dump.gz'

echo "[$(date -u +%FT%TZ)] backup done: $TARGET.gz ($(du -h "$TARGET.gz" | cut -f1))"
