from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is running")

app = web.Application()
app.add_routes([web.get("/", handle)])

import asyncio

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

    print(f"Web server running on port {PORT}")

    while True:
        await asyncio.sleep(3600)

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def start_bot():
    await bot.start("YOUR_BOT_TOKEN")

async def main_runner():
    await asyncio.gather(main(), start_bot())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_runner())
