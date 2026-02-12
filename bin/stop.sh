#!/bin/bash
PID=$(pgrep -f "python3.*server.py")
if [ -n "$PID" ]; then
  kill "$PID"
  echo "RPMC stopped (PID: $PID)"
else
  echo "RPMC is not running"
fi
