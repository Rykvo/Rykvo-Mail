# Rykvo 邮局

适用于 Ubuntu 22.04 / 24.04，请使用 root 用户安装。

## 一键安装

```bash
apt-get update && apt-get install -y git && cd /root && (test -d Rykvo-Mail/.git && git -C Rykvo-Mail pull --ff-only || git clone https://github.com/Rykvo/Rykvo-Mail.git) && bash /root/Rykvo-Mail/install.sh
```

后台：`http://服务器IP/gly`

- 账号：`admin`
- 密码：`admin123`

## 开放端口

`25, 80, 110, 143, 443, 465, 587, 993, 995, 4190`

## 更新

```bash
cd /root/Rykvo-Mail && git pull --ff-only && bash install.sh
```

## 完全卸载

```bash
cd /root/Rykvo-Mail && git pull --ff-only && bash uninstall.sh --yes
```
