#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq certbot libnginx-mod-stream openssl >/dev/null
mkdir -p /var/www/mailpanel-acme /etc/nginx/stream-conf.d /etc/nginx/mailpanel-certs /usr/local/lib/mailpanel
if ! grep -q 'MAILPANEL_STREAM' /etc/nginx/nginx.conf; then
cat >>/etc/nginx/nginx.conf <<'EOF'

# MAILPANEL_STREAM
stream {
    include /etc/nginx/stream-conf.d/*.conf;
}
EOF
fi
cat >/usr/local/sbin/mailpanel-cert-helper <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
REQ=/var/lib/mailpanel/cert-request
RESULT=/var/lib/mailpanel/cert-result
DOMAIN="$(tr -d '\r\n' < "$REQ")"
if ! [[ "$DOMAIN" =~ ^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$ ]]; then echo '失败：后台域名格式错误' >"$RESULT"; exit 1; fi
echo '申请中，请稍后刷新' >"$RESULT"; chown www-data:www-data "$RESULT"
if ! certbot certonly --webroot -w /var/www/mailpanel-acme -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --keep-until-expiring >/tmp/mailpanel-certbot.log 2>&1; then echo '失败：请确认 A 记录已指向服务器并设为仅 DNS' >"$RESULT"; chown www-data:www-data "$RESULT"; exit 1; fi
cd /opt/mailpanel
python3 - <<'PY'
import app
o=app.call([["x:NetworkListener/query",{},"q"],["x:NetworkListener/get",{"#ids":{"resultOf":"q","name":"x:NetworkListener/query","path":"/ids"}},"g"]])
for x in app.resp(o,"x:NetworkListener/get").get("list",[]):
    if x.get("name")=="https" and "127.0.0.1:8443" not in x.get("bind",{}):
        app.call([["x:NetworkListener/set",{"update":{x["id"]:{"bind":{"127.0.0.1:8443":True}}}},"s"]])
PY
systemctl restart stalwart
cat >/etc/nginx/stream-conf.d/mailpanel.conf <<CFG
map \$ssl_preread_server_name \$mailpanel_backend {
    $DOMAIN 127.0.0.1:4443;
    default 127.0.0.1:8443;
}
server {
    listen 0.0.0.0:443;
    listen [::]:443;
    proxy_pass \$mailpanel_backend;
    ssl_preread on;
}
CFG
cat >/etc/nginx/conf.d/mailpanel-https.conf <<CFG
server {
    listen 127.0.0.1:4443 ssl;
    server_name $DOMAIN;
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:8090;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
CFG
nginx -t >/dev/null
systemctl reload nginx
echo "成功：https://$DOMAIN（自动续期）" >"$RESULT"; chown www-data:www-data "$RESULT"
EOF
chmod 0755 /usr/local/sbin/mailpanel-cert-helper
cat >/etc/systemd/system/mailpanel-cert.service <<'EOF'
[Unit]
Description=Mailpanel certificate issuer
After=network-online.target
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/mailpanel-cert-helper
EOF
cat >/etc/systemd/system/mailpanel-cert.path <<'EOF'
[Unit]
Description=Watch mailpanel certificate requests
[Path]
PathChanged=/var/lib/mailpanel/cert-request
Unit=mailpanel-cert.service
[Install]
WantedBy=multi-user.target
EOF
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat >/etc/letsencrypt/renewal-hooks/deploy/reload-mailpanel-nginx <<'EOF'
#!/bin/sh
systemctl reload nginx
EOF
chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/reload-mailpanel-nginx
# Ensure HTTP-01 challenges bypass the Python panel.
cat >/etc/nginx/sites-enabled/mailpanel <<'EOF'
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
systemctl daemon-reload
systemctl enable --now mailpanel-cert.path
nginx -t >/dev/null && systemctl reload nginx
