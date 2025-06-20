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
def get_kasa_plug():
    # Initialize manager and login with credentials
    mgr = TPLinkDeviceManager()
    mgr.login(KASA_EMAIL, KASA_PASSWORD)
    devices = mgr.get_devices()
    plug = mgr.get_device_by_alias(DEVICE_ALIAS)
    if plug is None:
        aliases = [d.alias for d in devices]
        raise ValueError(f"Plug alias '{DEVICE_ALIAS}' not found. Available: {aliases}")
    return plug

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True  # Ensure enabled in Dev Portal
bot = commands.Bot(command_prefix="!", intents=intents)

# Debug: log incoming messages
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(f"📩 Received message from {message.author}: {message.content}")
    await bot.process_commands(message)

# Debug: log commands
@bot.event
async def on_command(ctx):
    print(f"➡️ Command invoked: {ctx.command} by {ctx.author}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# Basic ping command\@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Core toggling logic
async def toggle_plug(ctx, turn_on: bool):
    action = 'turn_on' if turn_on else 'turn_off'
    print(f"👷 Executing {action}")
    try:
        plug = get_kasa_plug()
        plug.update()
        result = plug.turn_on() if turn_on else plug.turn_off()
        plug.update()
        status = plug.is_on
        print(f"🔌 {action} returned {result}, status now {status}")
        if status == turn_on:
            msg = "✅ Server plug turned **ON**. Booting TrueNAS…" if turn_on else "🛑 Server plug turned **OFF**."
        else:
            msg = f"⚠️ Plug did not {'turn on' if turn_on else 'turn off'}, status is {status}."
        await ctx.send(msg)
    except Exception as e:
        print(f"❌ Error during {action}: {e}")
        await ctx.send(f"⚠️ Failed to {'turn on' if turn_on else 'turn off'} plug: {e}")

# Commands
@bot.command(name="startserver", aliases=["poweron"])
async def startserver(ctx):
    await toggle_plug(ctx, True)

@bot.command(name="shutdownserver", aliases=["poweroff"])
async def shutdownserver(ctx):
    await toggle_plug(ctx, False)

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
