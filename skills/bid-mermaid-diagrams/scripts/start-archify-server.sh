#!/bin/bash
# Start the archify render server in the background.
# Runs OUTSIDE the bwrap sandbox — Chrome/Puppeteer needs full system access.
#
# Usage: bash start-archify-server.sh [port]
#   Default port: 18800

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${1:-${ARCHIFY_PORT:-18800}}"
PIDFILE="/tmp/archify-server-${PORT}.pid"
LOGFILE="/tmp/archify-server-${PORT}.log"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "archify-server already running (pid $(cat "$PIDFILE"), port $PORT)"
  exit 0
fi

ARCHIFY_PORT="$PORT" node "$SCRIPT_DIR/archify-server.mjs" >> "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
sleep 1

if curl -sf "http://127.0.0.1:${PORT}/health" > /dev/null; then
  echo "archify-server started (pid $(cat "$PIDFILE"), port $PORT, log: $LOGFILE)"
else
  echo "archify-server failed to start — check $LOGFILE"
  exit 1
fi
