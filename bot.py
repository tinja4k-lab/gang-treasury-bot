import os
import discord
from discord.ext import commands

# -----------------------------
# CONFIG
# -----------------------------

TOKEN = os.getenv("TOKEN")

MONEY_ROLE_ID = 1510964147100188733

# -----------------------------
# INTENTS
# -----------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # REQUIRED for role checking

bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------------------
# ROLE CHECK FUNCTION
# -----------------------------

def has_money_role(interaction: discord.Interaction) -> bool:
    return any(role.id == MONEY_ROLE_ID for role in interaction.user.roles)


# -----------------------------
# READY EVENT (SYNC COMMANDS)
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
# /CLEAR COMMAND
# -----------------------------

@bot.tree.command(name="clear", description="Clear all withdraws and deposits")
async def clear(interaction: discord.Interaction):

    # 🔒 Permission check
    if not has_money_role(interaction):
        await interaction.response.send_message(
            "❌ You need the **Money** role to use this command.",
            ephemeral=True
        )
        return

    # ✅ Main response
    await interaction.response.send_message(
        "✅ All withdraws and deposits have been cleared.",
        ephemeral=True
    )


# -----------------------------
# RUN BOT
# -----------------------------

bot.run(TOKEN)
