# Discord Matchmaking Queue Bot (Clean Rewrite)
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from discord.ext import commands
from discord import Intents, Embed, Interaction, Member, PermissionOverwrite
from discord.ui import View, Button, Modal, TextInput
import discord

# Load environment and token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("Missing DISCORD_TOKEN in .env")

# Intents and bot setup
intents = Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Config
RESTRICTED_CHANNEL_ID = 1372659479300149278
WAITLIST_ROLE_ID = 1373005273387503658
REGION_CHANNELS = {
    "EU": 1373230639603515503,
    "NA": 1373230665298083940,
    "AS": 1373230746269126728
}
REGION_ROLES = {
    "EU": 1373005273387503658,
    "NA": 1373231883420176457,
    "AS": 1373231929176096819
}

# Globals
queue = []
user_cooldowns = {}
queue_message = info_message = None
queue_creator = queue_region = None


# Events
@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")


@bot.event
async def on_message(message):
    if message.channel.id == RESTRICTED_CHANNEL_ID and not message.author.bot:
        try:
            await message.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")
    await bot.process_commands(message)


# UI
class JoinQueueModal(Modal):

    def __init__(self, user: Member):
        super().__init__(title="Join the Queue")
        self.user = user
        self.ign = TextInput(label="IGN", placeholder="Your in-game name")
        self.region = TextInput(label="Region", placeholder="NA/EU/AS")
        self.server = TextInput(label="Preferred Server",
                                placeholder="e.g., CrystalChaos")
        for input in (self.ign, self.region, self.server):
            self.add_item(input)


async def on_submit(self, interaction: Interaction):
    global queue
    now = datetime.utcnow()

    if self.user.id in user_cooldowns and user_cooldowns[self.user.id] > now:
        remaining = user_cooldowns[self.user.id] - now
        await interaction.response.send_message(
            f"⏳ Cooldown: {remaining.seconds // 60} mins left.",
            ephemeral=True)
        return

    if any(entry['user_id'] == self.user.id for entry in queue):
        await interaction.response.send_message("You're already in the queue!",
                                                ephemeral=True)
        return

    region_code = self.region.value.upper()
    if region_code not in REGION_CHANNELS:
        await interaction.response.send_message(
            "❌ Invalid region. Use NA/EU/AS.", ephemeral=True)
        return

    # Add to queue
    queue.append({
        "user_id": self.user.id,
        "mention": self.user.mention,
        "ign": self.ign.value,
        "region": region_code,
        "server": self.server.value
    })

    # Assign region-specific waitlist role
    region_role_id = REGION_ROLES[region_code]
    region_role = interaction.guild.get_role(region_role_id)
    if region_role:
        await self.user.add_roles(region_role)

    # Grant access to region channel and remove from others
        fegion_role_id = REGION_ROLES[region_code]
        if interaction.guild:
                            region_role = interaction.guild.get_role(region_role_id)
                            if region_role:
                                await self.user.add_roles(region_role)
        else:
                            await interaction.response.send_message("This interaction must occur within a server.", ephemeral=True)
                            return

    await update_queue_embed()
    await interaction.response.send_message(
        f"✅ Joined queue as {self.ign.value} ({region_code})", ephemeral=True)


class QueueView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Queue", style=discord.ButtonStyle.green)
    async def join(self, interaction: Interaction, button: Button):
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if member:
                await interaction.response.send_modal(JoinQueueModal(member))
            else:
                await interaction.response.send_message(
                    "Could not find you in this server.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "This interaction must occur within a server.", ephemeral=True)


# Commands
@bot.command()
async def createqueue(ctx, *, region: str = "NA"):
    global queue_message, info_message, queue_creator, queue_region
    queue.clear()
    queue_creator, queue_region = ctx.author, region.upper()

    if queue_region not in REGION_CHANNELS:
        await ctx.send("❌ Invalid region. Use NA/EU/AS.")
        return

    view = QueueView()
    embed = Embed(title="🎮 Matchmaking Queue",
                  description="Click to join!",
                  color=discord.Color.blurple())
    queue_message = await ctx.send(embed=embed, view=view)

    info = Embed(title="Queue Info", color=discord.Color.green())
    info.add_field(name="Created by", value=queue_creator.mention)
    info.add_field(name="Region", value=queue_region)
    info_message = await ctx.send(embed=info)


@bot.command()
async def leave(ctx):
    global queue
    queue = [entry for entry in queue if entry['user_id'] != ctx.author.id]
    await ctx.send(f"{ctx.author.mention} left the queue.")
    await update_queue_embed()


@bot.command()
@commands.has_permissions(administrator=True)
async def pull(ctx):
    if not queue:
        await ctx.send("❌ Queue is empty!")
        return
    entry = queue.pop(0)
    member = ctx.guild.get_member(entry['user_id'])
    if not member:
        await ctx.send("⚠️ User not found")
        return

    # Remove waitlist role and access
    waitlist_role = ctx.guild.get_role(WAITLIST_ROLE_ID)
    if waitlist_role:
        await member.remove_roles(waitlist_role)

    region_channel_id = REGION_CHANNELS[entry['region']]
    region_channel = ctx.guild.get_channel(region_channel_id)
    if region_channel:
        await region_channel.set_permissions(member, overwrite=None)

    for rid in REGION_CHANNELS.values():
        if rid != region_channel_id:
            chan = ctx.guild.get_channel(rid)
            if chan:
                await chan.set_permissions(member, overwrite=None)

    overwrites = {
        ctx.guild.default_role: PermissionOverwrite(read_messages=False),
        member: PermissionOverwrite(read_messages=True, send_messages=True),
        ctx.guild.me: PermissionOverwrite(read_messages=True,
                                          send_messages=True)
    }
    match_channel = await ctx.guild.create_text_channel(
        f"match-{member.name}",
        category=ctx.channel.category,
        overwrites=overwrites)
    await match_channel.send(
        f"{member.mention}, your match is ready!\nIGN: {entry['ign']}\nRegion: {entry['region']}\nServer: {entry['server']}"
    )
    await update_queue_embed()


@bot.command()
@commands.has_permissions(administrator=True)
async def done(ctx, member: Member):
    match_channel_name = f"match-{member.name.lower()}"
    match_channel = discord.utils.get(ctx.guild.channels,
                                      name=match_channel_name)
    user_region = next((r for r, rid in REGION_ROLES.items()
                        if ctx.guild.get_role(rid) in member.roles), None)

    if not match_channel or not user_region:
        await ctx.send("❌ Match channel or region not found.")
        return

    # Remove permissions and role
    waitlist_role = ctx.guild.get_role(REGION_ROLES[user_region])
    if waitlist_role:
        await member.remove_roles(waitlist_role)

    region_chan = ctx.guild.get_channel(REGION_CHANNELS[user_region])
    if region_chan:
        await region_chan.set_permissions(member, overwrite=None)

    user_cooldowns[member.id] = datetime.utcnow() + timedelta(hours=24)
    await match_channel.delete()
    await ctx.send(f"✅ Match for {member.mention} closed. Cooldown started.")

@bot.command()
@commands.has_permissions(administrator=True)
async def removecooldown(ctx, member: discord.Member):
    if member.id in user_cooldowns:
        del user_cooldowns[member.id]
        await ctx.send(f"✅ Cooldown removed for {member.mention}.")
    else:
        await ctx.send(f"ℹ️ {member.mention} has no active cooldown.")

@bot.command()
@commands.has_permissions(administrator=True)
async def givecooldownall(ctx, hours: int):
    if hours < 0:
        await ctx.send("❌ Cooldown hours must be positive.")
        return
    now = datetime.utcnow()
    for member in ctx.guild.members:
        if not member.bot:
            user_cooldowns[member.id] = now + timedelta(hours=hours)
    await ctx.send(f"✅ Set {hours}h cooldown for all members.")

@bot.command()
@commands.has_permissions(administrator=True)
async def removecooldownall(ctx):
    removed = 0
    for member in ctx.guild.members:
        if member.id in user_cooldowns:
            del user_cooldowns[member.id]
            removed += 1
    await ctx.send(f"✅ Removed cooldown for {removed} members.")


async def update_queue_embed():
    if not queue_message:
        return
    embed = Embed(title="🎮 Matchmaking Queue", color=discord.Color.blurple())
    embed.description = "\n".join([
        f"**{i+1}.** {e['mention']} | {e['ign']} ({e['region']}) - {e['server']}"
        for i, e in enumerate(queue)
    ]) or "Queue is empty."
    await queue_message.edit(embed=embed)


# Start bot
bot.run(TOKEN)