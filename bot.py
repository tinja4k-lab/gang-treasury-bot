import os
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

MONEY_ROLE_ID = 1510964147100188733

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def has_money_role(member: discord.Member) -> bool:
    return any(role.id == MONEY_ROLE_ID for role in member.roles)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"GLOBAL sync complete: {len(synced)} commands")
    except Exception as e:
        print("GLOBAL sync failed:", e)


@bot.tree.command(name="clear", description="Clear all withdraws and deposits")
async def clear(interaction: discord.Interaction):

    if not has_money_role(interaction.user):
        await interaction.response.send_message(
            "❌ You need the Money role to use this command.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "✅ Cleared successfully.",
        ephemeral=True
    )


bot.run(TOKEN)
