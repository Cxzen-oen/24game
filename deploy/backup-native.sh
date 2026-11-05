#!/usr/bin/env bash
# 24game 原生部署备份：pg_dump -Fc，保留 14 天
set -euo pipefail
cd /tmp
DIR=/opt/game24/backups
mkdir -p "$DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$DIR/game24-$STAMP.dump"
runuser -u postgres -- pg_dump -Fc game24 > "$TARGET.part"
mv "$TARGET.part" "$TARGET"
gzip -f "$TARGET"
find "$DIR" -name 'game24-*.dump.gz' -mtime +14 -delete
echo "[$(date -u +%FT%TZ)] backup done: $TARGET.gz ($(du -h "$TARGET.gz" | cut -f1))"
