#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
[ "$(id -u)" -eq 0 ] || { echo "请使用 root 用户运行"; exit 1; }
BASE="$(cd "$(dirname "$0")" && pwd)"
apt-get update -qq
apt-get install -y -qq curl ca-certificates nginx certbot libnginx-mod-stream openssl python3 >/dev/null
if ! command -v stalwart >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -sSf https://get.stalw.art/install.sh -o /tmp/stalwart-install.sh
  sh /tmp/stalwart-install.sh
fi
mkdir -p /etc/stalwart
ENV_FILE=/etc/stalwart/stalwart.env
RECOVERY_PASSWORD="$(openssl rand -hex 24)"
touch "$ENV_FILE"
sed -i '/^STALWART_RECOVERY_ADMIN=/d' "$ENV_FILE"
echo "STALWART_RECOVERY_ADMIN=admin:$RECOVERY_PASSWORD" >>"$ENV_FILE"
chmod 640 "$ENV_FILE"
chown root:stalwart "$ENV_FILE" 2>/dev/null || true
systemctl enable --now stalwart
systemctl restart stalwart
sleep 4
STALWART_API_USER=admin
STALWART_API_PASSWORD=admin123
if [ -f /etc/mailpanel.env ]; then
  # 更新安装时沿用已经生成的 Stalwart 永久管理员凭据。
  . /etc/mailpanel.env
  STALWART_API_USER="${STALWART_USER:-admin}"
  STALWART_API_PASSWORD="${STALWART_PASSWORD:-admin123}"
fi
if [ ! -f /etc/stalwart/config.json ]; then
STALWART_RECOVERY_PASSWORD="$RECOVERY_PASSWORD" python3 <<'PY' >/tmp/stalwart-bootstrap-result
import urllib.request,json,base64,os
auth=base64.b64encode(("admin:"+os.environ["STALWART_RECOVERY_PASSWORD"]).encode()).decode()
headers={"Content-Type":"application/json","Authorization":"Basic "+auth}
url="http://127.0.0.1:8080/jmap"
def api(calls):
 req=urllib.request.Request(url,data=json.dumps({"using":["urn:ietf:params:jmap:core","urn:stalwart:jmap"],"methodCalls":calls}).encode(),headers=headers)
 return json.loads(urllib.request.urlopen(req,timeout=60).read())
r=api([["x:Bootstrap/get",{"ids":["singleton"]},"g"]])
obj=r["methodResponses"][0][1]["list"][0];obj.pop("id",None)
obj.update(serverHostname="mail.mailpanel-placeholder.example.com",defaultDomain="mailpanel-placeholder.example.com",requestTlsCertificate=False,generateDkimKeys=True)
r=api([["x:Bootstrap/set",{"update":{"singleton":obj}},"s"]])
u=r["methodResponses"][0][1]["updated"]["singleton"]
print(u["username"]);print(u["secret"])
PY
 STALWART_API_USER="$(sed -n '1p' /tmp/stalwart-bootstrap-result)"
 STALWART_API_PASSWORD="$(sed -n '2p' /tmp/stalwart-bootstrap-result)"
 sleep 8
fi
sed -i '/^STALWART_RECOVERY_ADMIN=/d' "$ENV_FILE"
systemctl restart stalwart
sleep 5
install -d -o www-data -g www-data -m 750 /opt/mailpanel /var/lib/mailpanel
install -o www-data -g www-data -m 750 "$BASE/app.py" /opt/mailpanel/app.py
PANEL_USER="${MAILPANEL_USER:-admin}"
PANEL_PASSWORD="${MAILPANEL_PASSWORD:-admin123}"
SECRET="${MAILPANEL_SECRET:-$(openssl rand -hex 32)}"
PUBLIC_IP="$(curl -4fsS --max-time 8 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')"
cat >/etc/mailpanel.env <<EOF
MAILPANEL_USER=$PANEL_USER
MAILPANEL_PASSWORD=$PANEL_PASSWORD
MAILPANEL_SECRET=$SECRET
MAILPANEL_PUBLIC_IP=$PUBLIC_IP
STALWART_USER=$STALWART_API_USER
STALWART_PASSWORD=$STALWART_API_PASSWORD
EOF
chmod 600 /etc/mailpanel.env
cat >/etc/systemd/system/mailpanel.service <<'EOF'
[Unit]
Description=Rykvo Mail Management Panel
After=network.target stalwart.service
Requires=stalwart.service
[Service]
Type=simple
User=www-data
Group=www-data
EnvironmentFile=/etc/mailpanel.env
ExecStart=/usr/bin/python3 /opt/mailpanel/app.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/mailpanel
[Install]
WantedBy=multi-user.target
EOF
touch /var/lib/mailpanel/reload-stalwart
chown www-data:www-data /var/lib/mailpanel/reload-stalwart
cat >/etc/systemd/system/mailpanel-stalwart-reload.path <<'EOF'
[Unit]
Description=Watch Rykvo sender-name updates
[Path]
PathChanged=/var/lib/mailpanel/reload-stalwart
[Install]
WantedBy=multi-user.target
EOF
cat >/etc/systemd/system/mailpanel-stalwart-reload.service <<'EOF'
[Unit]
Description=Reload Stalwart sender-name rules
[Service]
Type=oneshot
ExecStart=/usr/bin/systemctl restart stalwart.service
EOF
cat >/etc/nginx/sites-available/mailpanel <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    client_max_body_size 2m;
    location ^~ /.well-known/acme-challenge/ { root /var/www/mailpanel-acme; }
    location / {
        proxy_pass http://127.0.0.1:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/mailpanel /etc/nginx/sites-enabled/mailpanel
bash "$BASE/install_cert_helper.sh"
systemctl daemon-reload
systemctl enable --now nginx mailpanel-stalwart-reload.path
systemctl enable --now mailpanel
systemctl restart mailpanel nginx
if command -v ufw >/dev/null 2>&1; then
  for port in 22 25 80 443 110 143 465 587 993 995 4190; do ufw allow "$port/tcp" >/dev/null 2>&1 || true; done
fi
rm -f /tmp/stalwart-install.sh /tmp/mailpanel-certbot.log /tmp/stalwart-bootstrap-result
sleep 2
curl -fsS http://127.0.0.1/health >/dev/null
printf '\n%s\n' 'Rykvo 邮局安装完成' "后台：http://$PUBLIC_IP/gly" "账号：$PANEL_USER" "密码：$PANEL_PASSWORD" '登录后请立即在“系统设置”修改管理员账号和密码。'
