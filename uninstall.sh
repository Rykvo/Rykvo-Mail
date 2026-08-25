#!/usr/bin/env bash
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "请使用 root 用户运行"; exit 1; }
BASE="$(cd "$(dirname "$0")" && pwd)"

if [ "${1:-}" != "--yes" ]; then
  echo "此操作将永久删除 Rykvo 邮局、全部域名、邮箱用户和邮件数据。"
  read -r -p "输入 DELETE 确认卸载：" answer
  [ "$answer" = "DELETE" ] || { echo "已取消"; exit 1; }
fi

systemctl disable --now \
  mailpanel.service mailpanel-cert.path mailpanel-cert.service \
  mailpanel-stalwart-reload.path mailpanel-stalwart-reload.service \
  stalwart.service 2>/dev/null || true

rm -f \
  /etc/systemd/system/mailpanel.service \
  /etc/systemd/system/mailpanel-cert.path \
  /etc/systemd/system/mailpanel-cert.service \
  /etc/systemd/system/mailpanel-stalwart-reload.path \
  /etc/systemd/system/mailpanel-stalwart-reload.service \
  /etc/systemd/system/stalwart.service
systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true

rm -rf /opt/mailpanel /var/lib/mailpanel /etc/mailpanel.env
rm -rf /opt/stalwart /var/lib/stalwart /etc/stalwart
rm -f /usr/local/bin/stalwart /usr/bin/stalwart

rm -f \
  /usr/local/sbin/mailpanel-cert-helper \
  /etc/nginx/sites-enabled/mailpanel \
  /etc/nginx/sites-available/mailpanel \
  /etc/nginx/stream-conf.d/mailpanel.conf \
  /etc/nginx/conf.d/mailpanel-https.conf \
  /etc/letsencrypt/renewal-hooks/deploy/reload-mailpanel-nginx
rm -rf /usr/local/lib/mailpanel /etc/nginx/mailpanel-certs /var/www/mailpanel-acme
rm -rf /etc/letsencrypt /var/lib/letsencrypt /var/log/letsencrypt

if grep -q '^# MAILPANEL_STREAM$' /etc/nginx/nginx.conf 2>/dev/null; then
  sed -i '/^# MAILPANEL_STREAM$/,/^}$/d' /etc/nginx/nginx.conf
fi
if [ -f /etc/nginx/sites-available/default ]; then
  ln -sfn /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
fi
nginx -t >/dev/null 2>&1 && systemctl reload nginx 2>/dev/null || true

if command -v ufw >/dev/null 2>&1; then
  for port in 25 80 443 110 143 465 587 993 995 4190; do
    ufw --force delete allow "$port/tcp" >/dev/null 2>&1 || true
  done
fi

apt-get purge -y nginx nginx-common nginx-core certbot libnginx-mod-stream >/dev/null 2>&1 || true
apt-get autoremove -y >/dev/null 2>&1 || true
rm -rf /etc/nginx /var/lib/nginx /var/log/nginx /usr/share/nginx

getent passwd stalwart >/dev/null && userdel stalwart 2>/dev/null || true
getent group stalwart >/dev/null && groupdel stalwart 2>/dev/null || true

echo "Rykvo 邮局已卸载，邮箱和邮件数据已删除。"
echo "邮件服务、管理面板、Nginx、Certbot 和 Let's Encrypt 证书均已删除。"
cd /root
rm -rf "$BASE"
