import os
import discord
from discord.ext import commands
from tuya_connector import TuyaOpenAPI

# Load environment variables (optional for local testing)
from dotenv import load_dotenv
load_dotenv()

# Tuya API credentials
TUYA_ENDPOINT = "https://openapi.tuyaus.com"
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")

# Discord bot token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Initialize Tuya OpenAPI
openapi = TuyaOpenAPI(TUYA_ENDPOINT, ACCESS_ID, ACCESS_SECRET)
openapi.connect()

# Set up Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def poweron(ctx):
    response = openapi.post(f"/v1.0/iot-03/devices/{DEVICE_ID}/commands", {
        "commands": [{"code": "switch_1", "value": True}]
    })
    await ctx.send("🔌 Plug turned **ON**" if response.get("success") else "⚠️ Failed to turn on plug")

@bot.command()
async def poweroff(ctx):
    response = openapi.post(f"/v1.0/iot-03/devices/{DEVICE_ID}/commands", {
        "commands": [{"code": "switch_1", "value": False}]
    })
    await ctx.send("🔌 Plug turned **OFF**" if response.get("success") else "⚠️ Failed to turn off plug")

bot.run(DISCORD_TOKEN)
