from discord.ext import commands
import random

class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='roll', help='Rolls a dice with a specified number of sides.')
    async def roll(self, ctx, sides: int):
        result = random.randint(1, sides)
        await ctx.send(f"You rolled a {result} on a {sides}-sided dice.")

async def setup(bot):
    await bot.add_cog(Roll(bot))
