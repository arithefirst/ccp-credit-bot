import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db import Database

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

    print(f"User ID: {message.author.id}")
    print(f"Guild: {message.guild.name if message.guild else 'DM'}")
    print(f"Message: {message.content}")

    # Process commands (important for slash commands to work)
    await bot.process_commands(message)


# Slash command: /leaderboard
@bot.tree.command(name="leaderboard", description="Display the leaderboard")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🏆 Leaderboard command executed! Check the console for details."
    )


# Run the bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables!")
        print("Please add your bot token to the .env file")
    else:
        bot.run(token)
