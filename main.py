import os
import logging
from dotenv import load_dotenv
from discord.ext import commands
import discord

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if not TOKEN:
    raise ValueError("No token found in the environment variables. Ensure the .env file is set correctly.")

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for member join events

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s:%(message)s',
                    handlers=[
                        logging.FileHandler("bot.log"),
                        logging.StreamHandler()
                    ])

# List of extensions to load
extensions = [
    'bot_commands.paginated_help',
    'bot_commands.ping',
    'bot_commands.userinfo',
    'bot_commands.serverinfo',
    'bot_commands.mute',
    'bot_commands.unmute',
    'bot_commands.kick',
    'bot_commands.ban',
    'bot_commands.unban',
    'bot_commands.clear',
    'bot_commands.roll',  
    'bot_commands.clone_category',
    'bot_commands.restart',
    'bot_commands.music',
    'bot_commands.translate',
    'bot_commands.autorole'
]

# Function to load extensions
async def load_extensions():
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logging.info(f"Loaded extension {extension}")
        except Exception as e:
            logging.error(f"Failed to load extension {extension}: {e}")

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    await load_extensions()

@bot.event
async def on_connect():
    logging.info("Bot connected.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param}")
    else:
        await ctx.send("An error occurred.")
        logging.error(f"An error occurred: {error}")

# Run the bot
bot.run(TOKEN)
