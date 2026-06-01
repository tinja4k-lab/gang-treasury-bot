import discord
from discord.ext import commands
import sqlite3
import os
from datetime import datetime

# 🔐 Token from Render
TOKEN = os.getenv("TOKEN")

# 🔒 Money role ID
MONEY_ROLE_ID = 1510964147100188733

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 📦 DATABASE
conn = sqlite3.connect("gang_money.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS money (
    user_id INTEGER PRIMARY KEY,
    deposited INTEGER DEFAULT 0,
    withdrawn INTEGER DEFAULT 0,
    rolls INTEGER DEFAULT 0
)
""")

# Add rolls column to older databases
try:
    cursor.execute(
        "ALTER TABLE money ADD COLUMN rolls INTEGER DEFAULT 0"
    )
except:
    pass

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


# 🔒 ROLE CHECK
def has_money_role(interaction: discord.Interaction) -> bool:
    return any(
        role.id == MONEY_ROLE_ID
        for role in interaction.user.roles
    )


# 🧾 TRANSACTION LOGGER
def log_transaction(user_id: int, ttype: str, amount: int):
    cursor.execute(
        """
        INSERT INTO transactions
        (user_id, type, amount, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            ttype,
            amount,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    conn.commit()


# 🚀 STARTUP
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"Logged in as {bot.user}")
    except Exception as e:
        print("Sync error:", e)


# 💰 DEPOSIT
@bot.tree.command(
    name="deposit",
    description="Add money to a member's contribution total"
)
async def deposit(
    interaction: discord.Interaction,
    member: discord.Member,
    amount: int
):

    if not has_money_role(interaction):
        await interaction.response.send_message(
            "❌ You need the Money role.",
            ephemeral=True
        )
        return

    cursor.execute(
        "INSERT OR IGNORE INTO money(user_id) VALUES(?)",
        (member.id,)
    )

    cursor.execute(
        """
        UPDATE money
        SET deposited = deposited + ?
        WHERE user_id = ?
        """,
        (amount, member.id)
    )

    conn.commit()

    log_transaction(member.id, "deposit", amount)

    await interaction.response.send_message(
        f"💰 Added ${amount:,} deposit for {member.display_name}"
    )


# 💸 WITHDRAW
@bot.tree.command(
    name="withdraw",
    description="Record money paid out to a member"
)
async def withdraw(
    interaction: discord.Interaction,
    member: discord.Member,
    amount: int
):

    if not has_money_role(interaction):
        await interaction.response.send_message(
            "❌ You need the Money role.",
            ephemeral=True
        )
        return

    cursor.execute(
        "INSERT OR IGNORE INTO money(user_id) VALUES(?)",
        (member.id,)
    )

    cursor.execute(
        """
        UPDATE money
        SET withdrawn = withdrawn + ?
        WHERE user_id = ?
        """,
        (amount, member.id)
    )

    conn.commit()

    log_transaction(member.id, "withdraw", amount)

    await interaction.response.send_message(
        f"💸 Added ${amount:,} withdrawal for {member.display_name}"
    )


# 🎲 ROLL
@bot.tree.command(
    name="roll",
    description="Record dirty money handed into the gang fund"
)
async def roll(
    interaction: discord.Interaction,
    member: discord.Member,
    amount: int
):

    if not has_money_role(interaction):
        await interaction.response.send_message(
            "❌ You need the Money role.",
            ephemeral=True
        )
        return

    cursor.execute(
        "INSERT OR IGNORE INTO money(user_id) VALUES(?)",
        (member.id,)
    )

    cursor.execute(
        """
        UPDATE money
        SET rolls = rolls + ?
        WHERE user_id = ?
        """,
        (amount, member.id)
    )

    conn.commit()

    log_transaction(member.id, "roll", amount)

    await interaction.response.send_message(
        f"🎲 Added ${amount:,} rolls for {member.display_name}"
    )


# 📊 MONEY
@bot.tree.command(
    name="money",
    description="Check a member's gang finances"
)
async def money(
    interaction: discord.Interaction,
    member: discord.Member
):

    if not has_money_role(interaction):
        await interaction.response.send_message(
            "❌ You need the Money role.",
            ephemeral=True
        )
        return

    cursor.execute(
        """
        SELECT deposited, withdrawn, rolls
        FROM money
        WHERE user_id = ?
        """,
        (member.id,)
    )

    data = cursor.fetchone()

    deposited, withdrawn, rolls = (
        data if data else (0, 0, 0)
    )

    net = deposited - withdrawn

    embed = discord.Embed(
        title=f"{member.display_name}'s Gang Finances"
    )

    embed.add_field(
        name="Deposited",
        value=f"${deposited:,}",
        inline=False
    )

    embed.add_field(
        name="Withdrawn",
        value=f"${withdrawn:,}",
        inline=False
    )

    embed.add_field(
        name="Net Contribution",
        value=f"${net:,}",
        inline=False
    )

    embed.add_field(
        name="Rolls Given",
        value=f"${rolls:,}",
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


# 🧾 TRANSACTIONS
@bot.tree.command(
    name="transactions",
    description="View a member's last 10 transactions"
)
async def transactions(
    interaction: discord.Interaction,
    member: discord.Member
):

    if not has_money_role(interaction):
        await interaction.response.send_message(
            "❌ You need the Money role.",
            ephemeral=True
        )
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
        await interaction.response.send_message(
            "No transactions found."
        )
        return

    text = ""

    for ttype, amount, timestamp in rows:

        if ttype == "deposit":
            icon = "💰"
        elif ttype == "withdraw":
            icon = "💸"
        else:
            icon = "🎲"

        text += (
            f"{icon} ${amount:,} | "
            f"{ttype.title()} | "
            f"{timestamp}\n"
        )

    embed = discord.Embed(
        title=f"{member.display_name}'s Transactions",
        description=text
    )

    await interaction.response.send_message(
        embed=embed
    )


# 🏆 CONTRIBUTION LEADERBOARD
@bot.tree.command(
    name="leaderboard",
    description="Top gang contributors"
)
async def leaderboard(interaction: discord.Interaction):

    if not has_money_role(interaction):
        await interaction.response.send_message(
            "❌ You need the Money role.",
            ephemeral=True
        )
        return

    cursor.execute("""
        SELECT user_id,
               deposited,
               withdrawn,
               (deposited - withdrawn) AS net
        FROM money
        ORDER BY net DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message(
            "No records found."
        )
        return

    text = ""

    for i, (user_id, deposited, withdrawn, net) in enumerate(rows, start=1):

        member = interaction.guild.get_member(user_id)

        name = (
            member.display_name
            if member
            else f"User {user_id}"
        )

        text += (
            f"{i}. {name} — "
            f"${net:,} net "
            f"(💰{deposited:,} / 💸{withdrawn:,})\n"
        )

    embed = discord.Embed(
        title="🏆 Gang Contribution Leaderboard",
        description=text
    )

    await interaction.response.send_message(
        embed=embed
    )


# 🎲 ROLL LEADERBOARD
@bot.tree.command(
    name="rollleaderboard",
    description="Top members by rolls handed in"
)
async def rollleaderboard(
    interaction: discord.Interaction
):

    if not has_money_role(interaction):
        await interaction.response.send_message(
            "❌ You need the Money role.",
            ephemeral=True
        )
        return

    cursor.execute("""
        SELECT user_id, rolls
        FROM money
        ORDER BY rolls DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message(
            "No roll records found."
        )
        return

    text = ""

    for i, (user_id, rolls) in enumerate(rows, start=1):

        member = interaction.guild.get_member(user_id)

        name = (
            member.display_name
            if member
            else f"User {user_id}"
        )

        text += f"{i}. {name} — 🎲 ${rolls:,}\n"

    embed = discord.Embed(
        title="🎲 Roll Leaderboard",
        description=text
    )

    await interaction.response.send_message(
        embed=embed
    )


# 🧹 CLEAR
@bot.tree.command(
    name="clear",
    description="Reset a member's deposits, withdrawals and rolls"
)
async def clear(
    interaction: discord.Interaction,
    member: discord.Member
):

    if not has_money_role(interaction):
        await interaction.response.send_message(
            "❌ You need the Money role.",
            ephemeral=True
        )
        return

    cursor.execute(
        """
        UPDATE money
        SET deposited = 0,
            withdrawn = 0,
            rolls = 0
        WHERE user_id = ?
        """,
        (member.id,)
    )

    conn.commit()

    await interaction.response.send_message(
        f"🧹 Reset all records for {member.display_name}"
    )


# ▶️ RUN BOT
bot.run(TOKEN)
