import os
import requests
from mcstatus import JavaServer
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MC_HOST = os.getenv("MC_HOST")
MC_PORT = int(os.getenv("MC_PORT", "25565"))
SERVER_NAME = os.getenv("SERVER_NAME", "Minecraft Server")
MESSAGE_ID = os.getenv("MESSAGE_ID")


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
            "footer": {"text": "Updates every 5 minutes"},
        }]
    }


def main():
    online, players = get_server_status()
    payload = build_payload(online, players)

    if MESSAGE_ID:
        r = requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json=payload)
        if r.status_code != 404:
            r.raise_for_status()
            print(f"Updated message {MESSAGE_ID} — {'online' if online else 'offline'}, {players} players")
            return

    r = requests.post(f"{WEBHOOK_URL}?wait=true", json=payload)
    r.raise_for_status()
    new_id = r.json()["id"]
    print(f"Posted new message. Set MESSAGE_ID={new_id} in your GitHub secret.")


if __name__ == "__main__":
    main()
