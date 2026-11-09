#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this configuration script as root." >&2
  exit 1
fi

install -m 0755 -d /etc/systemd/system/docker.service.d
printf '%s\n' \
  '[Service]' \
  'Environment="HTTP_PROXY=http://127.0.0.1:7897"' \
  'Environment="HTTPS_PROXY=http://127.0.0.1:7897"' \
  'Environment="NO_PROXY=localhost,127.0.0.1,::1"' \
  > /etc/systemd/system/docker.service.d/http-proxy.conf

systemctl daemon-reload
systemctl restart docker
systemctl show --property=Environment docker
