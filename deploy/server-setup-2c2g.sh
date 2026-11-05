#!/usr/bin/env bash
# 在 2C2G Ubuntu 服务器上初始化 24game：PostgreSQL 调优 + 建库建用户 + /opt/game24 环境文件
# 用法（root）：bash server-setup-2c2g.sh
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "请用 root 运行" >&2
  exit 1
fi

APP_DIR=/opt/game24
DB_NAME=game24
DB_USER=game24

# 1) PostgreSQL：2G 内存下的保守参数
CONF=/etc/postgresql/14/main/postgresql.conf
if ! grep -q "game24 tuning" "$CONF"; then
  cat >> "$CONF" <<'EOF'

# game24 tuning (2C2G)
shared_buffers = 96MB
max_connections = 30
work_mem = 4MB
maintenance_work_mem = 64MB
effective_cache_size = 512MB
EOF
fi
systemctl enable postgresql
systemctl restart postgresql

# 2) 建库建用户（幂等；每次重设密码并写回 env）
DBPASS="$(openssl rand -hex 24)"
runuser -u postgres -- psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
    CREATE ROLE $DB_USER LOGIN PASSWORD '$DBPASS';
  ELSE
    ALTER ROLE $DB_USER WITH PASSWORD '$DBPASS';
  END IF;
END
\$\$;
SQL
if ! runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
  runuser -u postgres -- createdb -O "$DB_USER" "$DB_NAME"
fi

# 3) 运行用户与目录
if ! id game24 >/dev/null 2>&1; then
  useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin game24
fi
mkdir -p "$APP_DIR"
chown -R game24:game24 "$APP_DIR"

# 4) 应用环境变量：JWT 已有则保留，避免每次部署让所有人掉线
JWT_SECRET=""
if [ -f "$APP_DIR/game24.env" ]; then
  JWT_SECRET="$(grep '^JWT_SECRET=' "$APP_DIR/game24.env" | cut -d= -f2- || true)"
fi
if [ -z "$JWT_SECRET" ]; then
  JWT_SECRET="$(openssl rand -hex 32)"
fi

cat > "$APP_DIR/game24.env" <<EOF
DB_URL=jdbc:postgresql://127.0.0.1:5432/$DB_NAME
DB_USERNAME=$DB_USER
DB_PASSWORD=$DBPASS
DB_POOL_SIZE=6
JWT_SECRET=$JWT_SECRET
COOKIE_SECURE=false
FORWARD_HEADERS_STRATEGY=none
SERVER_PORT=8081
TOMCAT_MAX_THREADS=40
EOF
chown game24:game24 "$APP_DIR/game24.env"
chmod 600 "$APP_DIR/game24.env"

echo "server setup done: db=$DB_NAME user=$DB_USER app=$APP_DIR port=8081"
