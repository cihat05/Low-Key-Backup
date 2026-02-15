#!/usr/bin/env bash
set -euo pipefail

APP_NAME="lowkey-backup"
APP_DIR="/opt/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
UNIT_FILE="/etc/systemd/system/${APP_NAME}.service"

echo "Stopping service..."
systemctl stop "${APP_NAME}" 2>/dev/null || true
systemctl disable "${APP_NAME}" 2>/dev/null || true

echo "Removing systemd unit..."
rm -f "${UNIT_FILE}"
systemctl daemon-reload

echo "Removing application directory..."
rm -rf "${APP_DIR}"

echo "Removing logs..."
rm -rf "${LOG_DIR}"

echo ""
read -p "Delete database and job configuration in ${DATA_DIR}? (y/N): " CONFIRM

if [[ "${CONFIRM}" =~ ^[Yy]$ ]]; then
    echo "Removing data directory..."
    rm -rf "${DATA_DIR}"
    echo "All data removed."
else
    echo "Data directory kept at: ${DATA_DIR}"
fi

echo ""
echo "Uninstall complete."
