#!/usr/bin/env bash
# 用法：/opt/game24/restore-native.sh /opt/game24/backups/game24-xxx.dump.gz
set -euo pipefail
cd /tmp
if [ "$#" -ne 1 ]; then
  echo "用法: $0 <备份文件.dump.gz>" >&2
  exit 1
fi
echo "即将用 $1 覆盖 game24 数据库，10 秒内 Ctrl+C 取消..."
sleep 10
systemctl stop game24
gunzip -c "$1" | runuser -u postgres -- pg_restore -d game24 --clean --if-exists --no-owner
systemctl start game24
echo "恢复完成，检查 http://127.0.0.1:8081/api/health"
