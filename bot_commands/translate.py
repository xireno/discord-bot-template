import discord
from discord.ext import commands
from discord import ui, Interaction
import opencc
from googletrans import Translator

# In-memory dictionary to store user language settings
user_language_settings = {}

class LanguageSelect(ui.Select):
    def __init__(self, user_id):
        self.user_id = user_id
        options = [
            discord.SelectOption(label="簡體中文", value="zh-CN", description="翻譯成簡體中文"),
            discord.SelectOption(label="繁體中文", value="zh-TW", description="翻譯成繁體中文"),
            discord.SelectOption(label="英文", value="en", description="翻譯成英文"),
            discord.SelectOption(label="西班牙文", value="es", description="翻譯成西班牙文"),
            discord.SelectOption(label="韓文", value="ko", description="翻譯成韓文")
        ]
        super().__init__(placeholder="選擇您的語言...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        language = self.values[0]
        user_language_settings[self.user_id] = language
        await interaction.response.send_message(f"語言設定已更新為 {self.values[0]}!", ephemeral=True)

class TranslateSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='trsetting')
    async def trsetting(self, ctx):
        embed = discord.Embed(title="翻譯設定", description="選擇您偏好的翻譯語言。")
        view = ui.View()
        view.add_item(LanguageSelect(ctx.author.id))
        await ctx.send(embed=embed, view=view)

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()
        self.cc_t2s = opencc.OpenCC('t2s')
        self.cc_s2t = opencc.OpenCC('s2t')

    @commands.command(name='trans')
    async def translate_text(self, ctx, *, text: str):
        user_id = ctx.author.id
        target_language = user_language_settings.get(user_id, 'en')

        if target_language == 'zh-CN':
            translated_text = self.cc_t2s.convert(text)
        elif target_language == 'zh-TW':
            translated_text = self.cc_s2t.convert(text)
        else:
            translated_text = self.translator.translate(text, dest=target_language).text

        await ctx.send(translated_text)

async def setup(bot):
    await bot.add_cog(TranslateSettings(bot))
    await bot.add_cog(Translate(bot))
