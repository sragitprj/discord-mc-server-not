import os
import json
import requests
from mcstatus import JavaServer
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MC_HOST = os.getenv("MC_HOST")
MC_PORT = int(os.getenv("MC_PORT", "25565"))
SERVER_NAME = os.getenv("SERVER_NAME", "Minecraft Server")
MESSAGE_ID = os.getenv("MESSAGE_ID")
PLAYERS_FILE = "players.json"


def load_known_players() -> set[str]:
    if os.path.exists(PLAYERS_FILE):
        with open(PLAYERS_FILE) as f:
            return set(json.load(f).get("known_players", []))
    return set()


def save_known_players(players: set[str]):
    with open(PLAYERS_FILE, "w") as f:
        json.dump({"known_players": sorted(players)}, f, indent=2)


def get_server_status() -> tuple[bool, int, list[str]]:
    try:
        server = JavaServer(MC_HOST, MC_PORT, timeout=5)
        status = server.status()
        names = [p.name for p in (status.players.sample or [])]
        return True, status.players.online, names
    except Exception:
        return False, 0, []


def build_payload(online: bool, player_count: int, online_names: list[str], offline_names: list[str]) -> dict:
    color = 0x57F287 if online else 0xED4245
    status_emoji = "🟢" if online else "🔴"
    ip = MC_HOST if MC_PORT == 25565 else f"{MC_HOST}:{MC_PORT}"

    fields = [
        {"name": "Status", "value": "Online" if online else "Offline", "inline": True},
        {"name": "IP", "value": f"`{ip}`", "inline": True},
        {"name": "Players", "value": str(player_count) if online else "—", "inline": True},
    ]

    if online:
        online_value = "\n\n" + "\n".join(f"🟢 {n}" for n in online_names) if online_names else "\n\n*No one online*"
        fields.append({"name": "Online Players", "value": online_value, "inline": False})

        if offline_names:
            offline_value = "\n\n" + "\n".join(f"⚫ {n}" for n in offline_names)
            fields.append({"name": "Offline Players", "value": offline_value, "inline": False})

    return {
        "embeds": [{
            "title": f"{status_emoji} {SERVER_NAME}",
            "color": color,
            "fields": fields,
            "footer": {"text": "Updates every 5 minutes"},
        }]
    }


def main():
    online, player_count, online_names = get_server_status()

    known_players = load_known_players()
    if online_names:
        known_players.update(online_names)
        save_known_players(known_players)

    offline_names = sorted(known_players - set(online_names))
    payload = build_payload(online, player_count, online_names, offline_names)

    if MESSAGE_ID:
        r = requests.patch(f"{WEBHOOK_URL}/messages/{MESSAGE_ID}", json=payload)
        if r.status_code != 404:
            r.raise_for_status()
            print(f"Updated message {MESSAGE_ID} — {'online' if online else 'offline'}, {player_count} players")
            return

    r = requests.post(f"{WEBHOOK_URL}?wait=true", json=payload)
    r.raise_for_status()
    new_id = r.json()["id"]
    print(f"Posted new message. Set MESSAGE_ID={new_id} in your GitHub secret.")


if __name__ == "__main__":
    main()
