#!/usr/bin/env bash
# Puts Lord Unga on a fresh Ubuntu box and keeps him there.
# Run it from inside the checked-out folder:  bash deploy/setup.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE=/etc/systemd/system/troglodyte.service

echo "==> packages"
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip git nano

echo "==> virtualenv"
cd "$APP_DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo "   .env created from the example. It has no token in it yet."
  echo "   Put the token in with:   nano $APP_DIR/.env"
  echo "   Then:                    sudo systemctl restart troglodyte"
  echo
fi

echo "==> service"
sudo tee "$SERVICE" >/dev/null <<UNIT
[Unit]
Description=Troglodyte OS (Lord Unga)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=PYTHONUNBUFFERED=1
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/troglodyte_os.py
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/troglodyte.log
StandardError=append:$APP_DIR/troglodyte.log

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable troglodyte >/dev/null
sudo systemctl restart troglodyte
sleep 4
sudo systemctl --no-pager --lines=20 status troglodyte || true

cat <<TIPS

Installed. It now starts on boot and restarts itself if it ever dies.

  tail -f $APP_DIR/troglodyte.log      watch it live
  sudo systemctl restart troglodyte     after changing the code or .env
  sudo systemctl stop troglodyte        take it offline
  cd $APP_DIR && git pull && sudo systemctl restart troglodyte    deploy an update

TIPS
