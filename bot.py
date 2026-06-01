import os
import discord
from discord.ext import commands
from discord import app_commands

# -----------------------------
# CONFIG
# -----------------------------

TOKEN = os.getenv("TOKEN")  # Use Render environment variable

MONEY_ROLE_ID = 1510964147100188733

# -----------------------------
# INTENTS
# -----------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # REQUIRED for role checks

bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------------------
# ROLE CHECK DECORATOR
# -----------------------------

def has_money_role():
    def predicate(interaction: discord.Interaction):
        if not interaction.user or not hasattr(interaction.user, "roles"):
            return False
        return any(role.id == MONEY_ROLE_ID for role in interaction.user.roles)
    return app_commands.check(predicate)


# -----------------------------
# BOT READY EVENT (SYNC COMMANDS)
# -----------------------------

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Sync error: {e}")

    print(f"Logged in as {bot.user}")


# -----------------------------
# /CLEAR COMMAND (ROLE LOCKED)
# -----------------------------

@bot.tree.command(name="clear", description="Clear treasury data")
@has_money_role()
async def clear(interaction: discord.Interaction):
    # 🔧 PUT YOUR CLEAR LOGIC HERE
    await interaction.response.send_message(
        "✅ All withdraws and deposits have been cleared.",
        ephemeral=True
    )


# -----------------------------
# ERROR HANDLER (NO PERMISSION)
# -----------------------------

@clear.error
async def clear_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ You need the **Money** role to use this command.",
            ephemeral=True
        )


# -----------------------------
# RUN BOT
# -----------------------------

bot.run(TOKEN)
