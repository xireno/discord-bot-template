import discord
from discord.ext import commands

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='clear', help='Clears a specified amount of messages. 用法 !clear <數量>')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        if amount <= 0:
            await ctx.send("Please specify a positive number of messages to delete.")
            return
        
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to also delete the command message
        await ctx.send(f"Cleared {len(deleted) - 1} messages.", delete_after=5)

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the number of messages to delete, e.g., `!clear 5`.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid number.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")
        else:
            await ctx.send("An error occurred while trying to clear messages.")

async def setup(bot):
    await bot.add_cog(Clear(bot))
