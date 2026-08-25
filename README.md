# Rykvo Mail（Rykvo 邮局）

Rykvo Mail 是一个中文邮件服务器管理面板，基于 Stalwart Mail Server，适合在 Ubuntu 云服务器上快速部署独立邮局。

## 功能

- 多邮局域名管理与 DNS 检测
- 邮箱用户创建、修改、删除、搜索和分页
- TXT 批量创建用户，显示实时进度
- 按域名筛选并导出邮箱账号和密码
- SMTP、POP3、IMAP 及其 SSL/TLS 端口
- 邮件域名和管理后台自动申请/续期 HTTPS 证书
- 邮件数据自动清理和手动清理
- 中文网页管理面板

## 系统要求

- Ubuntu 22.04 / 24.04
- root 权限
- 独立公网 IPv4
- 建议全新服务器
- 云防火墙放行 TCP：`25, 80, 110, 143, 443, 465, 587, 993, 995, 4190`

> Google Cloud 通常限制出站 TCP 25。若需向外发信，请向云厂商申请解封或配置 SMTP 中继。

## SSH 一键部署

使用 root 登录服务器后执行：

```bash
apt-get update && apt-get install -y git && cd /root && (test -d Rykvo-Mail/.git && git -C Rykvo-Mail pull --ff-only || git clone https://github.com/Rykvo/Rykvo-Mail.git) && bash /root/Rykvo-Mail/install.sh
```

安装程序会自动安装并配置 Stalwart、Nginx、Certbot 和 Rykvo Mail，并自动识别服务器公网 IP。

## 登录后台

安装完成后打开：

```text
http://服务器IP/gly
```

安装完成后，终端会显示登录信息：

```text
账号：admin
密码：安装时随机生成
```

首次登录后，请立即在“系统设置”中修改管理员账号和密码。

请同时在服务器商后台将 PTR/rDNS 设置为 `mail.你的域名`，以提高外部邮箱的投递成功率。

## 基本使用流程

1. 登录管理后台。
2. 在“邮局域名”添加邮件域名。
3. 根据面板显示的记录配置 DNS。
4. 点击“检测 DNS”。
5. 创建邮箱用户或通过 TXT 文件批量创建。
6. 在邮件客户端中使用 SMTP、POP3 或 IMAP 登录。

## 更新

```bash
cd /root/Rykvo-Mail && git pull --ff-only && bash install.sh
```

面板配置和邮件数据保存在服务器数据目录中，代码仓库不包含任何用户、域名、邮件或测试数据。
