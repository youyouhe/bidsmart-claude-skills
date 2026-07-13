#!/bin/bash
PORT="${1:-${ARCHIFY_PORT:-18800}}"
PIDFILE="/tmp/archify-server-${PORT}.pid"

if [ -f "$PIDFILE" ]; then
  PID=$(cat "$PIDFILE")
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "archify-server stopped (pid $PID)"
  else
    echo "archify-server not running (stale pidfile)"
  fi
  rm -f "$PIDFILE"
else
  echo "archify-server not running (no pidfile)"
fi
