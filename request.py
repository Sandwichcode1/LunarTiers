import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import asyncio
from datetime import datetime, timedelta

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

class JoinQueueModal(Modal):
    def __init__(self, user: discord.Member):
        super().__init__(title="Enter your info")
        self.user = user
        self.ign = TextInput(label="Your IGN", placeholder="Enter your in-game name", max_length=32)
        self.region = TextInput(label="Your Region", placeholder="Enter your region (e.g., NA, EU)", max_length=10)
        self.add_item(self.ign)
        self.add_item(self.region)

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
        entry = {
            "user_id": self.user.id,
            "mention": self.user.mention,
            "ign": self.ign.value,
            "region": region_value
        }
        queue.append(entry)
        user_cooldowns[self.user.id] = now + timedelta(days=1)

        waitlist_role = discord.utils.get(interaction.guild.roles, name=waitlist_role_name)
        if waitlist_role:
            await self.user.add_roles(waitlist_role)

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
async def pull(ctx):
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
    category = ctx.channel.category
    channel_name = f"match-{member.name}".lower()
    testers_role = discord.utils.get(ctx.guild.roles, name="Testers")
    if testers_role is None:
        await ctx.send("⚠️ Testers role not found! Please create a role named 'Testers'.")
        return
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        testers_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    try:
        new_channel = await ctx.guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await new_channel.send(f"{testers_role.mention} {member.mention}, your match channel is ready! 🎮")
        await ctx.send(f"✅ Created {new_channel.mention} and pulled {member.mention} from the queue.")
        waitlist_role = discord.utils.get(ctx.guild.roles, name=waitlist_role_name)
        if waitlist_role:
            await member.remove_roles(waitlist_role)
        await update_queue_embed()
    except Exception as e:
        await ctx.send(f"❌ Error creating channel: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def close(ctx, member: discord.Member):
    global queue, user_cooldowns

    now = datetime.utcnow()
    cooldown_duration = timedelta(days=1)

    # Add user to cooldown
    user_cooldowns[member.id] = now + cooldown_duration

    # Remove from queue if present
    queue = [entry for entry in queue if entry["user_id"] != member.id]
    await update_queue_embed()

    # Remove "Waitlist" role so they don't see the queue
    waitlist_role = discord.utils.get(ctx.guild.roles, name="Waitlist")
    if waitlist_role in member.roles:
        await member.remove_roles(waitlist_role)

    # Find and delete user's match channel if exists
    # Assuming channels are named like "match-username"
    channel_name = f"match-{member.name}".lower()
    match_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    if match_channel:
        try:
            await match_channel.delete(reason=f"Closing match channel for {member}")
        except Exception as e:
            await ctx.send(f"⚠️ Could not delete match channel: {e}")

    await ctx.send(f"✅ {member.mention} has been removed from the queue, put on cooldown, lost waitlist access, and their match channel was deleted (if existed).")

@bot.command()
@commands.has_permissions(administrator=True)
async def removecooldown(ctx, member: discord.Member):
    if member.id in user_cooldowns:
        del user_cooldowns[member.id]
        await ctx.send(f"✅ Cooldown removed for {member.mention}.")
    else:
        await ctx.send(f"ℹ️ {member.mention} has no active cooldown.")

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

bot.run("MTM3MjYzMjcwNDU5OTk4NjIzNw.GpsDlw.30RnOvci4BmEQZsFEDr10dZbbeopAfYj5N6lxw")
