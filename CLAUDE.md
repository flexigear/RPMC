# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

RPMC (Remote PC Management Controller) — a LAN-based web tool for remotely powering on, shutting down, and restarting Windows PCs from a mobile browser. Runs on a Linux server.

## Dependencies

```bash
sudo apt install python3-flask sshpass
```

- `python3-flask` — Web framework (backend)
- `sshpass` — Enables non-interactive SSH password authentication for remote shutdown/restart

## Running

```bash
./bin/start.sh    # Start (background)
./bin/stop.sh     # Stop
./bin/restart.sh  # Restart
```

Serves on `0.0.0.0:5000`. Access from phone at `http://<server-ip>:5000`. Log output in `rpmc.log`.


## Architecture

Single-file Flask backend (`server.py`) + single-page frontend (`templates/index.html` with inline CSS/JS).

- **WOL (power on):** Pure Python UDP broadcast of magic packet to port 9. Requires stored MAC address.
- **Shutdown/Restart:** SSH into Windows PC via `sshpass` + `ssh` and runs `shutdown /s /f /t 0` (or `/r` for restart). Requires OpenSSH Server enabled on target PC.
- **MAC resolution:** Pings target then reads `ip neigh show` to get MAC from ARP table.
- **Data persistence:** `data.json` stores PC list (IP, MAC, username, password) as a flat JSON array. Loaded/saved on every request — no caching.

## API Routes

All data routes under `/api/`. Control actions are `POST /api/wake/<ip>`, `POST /api/shutdown/<ip>`, `POST /api/restart/<ip>`. PC CRUD via `GET/POST /api/pcs` and `DELETE /api/pcs/<ip>`. GET `/api/pcs` strips credentials from response.

## Key Conventions

- Frontend is mobile-first, designed for iPhone. All JS/CSS is inline in `index.html`.
- User-facing text and UI are in English; code comments in English.
- The user communicates in Chinese (zh-CN).
