import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db import Database
from process_message import process_message
from discord import app_commands
from datetime import datetime
import pytz


load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
db = Database()


def print_message(message, score):
    # Console stuff
    truncated_content = message.content[:30]
    if len(message.content) > 30:
        truncated_content += "..."

    score_display = f"{'+' if score > 0 else ''}{score}"

    author_color = f"\033[1m\033[38;2;{message.author.color.r};{message.author.color.g};{message.author.color.b}m"
    reset_color = "\033[0m"
    colored_author = f"{author_color}{message.author.name}{reset_color}"

    print(f'{colored_author}: "{truncated_content}" ({score_display})')

    # Discord stuff
    logging_channel = os.getenv("UPDATE_CHANNEL_ID")
    if logging_channel:
        try:
            channel = bot.get_channel(int(logging_channel))
            if channel and channel.guild.id == message.guild.id:
                # Create embed with message details
                if score > 0:
                    title = "🎉 Citizen Upholds Socialist Values!"
                elif score < 0:
                    title = "🚨 Citizen Loses Rights!"
                else:
                    title = "😐 Citizen Remains Unremarkable."

                embed = discord.Embed(
                    title=title,
                    color=(
                        0xA6D189 if score > 0 else 0xE78284 if score < 0 else 0xE5C890
                    ),
                )

                embed.add_field(name="User", value=message.author.mention, inline=True)

                embed.add_field(
                    name="Score Change",
                    value=f"{'+' if score > 0 else ''}{score}",
                    inline=True,
                )

                embed.add_field(
                    name="Message", value=f'"{truncated_content}"', inline=False
                )

                embed.set_thumbnail(url=message.author.avatar.url)

                # Send the embed (this needs to be async)
                asyncio.create_task(channel.send(embed=embed))
        except ValueError:
            print(f"Invalid UPDATE_CHANNEL_ID: {logging_channel}")
        except Exception as e:
            print(f"Error sending embed: {e}")


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    print(f"Bot is in {len(bot.guilds)} guilds")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message):
    # Don't log messages from the bot itself
    if message.author == bot.user:
        return

    score = process_message(message.content, db)
    print_message(message, score)

    db.update_social_credit(message.author.id, message.guild.id, score)

    # Process commands (important for slash commands to work)
    await bot.process_commands(message)


# Slash command: /leaderboard
@bot.tree.command(name="leaderboard", description="Display the leaderboard")
async def leaderboard(interaction: discord.Interaction):
    server_data = db.get_social_credit_server(interaction.guild.id)

    # Sort users by credit amount (highest to lowest)
    sorted_users = sorted(
        server_data, key=lambda x: x.get("credit_amount", 0), reverse=True
    )

    embed = discord.Embed(
        title="🏆 Social Credit Leaderboard 🏆",
        description="User rankings based on social credit points",
        color=0xE5C890,
    )

    # Add users with positive or zero points
    positive_users = [
        user for user in sorted_users if user.get("credit_amount", 0) >= 0
    ]
    if positive_users:
        positive_list = ""
        for i, user in enumerate(positive_users, 1):
            user_id = user.get("id")
            credit = user.get("credit_amount", 0)
            # Try to get the member object using the correct user ID
            member = interaction.guild.get_member(int(user_id))
            # Use member's display name or fallback to mentioning the user
            username = member.display_name if member else f"<@{user_id}>"
            positive_list += f"**{i}.** {username}: **{credit}** points\n"

        embed.add_field(name="Behaved Citizens", value=positive_list, inline=False)

    # Add divider and negative users section
    negative_users = [user for user in sorted_users if user.get("credit_amount", 0) < 0]
    if negative_users:

        # Add negative users list
        negative_list = ""
        for i, user in enumerate(negative_users, 1):
            user_id = user.get("id")
            credit = user.get("credit_amount", 0)
            # Try to get the member object using the correct user ID
            member = interaction.guild.get_member(int(user_id))
            # Use member's display name or fallback to mentioning the user
            username = member.display_name if member else f"<@{user_id}>"
            negative_list += f"**{i}.** {username}: **{credit}** points\n"

        embed.add_field(
            name="Untrustworthy Citizens",
            value=negative_list,
            inline=False,
        )

    embed.set_footer(text="Be a good citizen to earn more social credit points!")

    await interaction.response.send_message(embed=embed)


# Slash command: /set-timezone
@bot.tree.command(name="set-timezone", description="Set your timezone")
@app_commands.describe(
    timezone="Your timezone (e.g., 'America/New_York', 'Europe/London')"
)
async def set_timezone(interaction: discord.Interaction, timezone: str):

    try:
        db.update_timezone(interaction.user.id, interaction.guild.id, timezone)
    except ValueError:
        await interaction.response.send_message(
            f'"{timezone}" is not a valid timezone. Please enter your timezone in [IANA format](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).',
            ephemeral=True,
        )
        return

    target_obj = pytz.timezone(timezone)

    await interaction.response.send_message(
        f"Your timezone has been set to: **{timezone}** ({datetime.now(target_obj)})",
        ephemeral=True,
    )


@bot.tree.command(name="time", description="View the time for server members")
async def time(interaction: discord.Interaction):
    server_data = db.get_social_credit_server(interaction.guild.id)

    embed = discord.Embed(
        title="⏰ Server Member Times ⏰",
        description="Current local time for server members (set with /set-timezone)",
        color=0xE5C890,
    )

    contents = ""

    for user in server_data:
        user_id = user.get("id")
        timezone = user.get("timezone")
        username = f"<@{user_id}>"

        if timezone and timezone in pytz.all_timezones:
            now = datetime.now(pytz.timezone(timezone))
            time_str = now.strftime("%B %-d %Y, %I:%M %p")
            contents += f"{username}: **{time_str}** ({timezone})\n"

    embed.add_field(name="Times", inline=False, value=contents)
    await interaction.response.send_message(embed=embed)


# Slash command: /force-set-timezone
@bot.tree.command(name="force-set-timezone", description="Admin: Set a user's timezone")
@app_commands.describe(
    user="The user to set the timezone for",
    timezone="Timezone in IANA format (e.g., 'America/New_York')",
)
@app_commands.checks.has_permissions(administrator=True)
async def force_set_timezone(
    interaction: discord.Interaction, user: discord.Member, timezone: str
):
    # Only allow admins to use this command
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    try:
        db.update_timezone(user.id, interaction.guild.id, timezone)
    except ValueError:
        await interaction.response.send_message(
            f'"{timezone}" is not a valid timezone. Please enter your timezone in [IANA format](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).',
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"Timezone for {user.mention} has been set to **{timezone}**.",
        ephemeral=True,
    )


# Run the bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables!")
        print("Please add your bot token to the .env file")
    else:
        bot.run(token)
