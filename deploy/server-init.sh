#!/usr/bin/env bash
# 2C2G 云服务器初始化：2G swap + Docker + 常用安全组件
# 用法（root）：bash deploy/server-init.sh            不启用防火墙，只装 Docker/swap
#               bash deploy/server-init.sh --firewall 额外启用 ufw（会只放行 SSH/80/443）
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "请用 root 运行" >&2
  exit 1
fi

# 1) 2G swap：2G 机器构建/峰值时兜底，避免 OOM Killer 直接杀进程
if ! swapon --show | grep -q .; then
  echo "创建 2G swap..."
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo 'vm.swappiness=10' > /etc/sysctl.d/99-game24.conf
  sysctl -p /etc/sysctl.d/99-game24.conf
else
  echo "已有 swap，跳过"
fi

# 2) 基础软件与 Docker
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl ufw fail2ban unattended-upgrades
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker
systemctl enable --now fail2ban
systemctl enable --now unattended-upgrades || true

# 3) 防火墙默认不动：面板/宝塔可能占用其他端口，误开 ufw 会锁死自己
if [ "${1:-}" = "--firewall" ]; then
  SSH_PORT="${SSH_CONNECTION##* }"
  SSH_PORT="${SSH_PORT:-22}"
  ufw allow "${SSH_PORT}/tcp"
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
  echo "ufw 已启用：SSH ${SSH_PORT}, 80, 443"
else
  echo "未启用 ufw；需要时执行: bash deploy/server-init.sh --firewall"
fi

echo "完成：$(docker --version)"
swapon --show || true
free -m || true
