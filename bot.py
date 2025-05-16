
import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Only needed if your bot uses member info

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

queue = []  # list of dicts with keys: user_id, mention, ign, region
queue_message = None
info_message = None
queue_channel = None
queue_creator = None
queue_region = None


@bot.command()
@commands.has_permissions(administrator=True)
async def removecooldown(ctx, member: discord.Member):
    """Remove the 24h cooldown for a specific user."""
    if member.id in user_cooldowns:
        del user_cooldowns[member.id]
        await ctx.send(f"✅ Cooldown removed for {member.mention}.")
    else:
        await ctx.send(f"ℹ️ {member.mention} has no active cooldown.")


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

        if any(entry["user_id"] == self.user.id for entry in queue):
            await interaction.response.send_message("You are already in the queue!", ephemeral=True)
            return

        entry = {
            "user_id": self.user.id,
            "mention": self.user.mention,
            "ign": self.ign.value,
            "region": self.region.value.upper(),
        }
        queue.append(entry)
        await update_queue_embed()
        await interaction.response.send_message(
            f"✅ You joined the queue as **{entry['ign']}** ({entry['region']})!", ephemeral=True
        )

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
        lines = []
        for i, entry in enumerate(queue):
            lines.append(f"**{i+1}.** {entry['mention']} | IGN: **{entry['ign']}** | Region: **{entry['region']}**")
        embed.description = "\n".join(lines)
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
async def leave(ctx):
    global queue
    user_id = ctx.author.id
    before = len(queue)
    queue = [entry for entry in queue if entry["user_id"] != user_id]
    if len(queue) < before:
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
    try:
        new_channel = await ctx.guild.create_text_channel(channel_name, category=category)
        await new_channel.send(f"Your match channel has been created, {member.mention}! 🎮")
        await ctx.send(f"✅ Created {new_channel.mention} for {member.mention}.")
        await update_queue_embed()
    except Exception as e:
        await ctx.send(f"❌ Error creating channel: {e}")

@bot.command()
async def closequeue(ctx):
    global queue, queue_message, info_message
    queue.clear()
    try:
        if queue_message:
            await queue_message.delete()
            queue_message = None
        if info_message:
            await info_message.delete()
            info_message = None
        await ctx.send("✅ Queue closed and messages deleted.")
    except Exception as e:
        await ctx.send(f"❌ Error closing queue: {e}")
















@bot.command()
async def requesttest(ctx):
    """Send a test join queue message in a different channel."""

    # Replace this with your target channel ID where you want the test message to go
    target_channel_id = 1368153339753140306 # <-- put the actual channel ID here

    target_channel = ctx.guild.get_channel(target_channel_id)
    if not target_channel:
        await ctx.send("❌ Could not find the target channel. Check the channel ID.")
        return

    await ctx.send(f"Sending test join message in {target_channel.mention}...")

    embed = discord.Embed(
        title="Test Join Queue Button",
        description="Click the button to open the info modal.",
        color=discord.Color.orange(),
    )
    view = QueueView()

    await target_channel.send(embed=embed, view=view)
    
bot.run("MTM3MjYzMjcwNDU5OTk4NjIzNw.Gqy4Ie.zrEMiR20m-oVOVE19vivCR_b2tvZI9sLhIB86A")