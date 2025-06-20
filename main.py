import os
import asyncio
import discord
from discord.ext import commands
from aiohttp import web
from tplinkcloud import TPLinkDeviceManager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Kasa Cloud credentials
KASA_EMAIL = os.getenv("KASA_EMAIL")
KASA_PASSWORD = os.getenv("KASA_PASSWORD")
DEVICE_ALIAS = os.getenv("KASA_DEVICE_ALIAS")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not all([KASA_EMAIL, KASA_PASSWORD, DEVICE_ALIAS, DISCORD_TOKEN]):
    raise ValueError("One or more required environment variables are missing.")

# Helper to get the Kasa plug
async def get_kasa_plug():
    mgr = TPLinkDeviceManager(KASA_EMAIL, KASA_PASSWORD)
    mgr.login()
    return mgr.get_device_by_alias(DEVICE_ALIAS)

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True  # ensure this is enabled in developer portal
bot = commands.Bot(command_prefix="!", intents=intents)

# Debug: log incoming messages
@bot.event
async def on_message(message):
    print(f"📩 Received message: {message.author}: {message.content}")
    await bot.process_commands(message)

# Debug: log commands
@bot.event
async def on_command(ctx):
    print(f"➡️ Command invoked: {ctx.command} by {ctx.author}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def startserver(ctx):
    plug = await get_kasa_plug()
    plug.turn_on()
    await ctx.send("✅ Server plug turned **ON**. Booting TrueNAS…")

@bot.command()
async def shutdownserver(ctx):
    plug = await get_kasa_plug()
    plug.turn_off()
    await ctx.send("🛑 Server plug turned **OFF**.")

# Health check server for free Web Service
async def start_web():
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
    await start_web()
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
