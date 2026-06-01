import discord
from discord.ext import commands
import sqlite3
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")

MONEY_ROLE_ID = 1510964147100188733

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# DATABASE
# -------------------------
conn = sqlite3.connect("gang_money.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS money (
    user_id INTEGER PRIMARY KEY,
    deposited INTEGER DEFAULT 0,
    withdrawn INTEGER DEFAULT 0
)
""")

# NEW TABLE: transactions
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    amount INTEGER,
    timestamp TEXT
)
""")

conn.commit()


# -------------------------
# ROLE CHECK
# -------------------------
def has_money_role(interaction: discord.Interaction) -> bool:
    return any(role.id == MONEY_ROLE_ID for role in interaction.user.roles)


# -------------------------
# SYNC
# -------------------------
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"Logged in as {bot.user}")
    except Exception as e:
        print("Sync error:", e)


# -------------------------
# LOG TRANSACTION FUNCTION
# -------------------------
def log_transaction(user_id: int, ttype: str, amount: int):
    cursor.execute(
        "INSERT INTO transactions (user_id, type, amount, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, ttype, amount, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()


# -------------------------
# DEPOSIT
# -------------------------
@bot.tree.command(name="deposit", description="Add money to a member")
async def deposit(interaction: discord.Interaction, member: discord.Member, amount: int):

    if not has_money_role(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    cursor.execute("INSERT OR IGNORE INTO money(user_id) VALUES(?)", (member.id,))
    cursor.execute("UPDATE money SET deposited = deposited + ? WHERE user_id = ?", (amount, member.id))
    conn.commit()

    log_transaction(member.id, "deposit", amount)

    await interaction.response.send_message(f"✅ Deposited ${amount:,} for {member.display_name}")


# -------------------------
# WITHDRAW
# -------------------------
@bot.tree.command(name="withdraw", description="Record withdrawal")
async def withdraw(interaction: discord.Interaction, member: discord.Member, amount: int):

    if not has_money_role(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    cursor.execute("INSERT OR IGNORE INTO money(user_id) VALUES(?)", (member.id,))
    cursor.execute("UPDATE money SET withdrawn = withdrawn + ? WHERE user_id = ?", (amount, member.id))
    conn.commit()

    log_transaction(member.id, "withdraw", amount)

    await interaction.response.send_message(f"💸 Withdrawn ${amount:,} for {member.display_name}")


# -------------------------
# TRANSACTIONS COMMAND (NEW)
# -------------------------
@bot.tree.command(name="transactions", description="View a user's transaction history")
async def transactions(interaction: discord.Interaction, member: discord.Member):

    if not has_money_role(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    cursor.execute("""
        SELECT type, amount, timestamp
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (member.id,))

    rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message("No transactions found.")
        return

    text = ""
    for ttype, amount, time in rows:
        icon = "💰" if ttype == "deposit" else "💸"
        text += f"{icon} ${amount:,} | {ttype} | {time}\n"

    embed = discord.Embed(
        title=f"{member.display_name}'s Transactions",
        description=text
    )

    await interaction.response.send_message(embed=embed)


# -------------------------
# MONEY CHECK
# -------------------------
@bot.tree.command(name="money", description="Check finances")
async def money(interaction: discord.Interaction, member: discord.Member):

    if not has_money_role(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    cursor.execute("SELECT deposited, withdrawn FROM money WHERE user_id = ?", (member.id,))
    data = cursor.fetchone()
    deposited, withdrawn = data if data else (0, 0)

    net = deposited - withdrawn

    embed = discord.Embed(title=f"{member.display_name}'s Finances")
    embed.add_field(name="Deposited", value=f"${deposited:,}", inline=False)
    embed.add_field(name="Withdrawn", value=f"${withdrawn:,}", inline=False)
    embed.add_field(name="Net", value=f"${net:,}", inline=False)

    await interaction.response.send_message(embed=embed)


# -------------------------
# CLEAR
# -------------------------
@bot.tree.command(name="clear", description="Reset user data")
async def clear(interaction: discord.Interaction, member: discord.Member):

    if not has_money_role(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    cursor.execute("UPDATE money SET deposited = 0, withdrawn = 0 WHERE user_id = ?", (member.id,))
    conn.commit()

    await interaction.response.send_message(f"🧹 Reset {member.display_name}")


bot.run(TOKEN)
