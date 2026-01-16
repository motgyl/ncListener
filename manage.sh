#!/bin/bash
# Service management helper for serv_mess

SERVICE_NAME="serv_mess"
LOG_FILE="/opt/serv_mess/logs/server.log"

print_usage() {
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  start      - Start the service"
    echo "  stop       - Stop the service"
    echo "  restart    - Restart the service"
    echo "  status     - Show service status"
    echo "  logs       - Show last 50 lines of logs"
    echo "  logs -f    - Follow logs in real-time"
    echo "  enable     - Enable auto-start on boot"
    echo "  disable    - Disable auto-start"
    echo "  info       - Show system info"
}

case "$1" in
    start)
        echo "Starting $SERVICE_NAME..."
        sudo systemctl start "$SERVICE_NAME"
        sleep 1
        sudo systemctl status "$SERVICE_NAME"
        ;;
    
    stop)
        echo "Stopping $SERVICE_NAME..."
        sudo systemctl stop "$SERVICE_NAME"
        sleep 1
        echo "Service stopped"
        ;;
    
    restart)
        echo "Restarting $SERVICE_NAME..."
        sudo systemctl restart "$SERVICE_NAME"
        sleep 1
        sudo systemctl status "$SERVICE_NAME"
        ;;
    
    status)
        sudo systemctl status "$SERVICE_NAME"
        ;;
    
    logs)
        if [ "$2" = "-f" ]; then
            echo "Following logs (Ctrl+C to stop)..."
            sudo tail -f "$LOG_FILE"
        else
            echo "=== Last 50 lines of logs ==="
            sudo tail -50 "$LOG_FILE"
        fi
        ;;
    
    enable)
        echo "Enabling auto-start..."
        sudo systemctl enable "$SERVICE_NAME"
        echo "Service will auto-start on boot"
        ;;
    
    disable)
        echo "Disabling auto-start..."
        sudo systemctl disable "$SERVICE_NAME"
        echo "Service will not auto-start"
        ;;
    
    info)
        echo "=== System Information ==="
        echo "Service: $SERVICE_NAME"
        echo "Log file: $LOG_FILE"
        echo ""
        echo "=== Service Status ==="
        sudo systemctl status "$SERVICE_NAME" --no-pager | head -10
        echo ""
        echo "=== Port Status ==="
        sudo netstat -tlnp 2>/dev/null | grep 7002 || echo "Port 7002 not listening"
        echo ""
        echo "=== Log File Size ==="
        sudo du -h "$LOG_FILE"
        echo ""
        echo "=== Recent Activity ==="
        sudo tail -5 "$LOG_FILE"
        ;;
    
    *)
        print_usage
        exit 1
        ;;
esac
