#!/bin/bash
# Quick log viewer for serv_mess server

LOG_FILE="/opt/serv_mess/logs/server.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "Log file not found: $LOG_FILE"
    exit 1
fi

if [ "$1" = "follow" ] || [ "$1" = "-f" ]; then
    echo "Following logs (Ctrl+C to stop)..."
    tail -f "$LOG_FILE"
    
elif [ "$1" = "errors" ]; then
    echo "=== Errors and warnings ==="
    grep -E "ERROR|WARNING" "$LOG_FILE" | tail -50
    
elif [ "$1" = "users" ]; then
    echo "=== User activity ==="
    grep -E "logged in|logged out|posted message" "$LOG_FILE" | tail -50
    
elif [ "$1" = "files" ]; then
    echo "=== File transfers ==="
    grep -E "uploaded|downloaded" "$LOG_FILE" | tail -50
    
elif [ "$1" = "today" ]; then
    TODAY=$(date +%Y-%m-%d)
    echo "=== Logs from today ($TODAY) ==="
    grep "$TODAY" "$LOG_FILE" | tail -100
    
elif [ "$1" = "stats" ]; then
    echo "=== Server Statistics ==="
    echo "Total lines: $(wc -l < "$LOG_FILE")"
    echo "File size: $(du -h "$LOG_FILE" | cut -f1)"
    echo ""
    echo "Logins: $(grep -c 'logged in' "$LOG_FILE")"
    echo "Logouts: $(grep -c 'logged out' "$LOG_FILE")"
    echo "Messages: $(grep -c 'posted message' "$LOG_FILE")"
    echo "Uploads: $(grep -c 'uploaded' "$LOG_FILE")"
    echo "Downloads: $(grep -c 'downloaded' "$LOG_FILE")"
    echo "Errors: $(grep -c ERROR "$LOG_FILE")"
    
elif [ "$1" = "clear" ]; then
    echo "Clearing logs..."
    > "$LOG_FILE"
    echo "Logs cleared"
    
elif [ "$1" = "help" ] || [ "$1" = "-h" ] || [ -z "$1" ]; then
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  (empty)   - Show last 50 lines"
    echo "  follow    - Follow logs in real-time"
    echo "  -f        - Follow logs in real-time"
    echo "  errors    - Show errors and warnings"
    echo "  users     - Show user activity"
    echo "  files     - Show file transfers"
    echo "  today     - Show today's logs"
    echo "  stats     - Show statistics"
    echo "  clear     - Clear log file"
    echo "  help      - Show this help"
    
else
    echo "Unknown command: $1"
    echo "Run '$0 help' for usage"
    exit 1
fi
