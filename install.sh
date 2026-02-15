#!/usr/bin/env bash
set -euo pipefail

APP_NAME="lowkey-backup"
APP_DIR="/opt/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
UNIT_FILE="/etc/systemd/system/${APP_NAME}.service"

apt-get update -y
apt-get install -y rsync openssh-client python3 python3-venv python3-pip sshpass

mkdir -p "${APP_DIR}" "${DATA_DIR}" "${LOG_DIR}"
chmod 755 "${LOG_DIR}"

rsync -a --delete --exclude ".venv" --exclude "__pycache__" --exclude "*.pyc" "./" "${APP_DIR}/"

python3 -m venv "${APP_DIR}/venv"
"${APP_DIR}/venv/bin/pip" install --upgrade pip
"${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

cat > "${UNIT_FILE}" <<EOF
[Unit]
Description=Low-Key Backup (FastAPI)
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
Environment=LOWKEY_DATA_DIR=${DATA_DIR}
Environment=LOWKEY_LOG_DIR=${LOG_DIR}
ExecStart=${APP_DIR}/venv/bin/uvicorn lowkey_backup.main:app --host 0.0.0.0 --port 8585
Restart=on-failure
RestartSec=2
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${APP_NAME}"
systemctl restart "${APP_NAME}"

echo "OK: http://localhost:8585"
