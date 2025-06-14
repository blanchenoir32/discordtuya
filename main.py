import os
import asyncio
import discord
from discord.ext import commands
from aiohttp import web
from tuya_iot import TuyaOpenAPI

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Tuya API credentials
TUYA_ENDPOINT = "https://openapi.tuyaus.com"
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")

# Discord bot token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is not set in environment variables.")

# Initialize Tuya OpenAPI
openapi = TuyaOpenAPI(TUYA_ENDPOINT, ACCESS_ID, ACCESS_SECRET)
openapi.connect()

# Set up Discord bot with message_content intent enabled
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def poweron(ctx):
    response = openapi.post(
        f"/v1.0/iot-03/devices/{DEVICE_ID}/commands", {
            "commands": [{"code": "switch_1", "value": True}]
        }
    )
    if response.get("success"):
        await ctx.send("🔌 Plug turned **ON**")
    else:
        await ctx.send(f"⚠️ Failed to turn on plug: {response}")

@bot.command()
async def poweroff(ctx):
    response = openapi.post(
        f"/v1.0/iot-03/devices/{DEVICE_ID}/commands", {
            "commands": [{"code": "switch_1", "value": False}]
        }
    )
    if response.get("success"):
        await ctx.send("🔌 Plug turned **OFF**")
    else:
        await ctx.send(f"⚠️ Failed to turn off plug: {response}")

# --- Health check web server for Koyeb Web Service ---
async def start_web_server():
    app = web.Application()
    async def health(request):
        return web.Response(text="OK")
    app.router.add_get('/', health)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Health endpoint running on port {port}")

async def main():
    # Start HTTP server and bot concurrently
    await start_web_server()
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
