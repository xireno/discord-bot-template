import discord
from discord.ext import commands

import asyncio  # Make sure asyncio is imported

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='kick', help='Kicks a specific user from the server.')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} has been kicked for {reason}.")

async def setup(bot):
    await bot.add_cog(Kick(bot))
