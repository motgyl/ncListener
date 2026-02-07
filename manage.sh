#!/bin/bash

SERVICE_NAME="serv_mess"
LOG_FILE="/opt/serv_mess/logs/server.log"
APP_DIR="/opt/serv_mess"
VENV_DIR="$APP_DIR/venv"

print_usage() {
    cat <<EOF
Usage: $0 <command>
Commands:
  start        - Start service (production: systemd)
  dev          - Run in development mode (python3 server.py)
  stop         - Stop systemd service
  restart      - Restart systemd service
  status       - Show service status
  logs         - Show logs (file or journal)
  logs -f      - Follow logs
  enable       - Enable auto-start on boot
  disable      - Disable auto-start
  update       - Pull latest code and reinstall deps
EOF
}

start() {
    echo "Starting service (systemd)..."
    sudo systemctl start "$SERVICE_NAME"
    sleep 1
    sudo systemctl status "$SERVICE_NAME"
}

dev() {
    echo "Running in development mode"
    cd "$APP_DIR" || exit
    if [ -d "$VENV_DIR" ]; then
        echo "Activating venv..."
        source "$VENV_DIR/bin/activate"
    fi
    echo "Starting server.py..."
    python3 server.py
}

stop() {
    echo "Stopping service..."
    sudo systemctl stop "$SERVICE_NAME"
}

restart() {
    echo "Restarting service..."
    sudo systemctl restart "$SERVICE_NAME"
    sleep 1
    sudo systemctl status "$SERVICE_NAME"
}

status() {
    sudo systemctl status "$SERVICE_NAME"
}

logs() {
    if [ "$2" = "-f" ]; then
        sudo journalctl -u "$SERVICE_NAME" -f
    else
        sudo journalctl -u "$SERVICE_NAME" --no-pager | tail -n 100
    fi
}

enable() {
    sudo systemctl enable "$SERVICE_NAME"
}

disable() {
    sudo systemctl disable "$SERVICE_NAME"
}

update() {
    echo "Updating code..."
    cd "$APP_DIR" || exit
    git pull
    if [ -f "requirements.txt" ]; then
        echo "Reinstalling dependencies..."
        if [ -d "$VENV_DIR" ]; then
            source "$VENV_DIR/bin/activate"
            pip install -r requirements.txt
        else
            pip install -r requirements.txt
        fi
    fi
    echo "Update finished!"
}

case "$1" in
    start|dev|stop|restart|status|logs|enable|disable|update)
        $1 "$2"
        ;;
    *)
        print_usage
        ;;
esac
