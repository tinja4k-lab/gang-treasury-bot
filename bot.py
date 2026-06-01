import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os

# 🔐 Load token safely from environment variables (Render will provide this)
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 📦 Database setup
conn = sqlite3.connect("gang_money.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS money (
    user_id INTEGER PRIMARY KEY,
    deposited INTEGER DEFAULT 0,
    withdrawn INTEGER DEFAULT 0
)
""")
conn.commit()


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


@bot.tree.command(name="deposit", description="Add money to a member's contribution total")
async def deposit(interaction: discord.Interaction, member: discord.Member, amount: int):

    cursor.execute("INSERT OR IGNORE INTO money(user_id) VALUES(?)", (member.id,))
    cursor.execute(
        "UPDATE money SET deposited = deposited + ? WHERE user_id = ?",
        (amount, member.id)
    )
    conn.commit()

    await interaction.response.send_message(
        f"✅ Added ${amount:,} deposit for {member.display_name}"
    )


@bot.tree.command(name="withdraw", description="Record money paid out to a member")
async def withdraw(interaction: discord.Interaction, member: discord.Member, amount: int):

    cursor.execute("INSERT OR IGNORE INTO money(user_id) VALUES(?)", (member.id,))
    cursor.execute(
        "UPDATE money SET withdrawn = withdrawn + ? WHERE user_id = ?",
        (amount, member.id)
    )
    conn.commit()

    await interaction.response.send_message(
        f"💸 Added ${amount:,} withdrawal for {member.display_name}"
    )


@bot.tree.command(name="money", description="Check a member's gang finances")
async def money(interaction: discord.Interaction, member: discord.Member):

    cursor.execute(
        "SELECT deposited, withdrawn FROM money WHERE user_id = ?",
        (member.id,)
    )
    data = cursor.fetchone()

    deposited, withdrawn = data if data else (0, 0)
    net = deposited - withdrawn

    embed = discord.Embed(
        title=f"{member.display_name}'s Gang Finances"
    )

    embed.add_field(name="Deposited", value=f"${deposited:,}", inline=False)
    embed.add_field(name="Withdrawn", value=f"${withdrawn:,}", inline=False)
    embed.add_field(name="Net Contribution", value=f"${net:,}", inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="leaderboard", description="Top contributors")
async def leaderboard(interaction: discord.Interaction):

    cursor.execute("""
        SELECT user_id, deposited, withdrawn
        FROM money
        ORDER BY deposited DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message("No records found.")
        return

    text = ""

    for i, (user_id, deposited, withdrawn) in enumerate(rows, start=1):
        member = interaction.guild.get_member(user_id)
        name = member.display_name if member else f"User {user_id}"
        text += f"{i}. {name} - ${deposited:,}\n"

    embed = discord.Embed(
        title="🏆 Gang Contribution Leaderboard",
        description=text
    )

    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)