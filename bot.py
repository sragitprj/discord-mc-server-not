import time
import json
import os
import requests
from mcstatus import JavaServer
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MC_HOST = os.getenv("MC_HOST")
MC_PORT = int(os.getenv("MC_PORT", "25565"))
SERVER_NAME = os.getenv("SERVER_NAME", "Minecraft Server")
MESSAGE_ID_FILE = "message_id.txt"
UPDATE_INTERVAL = 60


def get_server_status() -> tuple[bool, int]:
    try:
        server = JavaServer(MC_HOST, MC_PORT, timeout=5)
        status = server.status()
        return True, status.players.online
    except Exception:
        return False, 0


def build_payload(online: bool, player_count: int) -> dict:
    color = 0x57F287 if online else 0xED4245
    status_emoji = "🟢" if online else "🔴"
    ip = MC_HOST if MC_PORT == 25565 else f"{MC_HOST}:{MC_PORT}"

    return {
        "embeds": [{
            "title": f"{status_emoji} {SERVER_NAME}",
            "color": color,
            "fields": [
                {"name": "Status", "value": "Online" if online else "Offline", "inline": True},
                {"name": "IP", "value": f"`{ip}`", "inline": True},
                {"name": "Players", "value": str(player_count) if online else "—", "inline": True},
            ],
            "footer": {"text": "Updates every 60 seconds"},
        }]
    }


def load_message_id() -> str | None:
    if os.path.exists(MESSAGE_ID_FILE):
        return open(MESSAGE_ID_FILE).read().strip()
    return None


def save_message_id(message_id: str):
    with open(MESSAGE_ID_FILE, "w") as f:
        f.write(message_id)


def post_or_edit(payload: dict):
    message_id = load_message_id()

    if message_id:
        r = requests.patch(f"{WEBHOOK_URL}/messages/{message_id}", json=payload)
        if r.status_code == 404:
            message_id = None

    if not message_id:
        r = requests.post(f"{WEBHOOK_URL}?wait=true", json=payload)
        r.raise_for_status()
        save_message_id(r.json()["id"])


def main():
    print(f"Tracking {SERVER_NAME} ({MC_HOST}:{MC_PORT})")
    while True:
        try:
            online, players = get_server_status()
            post_or_edit(build_payload(online, players))
            print(f"Updated — {'online' if online else 'offline'}, {players} players")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    main()
