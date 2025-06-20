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

# Async helper to get the Kasa plug
async def get_kasa_plug():
    mgr = TPLinkDeviceManager()
    await mgr.login(KASA_EMAIL, KASA_PASSWORD)
    devices = await mgr.get_devices()
    for d in devices:
        if d.alias == DEVICE_ALIAS:
            return d
    aliases = [d.alias for d in devices]
    print(f"❌ Plug alias '{DEVICE_ALIAS}' not found. Available aliases: {aliases}")
    return None

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True  # ensure this is enabled in Dev Portal
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(f"📩 Received message from {message.author}: {message.content}")
    await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    print(f"➡️ Command invoked: {ctx.command} by {ctx.author}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command(name="ping", aliases=["latency"])
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Core toggling logic
async def toggle_plug(ctx, turn_on: bool):
    action = 'turn_on' if turn_on else 'turn_off'
    print(f"👷 Executing {action}")
    try:
        plug = await get_kasa_plug()
        if plug is None:
            await ctx.send("⚠️ No matching Kasa plug found. Check alias.")
            return
        if turn_on:
            await plug.turn_on()
        else:
            await plug.turn_off()
        status = plug.is_on
        print(f"🔌 {action} complete, status now {status}")
        if status == turn_on:
            msg = ("✅ Server plug turned **ON**. Booting TrueNAS…" if turn_on 
                   else "🛑 Server plug turned **OFF**.")
        else:
            msg = f"⚠️ Plug did not {'turn on' if turn_on else 'turn off'}, status is {status}."
        await ctx.send(msg)
    except Exception as e:
        print(f"❌ Error during {action}: {e}")
        await ctx.send(f"⚠️ Failed to {'turn on' if turn_on else 'turn off'} plug: {e}")

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

# Safe asyncio startup for environments with already-running loops
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            print("⚠️ Event loop already running. Using alternative startup.")
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
