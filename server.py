import json
import os
import socket
import struct
import subprocess
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / "data.json"


def load_pcs():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []


def save_pcs(pcs):
    DATA_FILE.write_text(json.dumps(pcs, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_mac(ip):
    """Try to resolve MAC address from ARP table."""
    try:
        # First ping to ensure ARP entry exists
        subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                       capture_output=True, timeout=3)
        result = subprocess.run(["ip", "neigh", "show", ip],
                                capture_output=True, text=True, timeout=3)
        match = re.search(r"([\da-fA-F]{2}:){5}[\da-fA-F]{2}", result.stdout)
        if match:
            return match.group(0).lower()
    except Exception:
        pass
    return None


def send_wol(mac):
    """Send Wake-on-LAN magic packet."""
    mac_bytes = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    magic = b"\xff" * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(magic, ("255.255.255.255", 9))


def remote_shutdown(ip, username, password, reboot=False):
    """Shutdown or restart a remote Windows PC via net rpc."""
    cmd = ["net", "rpc", "shutdown", "-I", ip, "-U", f"{username}%{password}", "-f"]
    if reboot:
        cmd.append("-r")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True, "OK"
        return False, result.stderr.strip() or result.stdout.strip() or "Unknown error"
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError:
        return False, "net rpc not found. Install samba-common-bin: sudo apt install samba-common-bin"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/pcs", methods=["GET"])
def get_pcs():
    pcs = load_pcs()
    # Return without passwords for security
    safe = [{"ip": p["ip"], "mac": p.get("mac", "")} for p in pcs]
    return jsonify(safe)


@app.route("/api/pcs", methods=["POST"])
def add_pc():
    data = request.json
    ip = data.get("ip", "").strip()
    mac = data.get("mac", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not ip:
        return jsonify({"error": "IP is required"}), 400
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Auto-resolve MAC if not provided
    if not mac:
        mac = resolve_mac(ip) or ""

    pcs = load_pcs()
    # Update if exists, otherwise add
    for p in pcs:
        if p["ip"] == ip:
            p.update({"mac": mac, "username": username, "password": password})
            save_pcs(pcs)
            return jsonify({"ip": ip, "mac": mac})

    pcs.append({"ip": ip, "mac": mac, "username": username, "password": password})
    save_pcs(pcs)
    return jsonify({"ip": ip, "mac": mac})


@app.route("/api/pcs/<ip>", methods=["DELETE"])
def delete_pc(ip):
    pcs = load_pcs()
    pcs = [p for p in pcs if p["ip"] != ip]
    save_pcs(pcs)
    return jsonify({"ok": True})


@app.route("/api/wake/<ip>", methods=["POST"])
def wake_pc(ip):
    pcs = load_pcs()
    pc = next((p for p in pcs if p["ip"] == ip), None)
    if not pc:
        return jsonify({"error": "PC not found"}), 404
    mac = pc.get("mac", "")
    if not mac:
        return jsonify({"error": "MAC address unknown. Please edit and provide MAC."}), 400
    try:
        send_wol(mac)
        return jsonify({"ok": True, "message": "WOL packet sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/shutdown/<ip>", methods=["POST"])
def shutdown_pc(ip):
    pcs = load_pcs()
    pc = next((p for p in pcs if p["ip"] == ip), None)
    if not pc:
        return jsonify({"error": "PC not found"}), 404
    ok, msg = remote_shutdown(ip, pc["username"], pc["password"], reboot=False)
    if ok:
        return jsonify({"ok": True, "message": "Shutdown command sent"})
    return jsonify({"error": msg}), 500


@app.route("/api/restart/<ip>", methods=["POST"])
def restart_pc(ip):
    pcs = load_pcs()
    pc = next((p for p in pcs if p["ip"] == ip), None)
    if not pc:
        return jsonify({"error": "PC not found"}), 404
    ok, msg = remote_shutdown(ip, pc["username"], pc["password"], reboot=True)
    if ok:
        return jsonify({"ok": True, "message": "Restart command sent"})
    return jsonify({"error": msg}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
