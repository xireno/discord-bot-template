import discord
from discord.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='serverinfo', help='Provides information about the server.')
    async def serverinfo(self, ctx):
        guild = ctx.guild
        owner = await guild.fetch_member(guild.owner_id)  # Fetch the owner using the owner_id

        embed = discord.Embed(title=f"Server Info - {guild.name}", color=discord.Color.blue())
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=str(owner), inline=True)  # Convert owner to string to display name
        embed.add_field(name="Voice Region", value=guild.preferred_locale, inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%m/%d/%Y, %H:%M:%S"), inline=False)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
