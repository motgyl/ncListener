#!/bin/bash
# Quick deployment script for serv_mess server

set -e

echo "========================================="
echo "  Serv Mess Server - Deployment Script"
echo "========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Configuration
INSTALL_PATH="/opt/serv_mess"
SERVICE_USER="memo"
SERVICE_NAME="serv_mess"

echo "[*] Installing Serv Mess Server..."
echo ""

# Step 1: Create user
echo "[1/6] Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/false "$SERVICE_USER"
    echo "      User '$SERVICE_USER' created"
else
    echo "      User '$SERVICE_USER' already exists"
fi

# Step 2: Create directories
echo "[2/6] Creating directories..."
mkdir -p "$INSTALL_PATH"
mkdir -p "$INSTALL_PATH/logs"
mkdir -p "$INSTALL_PATH/shared_files"
echo "      Directories created"

# Step 3: Copy files
echo "[3/6] Copying application files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp "$SCRIPT_DIR"/server.py "$INSTALL_PATH/"
cp "$SCRIPT_DIR"/client.py "$INSTALL_PATH/"
cp "$SCRIPT_DIR"/README.md "$INSTALL_PATH/"
echo "      Files copied"

# Step 4: Set permissions
echo "[4/6] Setting permissions..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_PATH"
chmod 755 "$INSTALL_PATH"
chmod 755 "$INSTALL_PATH/server.py"
chmod 755 "$INSTALL_PATH/client.py"
echo "      Permissions set"

# Step 5: Install systemd service
echo "[5/6] Installing systemd service..."
if [ -f "$SCRIPT_DIR/serv_mess.service" ]; then
    cp "$SCRIPT_DIR/serv_mess.service" /etc/systemd/system/
    systemctl daemon-reload
    echo "      Systemd service installed"
else
    echo "      WARNING: serv_mess.service not found, skipping"
fi

# Step 6: Start service
echo "[6/6] Starting service..."
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"
echo "      Service started"

echo ""
echo "========================================="
echo "  Installation Complete!"
echo "========================================="
echo ""
echo "Server installed at: $INSTALL_PATH"
echo "Service name: $SERVICE_NAME"
echo "Service user: $SERVICE_USER"
echo ""
echo "Useful commands:"
echo "  View status:   systemctl status $SERVICE_NAME"
echo "  View logs:     tail -f $INSTALL_PATH/logs/server.log"
echo "  Stop service:  systemctl stop $SERVICE_NAME"
echo "  Restart:       systemctl restart $SERVICE_NAME"
echo ""
echo "Test connection:"
echo "  nc localhost 7002"
echo ""
