import discord
from discord.ext import commands

class CloneCategory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='cc')
    @commands.has_permissions(manage_channels=True)
    async def clone_category(self, ctx, category_name: str, new_category_name: str):
        """Clones a category and renames it.  用法 !cc <原始類別名稱> <新的類別名稱>"""
        guild = ctx.guild
        category_name = category_name.replace('_', ' ')
        new_category_name = new_category_name.replace('_', ' ')
        category = discord.utils.get(guild.categories, name=category_name)

        if not category:
            await ctx.send(f"Category '{category_name}' not found.")
            return

        # Create the new category
        new_category = await guild.create_category(new_category_name)

        # Clone the channels within the category
        for channel in category.channels:
            if isinstance(channel, discord.TextChannel):
                await new_category.create_text_channel(channel.name, topic=channel.topic, nsfw=channel.nsfw, slowmode_delay=channel.slowmode_delay)
            elif isinstance(channel, discord.VoiceChannel):
                await new_category.create_voice_channel(channel.name, bitrate=channel.bitrate, user_limit=channel.user_limit)
            elif isinstance(channel, discord.StageChannel):
                await new_category.create_stage_channel(channel.name, topic=channel.topic)

        await ctx.send(f"Category '{category_name}' cloned as '{new_category_name}'.")

    @commands.command(name='rc')
    @commands.has_permissions(manage_channels=True)
    async def remove_cloned_category(self, ctx, new_category_name: str):
        """Removes a category and all its channels. 用法 !rc <類別名稱>"""
        guild = ctx.guild
        new_category_name = new_category_name.replace('_', ' ')
        new_category = discord.utils.get(guild.categories, name=new_category_name)

        if not new_category:
            await ctx.send(f"Category '{new_category_name}' not found.")
            return

        # Delete all channels within the category
        for channel in new_category.channels:
            await channel.delete()

        # Delete the category itself
        await new_category.delete()

        await ctx.send(f"Category '{new_category_name}' and all its channels have been removed.")

    @commands.command(name='mc')
    @commands.has_permissions(manage_channels=True)
    async def move_category(self, ctx, category_name: str, position: str, reference_channel_name: str):
        """Moves a category above or below a reference channel. 用法 !mc <要移動的類別> under/above <要置於(往上/往下)的類別>"""
        guild = ctx.guild
        category_name = category_name.replace('_', ' ')
        reference_channel_name = reference_channel_name.replace('_', ' ')
        category = discord.utils.get(guild.categories, name=category_name)
        reference_channel = discord.utils.get(guild.channels, name=reference_channel_name)

        if not category:
            await ctx.send(f"Category '{category_name}' not found.")
            return

        if not reference_channel:
            await ctx.send(f"Reference channel '{reference_channel_name}' not found.")
            return

        # Determine the new position
        if position.lower() == "above":
            new_position = reference_channel.position
        elif position.lower() == "under":
            new_position = reference_channel.position + 1
        else:
            await ctx.send("Invalid position. Use 'above' or 'under'.")
            return

        # Move the channels within the category to the new position
        await category.edit(position=new_position)
        
        # Update positions of the channels in the category
        for i, channel in enumerate(category.channels):
            await channel.edit(position=new_position + i)

        await ctx.send(f"Category '{category_name}' moved to {position} '{reference_channel_name}'.")

async def setup(bot):
    await bot.add_cog(CloneCategory(bot))
