#!/bin/bash
cd "$(dirname "$0")/.."
if pgrep -xf "python3 server.py" > /dev/null; then
  echo "RPMC is already running"
  exit 0
fi
nohup python3 server.py > rpmc.log 2>&1 &
PID=$!
sleep 2
if kill -0 "$PID" 2>/dev/null; then
  echo "RPMC started (PID: $PID)"
else
  echo "RPMC failed to start. Check rpmc.log for details."
  exit 1
fi
