import discord
WAITLIST_ROLE_ID = 1373005273387503658  # Replace with your Waitlist role ID
TESTERS_ROLE_ID = 1373005299922663534   # (Optional) Replace with your Testers role ID
def get_waitlist_role(guild: discord.Guild) -> discord.Role | None:
    return guild.get_role(WAITLIST_ROLE_ID)

import os
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

async def status_update_loop():
    while True:
        await update_status_embed()
        await asyncio.sleep(60)  # Update every minute
from pathlib import Path
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
member = []
queue = []
queue_message = None
info_message = None
queue_channel = None
queue_creator = None
queue_region = None
user_cooldowns = {}
allowed_regions = ["NA", "EU", "ASIA", "SA", "OCE", "AFRICA"]
request_channel_id = 1368153339753140306  # Replace with actual channel ID
waitlist_role_name = "Waitlist"
WAITLIST_ROLE_ID = 1373005273387503658  # Replace with your Waitlist role ID
TESTERS_ROLE_ID = 1373005299922663534   # (Optional) Replace with your Testers role ID
import os
from dotenv import load_dotenv
from pathlib import Path
import discord

async def update_no_testers_embeds(guild):
    # Channel IDs for region waitlist channels
    region_waitlist_channels = [1373230639603515503, 1373230665298083940, 1373230746269126728]
    high_tier_category = discord.utils.get(guild.categories, name="High Tier Tests")

    embed = discord.Embed(
        title="No Testers Online",
        description="No testers for your region are available at this time.\nYou will be pinged when a tester is available.\nCheck back later!",
        color=discord.Color.red()
    )
    embed.add_field(name="Last testing session", value=last_testing_session)

    # Update region waitlist channels
    for channel_id in region_waitlist_channels:
        channel = guild.get_channel(channel_id)
        if channel:
            # Delete previous messages from the bot
            async for message in channel.history(limit=100):
                if message.author == bot.user:
                    await message.delete()
            # Send new embed
            await channel.send(embed=embed)

    # Update high tier channels
    if high_tier_category:
        for channel in high_tier_category.channels:
            if channel.name.startswith("high-tier-"):
                # Delete previous messages from the bot
                async for message in channel.history(limit=100):
                    if message.author == bot.user:
                        await message.delete()
                # Send new embed
                await channel.send(embed=embed)


from discord.ext import commands

env_path = Path(__file__).parent / 'library.env'  # or '.env'
print(f"Loading env from: {env_path.resolve()}")

load_dotenv(dotenv_path=env_path)

token = os.getenv("DISCORD_TOKEN")
print(f"Token loaded: {repr(token)}")

if not token:
    raise ValueError("DISCORD_TOKEN environment variable not found.")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

async def update_status_embed():
    for guild in bot.guilds:
        status_channel = discord.utils.get(guild.channels, name="🤖┃bot-status")
        if status_channel:
            embed = discord.Embed(
                title="🤖 Bot Status Dashboard",
                description="Real-time bot monitoring and statistics",
                color=discord.Color.brand_green()
            )
            
            # Server Stats
            embed.add_field(name="🟢 Status", value="Online", inline=True)
            embed.add_field(name="📊 Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
            embed.add_field(name="⚡ Uptime", value="Active", inline=True)
            
            # Queue Stats
            embed.add_field(name="👥 Active Queues", value=str(len(queue)), inline=True)
            embed.add_field(name="⏳ Users on Cooldown", value=str(len(user_cooldowns)), inline=True)
            embed.add_field(name="🌐 Total Users", value=str(len(guild.members)), inline=True)
            
            # System Info
            current_time = datetime.utcnow()
            embed.set_footer(text=f"Last updated: {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            # Delete previous status messages
            async for message in status_channel.history(limit=10):
                if message.author == bot.user:
                    await message.delete()
            
            await status_channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

    # Store last testing session time
    global last_testing_session, queue_message, info_message
    last_testing_session = "No recent sessions"
    queue_message = None
    info_message = None
    queue.clear()

    # Clear messages from region-waitlist and high-tier channels
    region_channels = [1373230639603515503, 1373230665298083940, 1373230746269126728]  # Region waitlist channels
    
    for guild in bot.guilds:
        # Clear region waitlist channels
        for channel_id in region_channels:
            channel = guild.get_channel(channel_id)
            if channel:
                async for message in channel.history(limit=100):
                    try:
                        await message.delete()
                    except:
                        continue
        
        # Clear high tier channels
        high_tier_category = discord.utils.get(guild.categories, name="High Tier Tests")
        if high_tier_category:
            for channel in high_tier_category.channels:
                async for message in channel.history(limit=100):
                    try:
                        await message.delete()
                    except:
                        continue
        
        # Send "No Testers Online" embed to all channels
        await update_no_testers_embeds(guild)

    # Clear existing queue messages from channels
    request_channels = [1368153339753140306, 1373363129974525974]  # Normal and high tier request channels
    for channel_id in request_channels:
        channel = bot.get_channel(channel_id)
        if channel:
            async for message in channel.history(limit=100):
                if message.author == bot.user:
                    try:
                        await message.delete()
                    except:
                        continue

    # Auto-run commands in their respective channels
    request_channel = bot.get_channel(request_channel_id)  # Normal test requests
    high_tier_channel = bot.get_channel(1373363129974525974)  # High tier requests
    
    if request_channel:
        ctx = await bot.get_context(await request_channel.send("Initializing..."))
        await requesttest(ctx)
    
    if high_tier_channel:
        ctx = await bot.get_context(await high_tier_channel.send("Initializing..."))
        await highrequesttest(ctx)

    # Create status channel and start status updates
    for guild in bot.guilds:
        status_channel = discord.utils.get(guild.channels, name="🤖┃bot-status")
        if not status_channel:
            # Find Server Info category
            category = discord.utils.get(guild.categories, name="Server Info")
            if not category:
                category = await guild.create_category("Server Info")
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            status_channel = await guild.create_text_channel('🤖┃bot-status', category=category, overwrites=overwrites)

        # Start status update loop
        bot.loop.create_task(status_update_loop())

    # Create waitlist channels if they don't exist
    for guild in bot.guilds:
        # Create Server Info category if it doesn't exist
        server_info_category = discord.utils.get(guild.categories, name="Server Info")
        if not server_info_category:
            server_info_category = await guild.create_category("Server Info")

        # Define waitlist channels
        waitlist_channels = {
            "region-waitlist": 1373230639603515503,
            "region-waitlist-na": 1373230665298083940,
            "region-waitlist-asia": 1373230746269126728
        }

        # Create or get channels
        for channel_name, channel_id in waitlist_channels.items():
            channel = guild.get_channel(channel_id)
            if not channel:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel = await guild.create_text_channel(
                    name=channel_name,
                    category=server_info_category,
                    overwrites=overwrites,
                    position=0
                )

        await update_no_testers_embeds(guild)
        # Check/create category
        category = discord.utils.get(guild.categories, name="High Tier Tests")
        if not category:
            category = await guild.create_category("High Tier Tests")

        # Define regions with their colors
        region_data = {
            "NA": {"channel": "high-tier-na", "color": discord.Color.blue()},
            "EU": {"channel": "high-tier-eu", "color": discord.Color.red()},
            "AS": {"channel": "high-tier-asia", "color": discord.Color.green()}
        }

        for region_name, data in region_data.items():
            # Create channel if it doesn't exist
            channel = discord.utils.get(category.channels, name=data["channel"])
            if not channel:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                await guild.create_text_channel(
                    name=data["channel"],
                    category=category,
                    topic=f"High Tier Test requests for {region_name} region",
                    overwrites=overwrites
                )

            # Create region role if it doesn't exist
            role_name = f"High Tier {region_name}"
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                await guild.create_role(
                    name=role_name,
                    color=data["color"],
                    reason=f"High Tier Test role for {region_name} region"
                )







class JoinQueueModal(Modal):
    def __init__(self, user: discord.Member):
        super().__init__(title="Enter your info")
        self.user = user
        self.ign = TextInput(label="Your IGN", placeholder="Enter your in-game name", max_length=32)
        self.region = TextInput(label="Your Region", placeholder="Enter your region (e.g., NA, EU)", max_length=10)
        self.add_item(self.ign)
        self.add_item(self.region)
        self.server = TextInput(label="Preferred Server", placeholder="Enter your preferred server", max_length=32, required=False) # Added preferred server
        self.add_item(self.server) #Added preferred server

    async def on_submit(self, interaction: discord.Interaction):
        global queue
        now = datetime.utcnow()

        if self.user.id in user_cooldowns and user_cooldowns[self.user.id] > now:
            remaining = user_cooldowns[self.user.id] - now
            await interaction.response.send_message(f"⏳ You're on cooldown! Try again in {remaining.seconds // 3600}h {(remaining.seconds % 3600) // 60}m.", ephemeral=True)
            return

        if any(entry["user_id"] == self.user.id for entry in queue):
            await interaction.response.send_message("You are already in the queue!", ephemeral=True)
            return

        region_value = self.region.value.upper()
        if region_value not in allowed_regions:
            await interaction.response.send_message(f"❌ `{region_value}` is not a valid region. Allowed: {', '.join(allowed_regions)}", ephemeral=True)
            return

        # Map regions to role IDs
        region_roles = {
            "EU": 1373005273387503658,
            "NA": 1373231883420176457,
            "AS": 1373231929176096819
        }

        entry = {
            "user_id": self.user.id,
            "mention": self.user.mention,
            "ign": self.ign.value,
            "region": region_value,
            "server": self.server.value
        }
        queue.append(entry)
        user_cooldowns[self.user.id] = now + timedelta(days=1)

        # Add region-specific waitlist role and channel permissions
        if region_value in region_roles:
            waitlist_role = interaction.guild.get_role(region_roles[region_value])
            if waitlist_role:
                await self.user.add_roles(waitlist_role)
                
                # Setup channel access based on region
                eu_channel = interaction.guild.get_channel(1373230639603515503)
                na_channel = interaction.guild.get_channel(1373230665298083940)
                as_channel = interaction.guild.get_channel(1373230746269126728)
                
                # Define region channels
                region_channels = {
                    "EU": eu_channel,
                    "NA": na_channel,
                    "AS": as_channel
                }

                # Remove access to all channels first
                for region, channel in region_channels.items():
                    if channel:
                        # Give access only to the user's region channel
                        if region == region_value:
                            await channel.set_permissions(self.user, read_messages=True, send_messages=True)
                        else:
                            await channel.set_permissions(self.user, read_messages=False, send_messages=False)

        await update_queue_embed()
        await interaction.response.send_message(f"✅ You joined the queue as **{entry['ign']}** ({entry['region']})!", ephemeral=True)


class QueueView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Queue", style=discord.ButtonStyle.green)
    async def join_queue(self, interaction: discord.Interaction, button: Button):
        modal = JoinQueueModal(interaction.user)
        await interaction.response.send_modal(modal)

async def update_queue_embed():
    global queue_message
    if not queue_message:
        return
    embed = discord.Embed(title="🎮 Matchmaking Queue", color=discord.Color.blurple())
    if not queue:
        embed.description = "The queue is currently empty. Click the button to join!"
    else:
        desc_lines = [f"**{i+1}.** {entry['mention']} | IGN: **{entry['ign']}** | Region: **{entry['region']}**" for i, entry in enumerate(queue)]
        embed.description = "\n".join(desc_lines)
    await queue_message.edit(embed=embed)

async def update_info_embed():
    global info_message, queue_creator, queue_region
    if not info_message:
        return
    embed = discord.Embed(title="Queue Info", color=discord.Color.green())
    embed.add_field(name="Created by", value=queue_creator.mention if queue_creator else "Unknown", inline=True)
    embed.add_field(name="Region", value=queue_region or "Unknown", inline=True)
    embed.set_footer(text="Thanks for using this queue bot!")
    await info_message.edit(embed=embed)

@bot.command()
async def createqueue(ctx, *, region: str = "Unknown"):
    global queue_message, info_message, queue_channel, queue_creator, queue_region
    queue.clear()
    region = region.upper()
    if region not in allowed_regions:
        await ctx.send(f"❌ `{region}` is not a valid region.\nAllowed regions: {', '.join(allowed_regions)}")
        return
    queue_creator = ctx.author
    queue_region = region
    queue_channel = ctx.channel

    # Delete "No Testers Online" embed only from the current channel
    async for message in ctx.channel.history(limit=100):
        if message.author == bot.user and message.embeds and message.embeds[0].title == "No Testers Online":
            await message.delete()
    embed = discord.Embed(title="🎮 Matchmaking Queue", description="Click the button to join the queue!", color=discord.Color.blurple())
    view = QueueView()
    queue_message = await ctx.send(embed=embed, view=view)
    info_embed = discord.Embed(title="Queue Info", color=discord.Color.green())
    info_embed.add_field(name="Created by", value=queue_creator.mention, inline=True)
    info_embed.add_field(name="Region", value=queue_region, inline=True)
    info_embed.set_footer(text="Thanks for using this queue bot!")
    info_message = await ctx.send(embed=info_embed)
    await ctx.send(f"✅ Queue created by {queue_creator.mention} for region: **{queue_region}**")

@bot.command()
async def leave(ctx):
    global queue
    user_id = ctx.author.id
    before_len = len(queue)
    queue = [entry for entry in queue if entry["user_id"] != user_id]
    if len(queue) < before_len:
        await ctx.send(f"{ctx.author.mention} left the queue.")
        await update_queue_embed()
    else:
        await ctx.send("You're not in the queue.")

@bot.command()
async def pull(ctx: int):
    global queue
    if not queue:
        await ctx.send("❌ The queue is empty!")
        return

    entry = queue.pop(0)
    user_id = entry["user_id"]
    member = ctx.guild.get_member(user_id)

    if member is None:
        await ctx.send(f"❌ Could not find the user {entry['mention']} in the server.")
        await update_queue_embed()
        return

    waitlist_role = get_waitlist_role(ctx.guild)
    if waitlist_role and waitlist_role in member.roles:
        await member.remove_roles(waitlist_role)

    # Remove access to waitlist channels
    for channel_id in [1373230639603515503, 1373230665298083940, 1373230746269126728]:
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            await channel.set_permissions(member, read_messages=False, send_messages=False)

    # Add cooldown when pulled
    user_cooldowns[user_id] = datetime.utcnow() + timedelta(days=1)



    testers_role = discord.utils.get(ctx.guild.roles, name="☑️Verified Tester")
    if testers_role is None:
        await ctx.send("⚠️ Testers role not found! Please create a role named 'Testers'.")
        return

    category = ctx.channel.category
    channel_name = f"match-{member.name}".lower()

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        testers_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    try:
        # Create channel first with member not having access
        temp_overwrites = overwrites.copy()
        temp_overwrites[member] = discord.PermissionOverwrite(read_messages=False, send_messages=False)
        new_channel = await ctx.guild.create_text_channel(channel_name, category=category, overwrites=temp_overwrites)

        # Send initial messages
        # Create embed for match channel
        match_embed = discord.Embed(title="🎮 Match Details", color=discord.Color.blue())
        match_embed.add_field(name="Player", value=member.mention, inline=False)
        match_embed.add_field(name="In-Game Name", value=entry["ign"], inline=True)
        match_embed.add_field(name="Region", value=entry["region"], inline=True)
        match_embed.add_field(name="Preferred Server", value=entry["server"] or "Not specified", inline=True)
        match_embed.set_footer(text="Good luck with your match! 🎮")

        # Send match details
        await new_channel.send(f"{testers_role.mention}", embed=match_embed)

        # Send high tier test request details if it exists
        if hasattr(entry.get('modal', None), 'high_tier_embed'):
            await new_channel.send(embed=entry.get('modal').high_tier_embed)

        # DM the user
        dm_embed = discord.Embed(title="🎮 Match Found!", description=f"Your match is ready in {new_channel.mention}!", color=discord.Color.green())
        await member.send(embed=dm_embed)
        await ctx.send(f"✅ Created {new_channel.mention} and pulled {member.mention} from the queue.")

        # Now give the member access
        await new_channel.set_permissions(member, read_messages=True, send_messages=True)

    except Exception as e:
        await ctx.send(f"❌ Error creating channel: {e}")

    await update_queue_embed()


@bot.command()
@commands.has_permissions(administrator=True)
async def close(ctx):
    if not ctx.channel.name.startswith("match-"):
        await ctx.send("❌ This command can only be used in match channels!")
        return

    member_name = ctx.channel.name[6:]  # Remove 'match-' prefix
    member = discord.utils.find(lambda m: m.name.lower() == member_name.lower(), ctx.guild.members)

    if member:
        # Remove waitlist role and its permissions
        waitlist_role = get_waitlist_role(ctx.guild)
        if waitlist_role and waitlist_role in member.roles:
            await member.remove_roles(waitlist_role)

        # Remove access to waitlist channels
        for channel_id in [1373230639603515503, 1373230665298083940, 1373230746269126728]:
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                await channel.set_permissions(member, read_messages=False, send_messages=False)

        # Store channel reference for message
        notification_channel = ctx.channel

        try:
            # Send confirmation message before deleting
            await notification_channel.send(f"✅ Match channel closed for {member.mention}")
            await asyncio.sleep(1)  # Small delay to ensure message sends
            await ctx.channel.delete(reason=f"Match completed for {member}")
        except Exception as e:
            if notification_channel.permissions_for(ctx.guild.me).send_messages:
                await notification_channel.send(f"⚠️ Could not delete channel: {e}")
    else:
        await ctx.send("❌ Could not find the associated member for this channel.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setcooldown(ctx, member: discord.Member, hours: int):
    if hours < 0:
        await ctx.send("❌ Cooldown hours must be positive.")
        return
    user_cooldowns[member.id] = datetime.utcnow() + timedelta(hours=hours)
    await ctx.send(f"✅ Set {hours}h cooldown for {member.mention}.")

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
async def stopqueue(ctx):
    global queue, queue_message, info_message
    queue.clear()
    if queue_message:
        await queue_message.delete()
        queue_message = None
    if info_message:
        await info_message.delete()
        info_message = None

    # Clear all messages from region-waitlist and high-tier channels
    region_channels = [1373230639603515503, 1373230665298083940, 1373230746269126728]
    
    # Clear region waitlist channels
    for channel_id in region_channels:
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            async for message in channel.history(limit=100):
                try:
                    await message.delete()
                except:
                    continue
    
    # Clear high tier channels
    high_tier_category = discord.utils.get(ctx.guild.categories, name="High Tier Tests")
    if high_tier_category:
        for channel in high_tier_category.channels:
            async for message in channel.history(limit=100):
                try:
                    await message.delete()
                except:
                    continue

    # Show "No Testers Online" embed only in the channel where queue was stopped
    embed = discord.Embed(
        title="No Testers Online",
        description="No testers for your region are available at this time.\nYou will be pinged when a tester is available.\nCheck back later!",
        color=discord.Color.red()
    )
    embed.add_field(name="Last testing session", value=last_testing_session)
    await ctx.channel.send(embed=embed)
    
    # Restore waitlist role permissions
    waitlist_role = ctx.guild.get_role(WAITLIST_ROLE_ID)
    if waitlist_role:
        for member in ctx.guild.members:
            if any(role.name.startswith("High Tier") for role in member.roles):
                await member.add_roles(waitlist_role)
                
                # Restore queue channel access
                for channel_id in [1373230639603515503, 1373230665298083940, 1373230746269126728]:
                    channel = ctx.guild.get_channel(channel_id)
                    if channel:
                        await channel.set_permissions(member, read_messages=True, send_messages=True)
    
    await ctx.send("✅ Queue has been stopped and cleared. Waitlist permissions restored.")

class HighTierModal(Modal):
    def __init__(self, user: discord.Member):
        super().__init__(title="High Tier Test Request")
        self.user = user
        self.ign = TextInput(label="What is your IGN?", placeholder="Enter your in-game name", max_length=32)
        self.region = TextInput(label="What is your region?", placeholder="Enter your region (e.g., NA, EU)", max_length=10)
        self.lt3 = TextInput(label="Are you LT3 or above?", placeholder="Yes/No", max_length=3)
        self.add_item(self.ign)
        self.add_item(self.region)
        self.add_item(self.lt3)
        self.high_tier_embed = None  # Add attribute to store the embed

    async def on_submit(self, interaction: discord.Interaction):
        region = self.region.value.upper()
        role_name = f"High Tier {region}"
        region_role = discord.utils.get(interaction.guild.roles, name=role_name)
        waitlist_role = interaction.guild.get_role(WAITLIST_ROLE_ID)

        # Define channel IDs for each region
        region_channels = {
            "NA": {"queue": 1374025561776889917, "test": "high-tier-na"},
            "EU": {"queue": 1374025586930024529, "test": "high-tier-eu"},
            "AS": {"queue": 1374025611139866674, "test": "high-tier-asia"}
        }

        # Remove waitlist role temporarily
        if waitlist_role and waitlist_role in self.user.roles:
            await self.user.remove_roles(waitlist_role)

        if region_role:
            await self.user.add_roles(region_role)

            # Set permissions for high tier test channels
            category = discord.utils.get(interaction.guild.categories, name="High Tier Tests")
            if category:
                for channel in category.channels:
                    if channel.name == region_channels[region]["test"]:
                        await channel.set_permissions(self.user, read_messages=True, send_messages=False)
                    else:
                        await channel.set_permissions(self.user, read_messages=False, send_messages=False)

        embed = discord.Embed(
            title="🎮 High Tier Test Request",
            description=f"New request from {self.user.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="In-Game Name", value=self.ign.value, inline=True)
        embed.add_field(name="Region", value=self.region.value, inline=True)
        embed.add_field(name="LT3 or Above", value=self.lt3.value, inline=True)
        self.high_tier_embed = embed  # Store the embed in the modal

        channel = interaction.guild.get_channel(1373363129974525974)
        if channel:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ Your high tier test request has been submitted!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Error: Could not find the high tier test channel.", ephemeral=True)

class HighTierView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Request High Tier Test", style=discord.ButtonStyle.green)
    async def request_high_tier(self, interaction: discord.Interaction, button: Button):
        modal = HighTierModal(interaction.user)
        await interaction.response.send_modal(modal)

@bot.command()
async def requesttest(ctx):
    channel = bot.get_channel(request_channel_id)
    if not channel:
        await ctx.send("❌ Could not find the request channel.")
        return
    embed = discord.Embed(
        title="📨 Request a Tier Test",
        description="Click the button below to request a tier test!",
        color=discord.Color.orange()
    )
    view = QueueView()
    await channel.send(embed=embed, view=view)
    await ctx.send("✅ Tier test request message sent.")

@bot.command()
async def highrequesttest(ctx):
    channel = bot.get_channel(1373363129974525974)
    if not channel:
        await ctx.send("❌ Could not find the high tier request channel.")
        return
    embed = discord.Embed(
        title="📨 Request a High Tier Test",
        description="Click the button below to request a high tier test!",
        color=discord.Color.purple()
    )
    view = HighTierView()
    await channel.send(embed=embed, view=view)
    await ctx.send("✅ High tier test request message sent.")

bot.run(token)