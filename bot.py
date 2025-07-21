import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db import Database
from process_message import process_message

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
db = Database()


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
    print(f"{message.author.name}: {'+' if score > 0 else ''}{score}")
    db.update_social_credit(message.author.id, message.guild.id, score)

    # Process commands (important for slash commands to work)
    await bot.process_commands(message)


# Slash command: /leaderboard
@bot.tree.command(name="leaderboard", description="Display the leaderboard")
async def leaderboard(interaction: discord.Interaction):
    # Get all users from this server
    server_data = db.get_social_credit_server(interaction.guild.id)

    # Sort users by credit amount (highest to lowest)
    sorted_users = sorted(
        server_data, key=lambda x: x.get("credit_amount", 0), reverse=True
    )

    # Create the embed with yellow color (#FFFF08)
    embed = discord.Embed(
        title="🏆 Social Credit Leaderboard 🏆",
        description="User rankings based on social credit points",
        color=0xFFFF08,  # Yellow color in hex as requested
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

        # Add the negative list to the embed - this line was missing
        embed.add_field(
            name="Untrustworthy Citizens",
            value=negative_list,
            inline=False,
        )

    embed.set_footer(text="Be a good citizen to earn more social credit points!")

    await interaction.response.send_message(embed=embed)


# Run the bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables!")
        print("Please add your bot token to the .env file")
    else:
        bot.run(token)
