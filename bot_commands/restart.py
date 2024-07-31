import discord
from discord.ext import commands
import logging
import os
import sys
import asyncio

OWNER_ID = 957578507649683457  # Updated owner ID

class Restart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.author.id != OWNER_ID:
            await ctx.send("You do not have permission to use this command.")
            return False
        return True

    @commands.command(name='rs')
    async def restart(self, ctx, target: str):
        """Restart a bot extension, all extensions except main, or the entire bot"""
        if ctx.author.id != OWNER_ID:
            await ctx.send("You do not have permission to use this command.")
            return

        try:
            if target.lower() in ["bot", "main"]:
                await ctx.send("Restarting the bot...")
                logging.info("Restarting the bot...")
                await self.bot.close()
                # Change the working directory to the script's location
                os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
                # Restart the bot process with the correct command
                os.execv(sys.executable, [sys.executable] + sys.argv)
            elif target.lower() == "all":
                await ctx.send("Restarting all extensions except main...")
                logging.info("Restarting all extensions except main...")
                await self.restart_all_extensions_except_main(ctx)
                await ctx.send("All extensions restarted successfully.")
            else:
                await self.bot.unload_extension(f'bot_commands.{target}')
                await self.bot.load_extension(f'bot_commands.{target}')
                await ctx.send(f"Successfully restarted the {target} extension.")
                logging.info(f"Successfully restarted the {target} extension.")
        except Exception as e:
            await ctx.send(f"Failed to restart the {target} extension: {e}")
            logging.error(f"Failed to restart the {target} extension: {e}")

    async def restart_all_extensions_except_main(self, ctx):
        """Restart all extensions except the main bot script"""
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
            'bot_commands.ulearn_command',
            'bot_commands.restart',
            'bot_commands.music'
        ]
        for extension in extensions:
            try:
                await self.bot.unload_extension(extension)
                await self.bot.load_extension(extension)
                logging.info(f"Successfully restarted extension {extension}")
            except Exception as e:
                logging.error(f"Failed to restart extension {extension}: {e}")

async def setup(bot):
    await bot.add_cog(Restart(bot))
