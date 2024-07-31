import discord
from discord.ext import commands

class PaginatedHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    @commands.command(name='help')
    async def help_command(self, ctx):
        pages = self.generate_help_pages()
        message = await ctx.send(embed=pages[0], view=HelpView(pages))

    def generate_help_pages(self):
        pages = []
        page_layouts = [
            ['roll', 'ping', 'userinfo'],
            ['serverinfo', 'mute', 'unmute'],
            ['kick', 'ban', 'unban'],
            ['clear', 'cc', 'rc', 'mc'],
            ['play', 'skip', 'stop','addqueue','pause','resume']
        ]

        for layout in page_layouts:
            embed = discord.Embed(
                title="Help",
                description="List of available commands",
                color=discord.Color.from_rgb(54, 57, 63)
            )
            embed.set_thumbnail(url="https://example.com/thumbnail.png")  # Adjust the URL as needed
            embed.set_footer(text=f"Page {len(pages) + 1}")
            embed.timestamp = discord.utils.utcnow()

            for command_name in layout:
                command = self.bot.get_command(command_name)
                if command:
                    embed.add_field(
                        name=f'!{command.name}',
                        value=command.help or "No description provided.",
                        inline=False
                    )

            pages.append(embed)

        return pages

class HelpView(discord.ui.View):
    def __init__(self, pages):
        super().__init__()
        self.pages = pages
        self.current_page = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

async def setup(bot):
    await bot.add_cog(PaginatedHelp(bot))
