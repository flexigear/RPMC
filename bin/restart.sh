#!/bin/bash
DIR="$(dirname "$0")"
"$DIR/stop.sh"
sleep 1
"$DIR/start.sh"
