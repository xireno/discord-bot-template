import discord
from discord.ext import commands

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='mute', help='Mutes a specific user.')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        await member.add_roles(mute_role)
        await ctx.send(f"{member.mention} has been muted.")

async def setup(bot):
    await bot.add_cog(Mute(bot))
