#!/bin/bash
PIDS=$(pgrep -xf "python3 server.py")
if [ -n "$PIDS" ]; then
  # shellcheck disable=SC2086  # intentionally word-split: may be several PIDs
  kill $PIDS
  echo "RPMC stopped (PID: $(echo $PIDS | tr '\n' ' '))"
else
  echo "RPMC is not running"
fi
