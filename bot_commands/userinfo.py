import discord
from discord.ext import commands

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='userinfo', help='Provides information about a specific user.')
    async def userinfo(self, ctx, member: discord.Member):
        embed = discord.Embed(title=f"User Info - {member.name}", color=discord.Color.green())
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Display Name", value=member.display_name, inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%m/%d/%Y, %H:%M:%S"), inline=False)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%m/%d/%Y, %H:%M:%S"), inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserInfo(bot))
