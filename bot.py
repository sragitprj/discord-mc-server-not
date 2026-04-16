import discord
from discord.ext import tasks
from mcstatus import JavaServer
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MC_HOST = os.getenv("MC_HOST")
MC_PORT = int(os.getenv("MC_PORT", "25565"))
SERVER_NAME = os.getenv("SERVER_NAME", "Minecraft Server")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

status_message: discord.Message | None = None


def get_server_status() -> tuple[bool, int]:
    try:
        server = JavaServer(MC_HOST, MC_PORT, timeout=5)
        status = server.status()
        return True, status.players.online
    except Exception:
        return False, 0


def build_embed(online: bool, player_count: int) -> discord.Embed:
    color = discord.Color.green() if online else discord.Color.red()
    status_emoji = "🟢" if online else "🔴"
    status_text = "Online" if online else "Offline"

    embed = discord.Embed(title=f"{status_emoji} {SERVER_NAME}", color=color)
    embed.add_field(name="Status", value=status_text, inline=True)
    embed.add_field(name="IP", value=f"`{MC_HOST}`" if MC_PORT == 25565 else f"`{MC_HOST}:{MC_PORT}`", inline=True)
    embed.add_field(name="Players", value=str(player_count) if online else "—", inline=True)
    embed.set_footer(text="Updates every 60 seconds")
    return embed


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    update_status.start()


@tasks.loop(seconds=60)
async def update_status():
    global status_message

    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel {CHANNEL_ID} not found")
        return

    online, players = get_server_status()
    embed = build_embed(online, players)

    if status_message is None:
        # Try to find an existing pinned message from this bot
        async for msg in channel.history(limit=50):
            if msg.author == client.user:
                status_message = msg
                break

    if status_message is not None:
        await status_message.edit(embed=embed)
    else:
        status_message = await channel.send(embed=embed)


client.run(TOKEN)
