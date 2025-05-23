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
TOKEN = os.environ["DISCORD_TOKEN"]
if not TOKEN:
    raise ValueError(
        "Please add your Discord bot token in the Secrets tab with key 'DISCORD_TOKEN'"
 
)  
    
user_profiles = {}
intents = Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
@bot.command()

async def restricted_command(ctx):
    await ctx.send("This command is restricted to administrators.")
# Intents and bot setup
user_data = {}  # Global or class-level
# Intents and bot setup
user_data = {}  # Global or class-level
@bot.event
async def on_interaction(interaction):
    user = interaction.user  # Defines the user from the button click
    print(user.id)
class MyView(discord.ui.View):
    @discord.ui.button(label="Click Me", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        print(user.name)
        user_data[user.id] = {
            "region": "EU",
            "ign": "Notch",
            "joined_at": datetime.utcnow()
        }

@bot.check
async def role_check(ctx):
    required_role_id = 1368153209729716224
    return any(role.id == required_role_id for role in ctx.author.roles)

# Config
RESTRICTED_CHANNEL_ID = 1372659479300149278
WAITLIST_ROLE_ID = 1373005273387503658
REGION_CHANNELS = {
    "EU": 1374257102134181920,
    "NA": 1374257103283421184,
    "AS": 1374257110732509224
}

HIGH_TIER_CHANNELS = {
    "EU_HIGH": 1374257112690987059,
    "NA_HIGH": 1374257113920045136,
    "AS_HIGH": 1374257115656355870,
    # "EU_ELITE": 1374257112690987059,  # Removed
    # "NA_ELITE": 1374257113920045136,  # Removed
    # "AS_ELITE": 1374257115656355870   # Removed
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

# Further events and commands follow...


# Events
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

    # Store last testing session time
    global last_testing_session, queue_message, info_message
    last_testing_session = "No recent sessions"
    queue_message = None
    info_message = None
    queue.clear()

    for guild in bot.guilds:
        # Send No Testers Online to region waitlist channels
        for region, channel_id in REGION_CHANNELS.items():
            channel = guild.get_channel(channel_id)
            if channel:
                # Clear existing messages
                try:
                    await channel.purge(limit=100)
                except:
                    pass

                # Send new embed
                embed = discord.Embed(
                    title=f"No Testers Online - {region}",
                    description=
                    f"No testers for {region} region are available at this time.\nYou will be pinged when a tester is available.\nCheck back later!",
                    color=discord.Color.red())
                embed.add_field(name="Last testing session",
                                value=last_testing_session)
                await channel.send(embed=embed)

        # Send request messages to appropriate channels
        normal_request_channel = guild.get_channel(1368153328000962694)
        high_tier_request_channel = guild.get_channel(1368153336599023760)

        if normal_request_channel:
            async for message in normal_request_channel.history(limit=100):
                try:
                    await message.delete()
                except:
                    continue
            ctx = await bot.get_context(
                await normal_request_channel.send("Initializing..."))
            await requesttest(ctx)

        if high_tier_request_channel:
            async for message in high_tier_request_channel.history(limit=100):
                try:
                    await message.delete()
                except:
                    continue
            ctx = await bot.get_context(
                await high_tier_request_channel.send("Initializing..."))
            await highrequesttest(ctx)


@bot.event
async def on_message(message):
    if message.channel.id == RESTRICTED_CHANNEL_ID and not message.author.bot:
        try:
            await message.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")
    await bot.process_commands(message)





class HighTierView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Request High Tier Test",
                       style=discord.ButtonStyle.green)
    async def request_high_tier(self, interaction: Interaction,
                                button: Button):
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if member:
                await interaction.response.send_modal(HighTierModal(member))
            else:
                await interaction.response.send_message(
                    "Could not find you in this server.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "This interaction must occur within a server.", ephemeral=True)


class HighTierModal(Modal):

    def __init__(self, user: Member):
        super().__init__(title="High Tier Test Request")
        self.user = user
        self.ign = TextInput(label="IGN", placeholder="Your in-game name")
        self.region = TextInput(label="Region", placeholder="NA/EU/AS")
        self.lt3 = TextInput(label="Are you LT3 or above?",
                             placeholder="Yes/No")
        self.add_item(self.ign)
        self.add_item(self.region)
        self.add_item(self.lt3)

class JoinQueueModal(Modal):
    def __init__(self, user: Member):
        super().__init__(title="Join the Queue")
        self.user = user

        profile = user_profiles.get(user.id, {})
        self.ign = TextInput(
            label="IGN",
            placeholder="Your in-game name",
            default=profile.get("ign", "")
        )
        self.region = TextInput(
            label="Region",
            placeholder="NA/EU/AS",
            default=profile.get("region", "")
        )
        self.server = TextInput(
            label="Preferred Server",
            placeholder="e.g., CrystalChaos",
            default=profile.get("server", "")
        )

        for input in (self.ign, self.region, self.server):
            self.add_item(input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user = interaction.user
            now = datetime.utcnow()  # Updated to use correct datetime reference

            # Cooldown check
            if user.id in user_cooldowns and user_cooldowns[user.id] > now:
                remaining = user_cooldowns[user.id] - now
                await interaction.response.send_message(
                    f"⏳ Cooldown: {remaining.seconds // 60} mins left.",
                    ephemeral=True
                )
                return

            # Already in queue check
            if any(entry['user_id'] == user.id for entry in queue):
                await interaction.response.send_message(
                    "You're already in the queue!",
                    ephemeral=True
                )
                return

            # Region validation
            region_code = self.region.value.upper()
            if region_code not in REGION_CHANNELS:
                await interaction.response.send_message(
                    "❌ Invalid region. Use NA/EU/AS.",
                    ephemeral=True
                )
                return

            # Add to queue
            queue.append({
                "user_id": user.id,
                "mention": user.mention,
                "ign": self.ign.value,
                "region": region_code,
                "server": self.server.value
            })

            # Assign region-specific role
            region_role_id = REGION_ROLES[region_code]
            region_role = interaction.guild.get_role(region_role_id)
            if region_role:
                await user.add_roles(region_role)

            # Update queue embed
            await update_queue_embed()

            await interaction.response.send_message(
                f"✅ Joined queue as {self.ign.value} ({region_code})",
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in modal submit: {e}")
            try:
                await interaction.response.send_message(
                    "Something went wrong while processing your request.",
                    ephemeral=True
                )
            except Exception as inner_e:
                print(f"Error sending response: {inner_e}")
                



@bot.command()
async def createqueue(ctx, *, region: str = "NA"):
    global queue_message, info_message, queue_creator, queue_region
    queue.clear()
    queue_creator, queue_region = ctx.author, region.upper()

    if queue_region not in REGION_CHANNELS:
        await ctx.send("❌ Invalid region. Use NA/EU/AS.")
        return

    # Delete "No Testers Online" message only in current channel
    async for message in ctx.channel.history(limit=100):
        if message.author == bot.user and message.embeds and "No Testers Online" in message.embeds[0].title:
            await message.delete()

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

async def pull(ctx):
    global queue, user_cooldowns
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

    # Add cooldown for the pulled user (1 hour cooldown)
    now = datetime.utcnow()
    user_cooldowns[member.id] = now + timedelta(hours=24)

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
        ctx.guild.me: PermissionOverwrite(read_messages=True, send_messages=True)
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

async def close(ctx):
                            global queue

                            # Check if command was used in a match channel
                            if not ctx.channel.name.startswith("match-"):
                                await ctx.send("❌ This command can only be used in match channels!")
                                return

                            # Remove all user entries from the queue
                            queue.clear()

                            # Delete match channel
                            try:
                                await ctx.channel.delete(reason=f"Match closed by {ctx.author.name}")
                            except Exception as e:
                                await ctx.send(f"⚠️ Could not delete the channel: {e}")


@bot.command()

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

async def removecooldownall(ctx):
    removed = 0
    for member in ctx.guild.members:
        if member.id in user_cooldowns:
            del user_cooldowns[member.id]
            removed += 1
    await ctx.send(f"✅ Removed cooldown for {removed} members.")


@bot.command()

async def setup_channels(ctx):
    # Create Server Info category
    server_info = await ctx.guild.create_category("Server Info")

    # Create channels
    overwrites = {
        ctx.guild.default_role:
        discord.PermissionOverwrite(read_messages=True, send_messages=False),
        ctx.guild.me:
        discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    await ctx.guild.create_text_channel('🤖┃bot-status',
                                        category=server_info,
                                        overwrites=overwrites)

    # Create region waitlist channels
    waitlist_overwrites = {
        ctx.guild.default_role:
        discord.PermissionOverwrite(read_messages=False, send_messages=False),
        ctx.guild.me:
        discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }



@bot.command()

async def stopqueue(ctx):
    global queue, queue_message, info_message
    queue.clear()

    # Clear all messages in the channel
    await ctx.channel.purge(limit=100)

    queue_message = None
    info_message = None

    # Send "No Testers Online" embed
    embed = Embed(
        title="No Testers Online",
        description="No testers for your region are available at this time.\nYou will be pinged when a tester is available.\nCheck back later!",
        color=discord.Color.red()
    )
    embed.add_field(name="Last testing session", value="No recent sessions")
    await ctx.channel.send(embed=embed)

    await ctx.send("✅ Queue stopped and cleared.")


async def update_queue_embed():
    if not queue_message:
        return
    embed = Embed(title="🎮 Matchmaking Queue", color=discord.Color.blurple())
    embed.description = "\n".join([
        f"**{i+1}.** {e['mention']} | {e['ign']} ({e['region']}) - {e['server']}"
        for i, e in enumerate(queue)
    ]) or "Queue is empty."
    await queue_message.edit(embed=embed)


@bot.command()

async def requesttest(ctx):
    embed = discord.Embed(
        title="📨 Request a Tier Test",
        description="Click the button below to request a tier test!",
        color=discord.Color.orange())
    view = QueueView()
    await ctx.send(embed=embed, view=view)


@bot.command()

async def highrequesttest(ctx):
    embed = discord.Embed(
        title="📨 Request a High Tier Test",
        description="Click the button below to request a high tier test!",
        color=discord.Color.purple())
    view = HighTierView()
    await ctx.send(embed=embed, view=view)


@bot.command()

async def removecooldown(ctx, member: discord.Member):
    global user_cooldowns
    if member.id in user_cooldowns:
        del user_cooldowns[member.id]
        await ctx.send(f"✅ Cooldown removed for {member.mention}.")
    else:
        await ctx.send(f"ℹ️ {member.mention} has no active cooldown.")

# Start bot
bot.run(TOKEN)