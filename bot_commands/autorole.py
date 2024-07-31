import discord
from discord.ext import commands
import logging
import json
import os

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'auto_role_config.json'
        self.reaction_role_file = 'reaction_roles.json'
        self.bot.auto_role_config = self.load_config(self.config_file)
        self.bot.reaction_roles = self.load_config(self.reaction_role_file)

    def load_config(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                return json.load(file)
        return {}

    def save_config(self, config, filename):
        with open(filename, 'w') as file:
            json.dump(config, file)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        logging.info(f"Member {member.name} joined the server {member.guild.name}.")
        
        role_id = self.bot.auto_role_config.get(str(member.guild.id))
        if not role_id:
            logging.warning("Auto role not set for this server.")
            return
        
        role = member.guild.get_role(role_id)
        if not role:
            logging.error(f"Role ID {role_id} not found in the server {member.guild.name}.")
            return
        
        if not member.guild.me.guild_permissions.manage_roles:
            logging.error("Bot does not have manage_roles permission.")
            return
        
        bot_role = member.guild.me.top_role
        if role >= bot_role:
            logging.error(f"The bot's role '{bot_role.name}' is not high enough to assign '{role.name}'.")
            return
        
        try:
            await member.add_roles(role)
            logging.info(f"Assigned role {role.name} to {member.name}.")
            await member.send(f"Welcome to {member.guild.name}! You have been assigned the role {role.name}.")
        except discord.Forbidden:
            logging.error("Bot does not have permission to assign roles.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    @commands.command(name='setautorole')
    @commands.has_permissions(administrator=True)
    async def set_auto_role(self, ctx, *, role: discord.Role):
        self.bot.auto_role_config[str(ctx.guild.id)] = role.id
        self.save_config(self.bot.auto_role_config, self.config_file)
        await ctx.send(f"Auto-role set to {role.name} for this server.")
        logging.info(f"Auto-role set to {role.name} for the server {ctx.guild.name}.")

    @commands.command(name='setreactionrole')
    @commands.has_permissions(administrator=True)
    async def set_reaction_role(self, ctx, emoji: str, role: discord.Role, message_id: int = None):
        # Determine the target message
        if ctx.message.reference:
            # Get the message being replied to
            target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        elif message_id:
            # Get the message by ID
            target_message = await ctx.channel.fetch_message(message_id)
        else:
            await ctx.send("You need to either reply to a message or provide a message ID.")
            return
        
        if str(ctx.guild.id) not in self.bot.reaction_roles:
            self.bot.reaction_roles[str(ctx.guild.id)] = {}
        
        self.bot.reaction_roles[str(ctx.guild.id)][str(target_message.id)] = {
            "emoji": emoji,
            "role_id": role.id
        }
        self.save_config(self.bot.reaction_roles, self.reaction_role_file)
        
        # Add the emoji to the message
        try:
            # Check if emoji is custom
            if emoji.startswith('<:') and emoji.endswith('>'):
                # Custom emoji
                custom_emoji = discord.PartialEmoji.from_str(emoji)
                await target_message.add_reaction(custom_emoji)
            else:
                # Standard Unicode emoji
                await target_message.add_reaction(emoji)
                
            await ctx.send(f"Reaction role set: React with {emoji} to get {role.name}")
            logging.info(f"Reaction role set for message {target_message.id} with emoji {emoji} to assign role {role.name}.")
        except discord.HTTPException:
            await ctx.send("Failed to add reaction to the message. Make sure the emoji is valid and the bot has access to it.")
            logging.error("Failed to add reaction to the message.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        # Avoid processing reactions added by the bot itself
        if payload.user_id == self.bot.user.id:
            return

        if str(payload.guild_id) in self.bot.reaction_roles:
            if str(payload.message_id) in self.bot.reaction_roles[str(payload.guild_id)]:
                reaction_role = self.bot.reaction_roles[str(payload.guild_id)][str(payload.message_id)]
                if reaction_role["emoji"] == str(payload.emoji):
                    role = guild.get_role(reaction_role["role_id"])
                    if role:
                        member = guild.get_member(payload.user_id)
                        if member:
                            if role in member.roles:
                                # Debugging output
                                logging.info(f"{member.name} already has the {role.name} role. Removing reaction.")
                                
                                # Remove the reaction if the member already has the role
                                channel = guild.get_channel(payload.channel_id)
                                message = await channel.fetch_message(payload.message_id)
                                await message.remove_reaction(payload.emoji, member)
                                logging.info(f"Removed reaction for {member.name} as they already have the {role.name} role.")
                            else:
                                await member.add_roles(role)
                                logging.info(f"Assigned role {role.name} to {member.name} for reacting with {reaction_role['emoji']}.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        if str(payload.guild_id) in self.bot.reaction_roles:
            if str(payload.message_id) in self.bot.reaction_roles[str(payload.guild_id)]:
                reaction_role = self.bot.reaction_roles[str(payload.guild_id)][str(payload.message_id)]
                if reaction_role["emoji"] == str(payload.emoji):
                    role = guild.get_role(reaction_role["role_id"])
                    if role:
                        member = guild.get_member(payload.user_id)
                        if member:
                            await member.remove_roles(role)
                            logging.info(f"Removed role {role.name} from {member.name} for removing reaction {reaction_role['emoji']}.")

async def setup(bot):
    await bot.add_cog(AutoRole(bot))

# Custom logging handler to handle Unicode characters
class UnicodeHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            msg = self.format(record)
            msg = msg.encode('utf-8', errors='replace').decode('ascii', errors='replace')
            stream.write(msg + self.terminator)
            self.flush()

# Configure logging with UTF-8 encoding
file_handler = logging.FileHandler('bot.log', encoding='utf-8')
console_handler = UnicodeHandler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[console_handler, file_handler]
)

# Ensure the console handler uses UTF-8 encoding
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.stream = open(handler.stream.fileno(), 'w', encoding='utf-8', closefd=False)
