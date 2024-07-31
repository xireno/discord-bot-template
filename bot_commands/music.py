import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Modal, TextInput
import yt_dlp
import shutil
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from fake_useragent import UserAgent
import re
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_states = {}  # Dictionary to hold the state for each guild
        self.ffmpeg_path = shutil.which("ffmpeg") or r'C:\\Program Files\\ffmpeg-7.0.1-essentials_build\\ffmpeg-7.0.1-essentials_build\\bin\\ffmpeg.exe'
        logging.info("Music Cog initialized")

        self.update_embed_task.start()

    def cog_unload(self):
        self.update_embed_task.cancel()

    def get_guild_state(self, guild_id):
        """Get the state for the specified guild."""
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = {
                'is_playing': False,
                'is_paused': False,
                'current_channel': None,
                'queue': [],
                'current_song': None,
                'embed_message': None,
                'embed_update_pending': False,
                'song_start_time': None,
                'song_duration': 0,
                'paused_time': None,
                'elapsed_paused_time': 0,
            }
        return self.guild_states[guild_id]

    @tasks.loop(seconds=10.0)
    async def update_embed_task(self):
        for guild_id in self.guild_states:
            guild_state = self.get_guild_state(guild_id)
            if guild_state['is_playing'] and guild_state['embed_message']:
                await self.update_progress_bar(guild_id)

    async def update_progress_bar(self, guild_id):
        guild_state = self.get_guild_state(guild_id)
        progress, elapsed_time, total_time = self.get_song_progress(guild_id)
        progress_bar = self.format_progress_bar(progress)

        embed = discord.Embed(
            title="🎶 Music Controls 🎶", 
            description=f"**Now playing:** `{guild_state['current_song'] if guild_state['current_song'] else 'None'}`", 
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="Progress", 
            value=f"`{self.format_time(elapsed_time)}` {progress_bar} `{self.format_time(total_time)}`", 
            inline=False
        )

        if guild_state['queue']:
            queue_list = "\n".join([f"{i+1}. {title}" for i, (_, title, _) in enumerate(guild_state['queue'])])
            embed.add_field(name="📜 Queue", value=queue_list, inline=False)
        else:
            embed.add_field(name="📜 Queue", value="No songs in queue.", inline=False)

        embed.set_footer(text="Use the buttons below to control the music.")

        if guild_state['embed_message']:
            try:
                # Edit the existing embed message
                await guild_state['embed_message'].edit(embed=embed)
                logging.info("Updated progress bar in existing embed")
            except discord.errors.NotFound:
                logging.error("Embed message not found. It might have been deleted.")
                guild_state['embed_message'] = None

    def is_valid_spotify_url(self, url: str) -> bool:
        """Check if the given URL is a valid Spotify track URL."""
        return re.match(r'https?://open\.spotify\.com/track/[a-zA-Z0-9]+', url) is not None

    @commands.command(name="play", help="Plays a song from a YouTube or Spotify URL, or shows the current queue if no URL is provided")
    async def play(self, ctx, url: str = None):
        logging.info(f"Play command invoked with URL: {url}")
        
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)

        if url is None:
            await self.send_or_update_embed(ctx)
            return

        if 'spotify' in url and not self.is_valid_spotify_url(url):
            await ctx.send("Invalid Spotify URL. Please provide a valid Spotify track URL.")
            logging.warning("Invalid Spotify URL provided")
            return

        guild_state['current_channel'] = ctx.author.voice.channel
        if not guild_state['current_channel']:
            await ctx.send("You need to be in a voice channel to play music.")
            logging.warning("User not in a voice channel")
            return

        await self.join(ctx)
        
        if 'spotify' in url:
            await self.process_spotify_url(ctx, url)
        else:
            await self.process_url(ctx, url)
        
        await self.send_or_update_embed(ctx)

    async def fetch_spotify_track_info(self, url: str):
        def fetch_info():
            ua = UserAgent()
            headers = {
                "User-Agent": ua.random
            }
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Status code {response.status_code}")

            soup = BeautifulSoup(response.content, 'html.parser')

            # Attempt to extract the song title and artist name
            track_title_meta = soup.find('meta', property='og:title')
            track_artist_meta = soup.find('meta', property='og:description')

            track_title = track_title_meta['content'] if track_title_meta else None
            track_artist = track_artist_meta['content'].split(' · ')[0] if track_artist_meta else None

            if not track_title or not track_artist:
                if not track_title:
                    track_title = soup.title.string if soup.title else None
                if not track_artist:
                    possible_artist_selectors = [
                        'meta[property="music:musician"]',
                        'meta[name="twitter:audio:artist_name"]',
                        'meta[property="og:audio:artist"]',
                        'div.creator-name',
                        'span[data-testid="creator-link"]',
                        'a[href*="/artist/"]'
                    ]
                    for selector in possible_artist_selectors:
                        artist_tag = soup.select_one(selector)
                        if artist_tag:
                            track_artist = artist_tag.get('content') or artist_tag.text.strip()
                            if track_artist:
                                break
                if not track_title or not track_artist:
                    raise Exception("Title or artist not found")

            return f"{track_title} {track_artist}"

        max_retries = 10
        for attempt in range(max_retries):
            try:
                return await asyncio.to_thread(fetch_info)
            except Exception as e:
                logging.error(f"Encountered error: {str(e)}. Retrying: {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to fetch Spotify track information after {max_retries} retries: {str(e)}")

    async def process_spotify_url(self, ctx, url: str):
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)
        
        if 'track' in url:
            try:
                track_info = await self.fetch_spotify_track_info(url)
                youtube_url = await self.search_youtube(track_info)
                await self.process_url(ctx, youtube_url)
            except Exception as e:
                await ctx.send(f"An error occurred while processing the Spotify URL: {str(e)}")
                logging.error(f"An error occurred while processing the Spotify URL: {str(e)}")
        else:
            await ctx.send("Invalid Spotify URL. Only track URLs are supported.")

    async def search_youtube(self, query: str):
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch',
            'extract_flat': 'in_playlist'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, query, download=False)
            video_url = f"https://www.youtube.com/watch?v={info['entries'][0]['id']}"
            return video_url

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)

        if guild_state['queue']:
            guild_state['is_playing'] = True
            guild_state['is_paused'] = False
            guild_state['paused_time'] = None
            guild_state['elapsed_paused_time'] = 0
            source, guild_state['current_song'], guild_state['song_duration'] = guild_state['queue'].pop(0)
            guild_state['song_start_time'] = datetime.utcnow()
            ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            logging.info(f"Playing next song: {guild_state['current_song']}")
            await self.send_or_update_embed(ctx)
        else:
            guild_state['is_playing'] = False
            guild_state['current_song'] = None
            guild_state['song_start_time'] = None
            await ctx.send("Queue is empty, no more songs to play.")
            logging.info("Queue is empty")
            await self.send_or_update_embed(ctx)

    async def join(self, ctx):
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
            logging.info(f"Bot joined {ctx.author.voice.channel}")

    @commands.command(name="pause", help="Pauses the current song")
    async def pause(self, ctx):
        logging.info("Pause command invoked")
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)

        if ctx.voice_client is None:
            await ctx.send("Bot is not connected to a voice channel.")
            logging.warning("Bot not connected to a voice channel")
            return

        if guild_state['is_playing'] and not guild_state['is_paused']:
            ctx.voice_client.pause()
            guild_state['is_paused'] = True
            guild_state['is_playing'] = False
            guild_state['paused_time'] = datetime.utcnow()
            await ctx.send("Paused the song.")
            logging.info("Song paused")
        else:
            await ctx.send("No song is currently playing or song is already paused.")
            logging.warning("No song is playing or song already paused")

        await self.send_or_update_embed(ctx)

    @commands.command(name="resume", help="Resumes the paused song")
    async def resume(self, ctx):
        logging.info("Resume command invoked")
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)

        if ctx.voice_client is None:
            await ctx.send("Bot is not connected to a voice channel.")
            logging.warning("Bot not connected to a voice channel")
            return

        if guild_state['is_paused']:
            ctx.voice_client.resume()
            guild_state['is_paused'] = False
            guild_state['is_playing'] = True
            if guild_state['paused_time']:
                guild_state['elapsed_paused_time'] += (datetime.utcnow() - guild_state['paused_time']).total_seconds()
            await ctx.send("Resumed the song.")
            logging.info("Song resumed")
        else:
            await ctx.send("No song is currently paused.")
            logging.warning("No song is paused")

        await self.send_or_update_embed(ctx)

    @commands.command(name="skip", help="Skips the current song")
    async def skip(self, ctx):
        logging.info("Skip command invoked")
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)

        if ctx.voice_client is None:
            await ctx.send("Bot is not connected to a voice channel.")
            logging.warning("Bot not connected to a voice channel")
            return

        if guild_state['is_playing'] or guild_state['is_paused']:
            ctx.voice_client.stop()
            await ctx.send("Skipped the song.")
            logging.info("Song skipped")
        else:
            await ctx.send("No song is currently playing.")
            logging.warning("No song is playing")

        await self.send_or_update_embed(ctx)

    @commands.command(name="stop", help="Stops the current song and clears the queue")
    async def stop(self, ctx):
        logging.info("Stop command invoked")
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)

        if ctx.voice_client is None:
            await ctx.send("Bot is not connected to a voice channel.")
            logging.warning("Bot not connected to a voice channel")
            return

        if guild_state['is_playing'] or guild_state['is_paused']:
            ctx.voice_client.stop()
            guild_state['is_playing'] = False
            guild_state['is_paused'] = False
            guild_state['queue'] = []
            guild_state['current_song'] = None
            guild_state['song_start_time'] = None
            guild_state['paused_time'] = None
            guild_state['elapsed_paused_time'] = 0
            await ctx.send("Stopped the song and cleared the queue.")
            logging.info("Stopped the song and cleared the queue")
        else:
            await ctx.send("No song is currently playing.")
            logging.warning("No song is playing")

        await self.send_or_update_embed(ctx)

    @commands.command(name="leave", help="Leaves the voice channel and clears the queue")
    async def leave(self, ctx):
        logging.info("Leave command invoked")
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)

        if ctx.voice_client is None:
            await ctx.send("Bot is not connected to a voice channel.")
            logging.warning("Bot not connected to a voice channel")
            return

        await ctx.voice_client.disconnect()
        guild_state['is_playing'] = False
        guild_state['is_paused'] = False
        guild_state['queue'] = []
        guild_state['current_song'] = None
        guild_state['song_start_time'] = None
        guild_state['paused_time'] = None
        guild_state['elapsed_paused_time'] = 0
        await ctx.send("Disconnected from the voice channel and cleared the queue.")
        logging.info("Disconnected from the voice channel and cleared the queue")

        await self.send_or_update_embed(ctx)

    @commands.command(name="addlist", help="Adds multiple songs to the queue from a list of YouTube URLs")
    async def addlist(self, ctx, *, urls: str):
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)

        url_list = urls.split()  # Split the input string by spaces to get individual URLs
        successful_adds = []
        failed_adds = []

        # Ensure the bot is connected to a voice channel before adding songs
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                logging.info(f"Bot joined {ctx.author.voice.channel}")
            else:
                await ctx.send("You need to be in a voice channel to add songs to the queue.")
                logging.warning("User not in a voice channel")
                return

        for url in url_list:
            try:
                await self.process_url(ctx, url)
                successful_adds.append(url)
            except Exception as e:
                logging.error(f"Error adding URL {url}: {e}")
                failed_adds.append(url)
        
        await ctx.send(f"Successfully added: {', '.join(successful_adds)}")
        if failed_adds:
            await ctx.send(f"Failed to add: {', '.join(failed_adds)}")

        await self.send_or_update_embed(ctx)

    async def process_url(self, ctx, url):
        guild_id = ctx.guild.id
        guild_state = self.get_guild_state(guild_id)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'noplaylist': False,  # Allow playlist extraction
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            except Exception as e:
                await ctx.send(f"An error occurred while processing the URL: {str(e)}")
                logging.error(f"An error occurred while processing the URL: {str(e)}")
                return
            
            if 'entries' in info:  # This means the URL is a playlist
                for entry in info['entries']:
                    try:
                        audio_url = entry['url']
                        song_title = entry.get('title', 'Unknown Title')
                        duration = entry.get('duration', 0)  # duration in seconds

                        ffmpeg_options = {
                            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                            'options': '-vn',
                        }
                        source = await asyncio.to_thread(discord.FFmpegPCMAudio, audio_url, executable=self.ffmpeg_path, **ffmpeg_options)

                        if guild_state['is_playing'] or guild_state['is_paused']:
                            guild_state['queue'].append((source, song_title, duration))
                        else:
                            guild_state['current_song'] = song_title
                            guild_state['song_duration'] = duration
                            guild_state['song_start_time'] = datetime.utcnow()
                            guild_state['is_playing'] = True
                            ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                            await self.send_or_update_embed(ctx)
                    except Exception as e:
                        logging.error(f"An error occurred while processing the entry: {str(e)}")
                        continue
            else:
                try:
                    audio_url = info['url']
                    song_title = info.get('title', 'Unknown Title')
                    duration = info.get('duration', 0)  # duration in seconds

                    ffmpeg_options = {
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        'options': '-vn',
                    }
                    source = await asyncio.to_thread(discord.FFmpegPCMAudio, audio_url, executable=self.ffmpeg_path, **ffmpeg_options)

                    if guild_state['is_playing'] or guild_state['is_paused']:
                        guild_state['queue'].append((source, song_title, duration))
                    else:
                        guild_state['current_song'] = song_title
                        guild_state['song_duration'] = duration
                        guild_state['song_start_time'] = datetime.utcnow()
                        guild_state['is_playing'] = True
                        ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                        await self.send_or_update_embed(ctx)
                except Exception as e:
                    await ctx.send(f"An error occurred while processing the URL: {str(e)}")
                    logging.error(f"An error occurred while processing the URL: {str(e)}")

    def get_song_progress(self, guild_id):
        guild_state = self.get_guild_state(guild_id)
        if guild_state['song_start_time'] and guild_state['song_duration'] > 0:
            elapsed_time = (datetime.utcnow() - guild_state['song_start_time']).total_seconds() - guild_state['elapsed_paused_time']
            progress = min(elapsed_time / guild_state['song_duration'], 1.0)
            return progress, elapsed_time, guild_state['song_duration']
        return 0, 0, 0

    def format_progress_bar(self, progress):
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        return bar

    def format_time(self, seconds):
        return str(timedelta(seconds=int(seconds)))

    async def send_or_update_embed(self, ctx_or_interaction):
        guild_id = ctx_or_interaction.guild.id
        guild_state = self.get_guild_state(guild_id)

        if guild_state['embed_update_pending']:
            return

        guild_state['embed_update_pending'] = True

        progress, elapsed_time, total_time = self.get_song_progress(guild_id)
        progress_bar = self.format_progress_bar(progress)

        embed = discord.Embed(
            title="🎶 Music Controls 🎶", 
            description=f"**Now playing:** `{guild_state['current_song'] if guild_state['current_song'] else 'None'}`", 
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="Progress", 
            value=f"`{self.format_time(elapsed_time)}` {progress_bar} `{self.format_time(total_time)}`", 
            inline=False
        )

        if guild_state['queue']:
            queue_list = "\n".join([f"{i+1}. {title}" for i, (_, title, _) in enumerate(guild_state['queue'])])
            embed.add_field(name="📜 Queue", value=queue_list, inline=False)
        else:
            embed.add_field(name="📜 Queue", value="No songs in queue.", inline=False)

        embed.set_footer(text="Use the buttons below to control the music.")

        view = MusicControlView(self)

        # If embed_message exists, delete it and then send a new one
        if guild_state['embed_message']:
            try:
                await guild_state['embed_message'].delete()
            except discord.NotFound:
                pass

        if isinstance(ctx_or_interaction, discord.ext.commands.Context):
            guild_state['embed_message'] = await ctx_or_interaction.send(embed=embed, view=view)
            logging.info("Sent new music controls embed")
        elif isinstance(ctx_or_interaction, discord.Interaction):
            guild_state['embed_message'] = await ctx_or_interaction.followup.send(embed=embed, view=view)
            logging.info("Sent new music controls embed via interaction")

        guild_state['embed_update_pending'] = False

    async def pause_interaction(self, interaction: discord.Interaction):
        logging.info("Pause interaction invoked")
        guild_id = interaction.guild.id
        guild_state = self.get_guild_state(guild_id)

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await interaction.response.send_message("Bot is not connected to a voice channel.", ephemeral=True)
            logging.warning("Bot not connected to a voice channel")
            return

        if guild_state['is_playing'] and not guild_state['is_paused']:
            voice_client.pause()
            guild_state['is_paused'] = True
            guild_state['is_playing'] = False
            guild_state['paused_time'] = datetime.utcnow()
            await interaction.response.send_message("Paused the song.", ephemeral=True)
            logging.info("Paused the song via interaction")
        else:
            await interaction.response.send_message("No song is currently playing or song is already paused.", ephemeral=True)
            logging.warning("No song is playing or song already paused")

        await self.send_or_update_embed(interaction)

    async def resume_interaction(self, interaction: discord.Interaction):
        logging.info("Resume interaction invoked")
        guild_id = interaction.guild.id
        guild_state = self.get_guild_state(guild_id)

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await interaction.response.send_message("Bot is not connected to a voice channel.", ephemeral=True)
            logging.warning("Bot not connected to a voice channel")
            return

        if guild_state['is_paused']:
            voice_client.resume()
            guild_state['is_paused'] = False
            guild_state['is_playing'] = True
            if guild_state['paused_time']:
                guild_state['elapsed_paused_time'] += (datetime.utcnow() - guild_state['paused_time']).total_seconds()
            await interaction.response.send_message("Resumed the song.", ephemeral=True)
            logging.info("Resumed the song via interaction")
        else:
            await interaction.response.send_message("No song is currently paused.", ephemeral=True)
            logging.warning("No song is paused")

        await self.send_or_update_embed(interaction)

    async def skip_interaction(self, interaction: discord.Interaction):
        logging.info("Skip interaction invoked")
        guild_id = interaction.guild.id
        guild_state = self.get_guild_state(guild_id)

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await interaction.response.send_message("Bot is not connected to a voice channel.", ephemeral=True)
            logging.warning("Bot not connected to a voice channel")
            return

        if guild_state['is_playing'] or guild_state['is_paused']:
            voice_client.stop()
            await interaction.response.send_message("Skipped the song.", ephemeral=True)
            logging.info("Skipped the song via interaction")
        else:
            await interaction.response.send_message("No song is currently playing.", ephemeral=True)
            logging.warning("No song is playing")

        await self.send_or_update_embed(interaction)

    async def stop_interaction(self, interaction: discord.Interaction):
        logging.info("Stop interaction invoked")
        guild_id = interaction.guild.id
        guild_state = self.get_guild_state(guild_id)

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await interaction.response.send_message("Bot is not connected to a voice channel.", ephemeral=True)
            logging.warning("Bot not connected to a voice channel")
            return

        if guild_state['is_playing'] or guild_state['is_paused']:
            voice_client.stop()
            guild_state['is_playing'] = False
            guild_state['is_paused'] = False
            guild_state['queue'] = []
            guild_state['current_song'] = None
            guild_state['song_start_time'] = None
            guild_state['paused_time'] = None
            guild_state['elapsed_paused_time'] = 0
            await interaction.response.send_message("Stopped the song and cleared the queue.", ephemeral=True)
            logging.info("Stopped the song and cleared the queue via interaction")
        else:
            await interaction.response.send_message("No song is currently playing.", ephemeral=True)
            logging.warning("No song is playing")

        await self.send_or_update_embed(interaction)

    async def leave_interaction(self, interaction: discord.Interaction):
        logging.info("Leave interaction invoked")
        guild_id = interaction.guild.id
        guild_state = self.get_guild_state(guild_id)

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await interaction.response.send_message("Bot is not connected to a voice channel.", ephemeral=True)
            logging.warning("Bot not connected to a voice channel")
            return

        await voice_client.disconnect()
        guild_state['is_playing'] = False
        guild_state['is_paused'] = False
        guild_state['queue'] = []
        guild_state['current_song'] = None
        guild_state['song_start_time'] = None
        guild_state['paused_time'] = None
        guild_state['elapsed_paused_time'] = 0
        await interaction.response.send_message("Disconnected from the voice channel and cleared the queue.", ephemeral=True)
        logging.info("Disconnected from the voice channel and cleared the queue via interaction")

        await self.send_or_update_embed(interaction)

    async def add_queue_interaction(self, interaction: discord.Interaction):
        logging.info("Add to queue interaction invoked")
        await interaction.response.send_modal(AddQueueModal(self, interaction))

class MusicControlView(View):
    def __init__(self, music_cog):
        super().__init__(timeout=None)
        self.music_cog = music_cog

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, custom_id="pause_button", emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.pause_interaction(interaction)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.success, custom_id="resume_button", emoji="▶️")
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.resume_interaction(interaction)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.danger, custom_id="skip_button", emoji="⏭️")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.skip_interaction(interaction)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.secondary, custom_id="stop_button", emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.stop_interaction(interaction)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.secondary, custom_id="leave_button", emoji="🚪")
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.leave_interaction(interaction)

    @discord.ui.button(label="Add to Queue", style=discord.ButtonStyle.primary, custom_id="add_queue_button", emoji="➕")
    async def add_queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.add_queue_interaction(interaction)

class AddQueueModal(Modal):
    def __init__(self, music_cog, interaction):
        super().__init__(title="Add Song to Queue")
        self.music_cog = music_cog
        self.interaction = interaction
        self.add_item(TextInput(label="YouTube URL or Spotify URL", placeholder="Enter the YouTube or Spotify URL of the song"))

    async def on_submit(self, interaction: discord.Interaction):
        url = self.children[0].value
        logging.info(f"Modal URL: {url}")

        # Acknowledge the interaction first
        await interaction.response.defer(ephemeral=True)

        # Ensuring bot is in the voice channel
        if interaction.guild.voice_client is None:
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
                logging.info(f"Bot joined {interaction.user.voice.channel}")
            else:
                await interaction.followup.send("You need to be in a voice channel to add songs to the queue.", ephemeral=True)
                logging.warning("User not in a voice channel")
                return

        # Fetching the context from the interaction
        try:
            ctx = await self.music_cog.bot.get_context(interaction.message)
            logging.info(f"Context: {ctx}")
        except Exception as e:
            logging.error(f"Failed to get context: {e}")
            await interaction.followup.send(f"Failed to get context: {e}", ephemeral=True)
            return

        if not ctx.author.voice:
            await interaction.followup.send("You need to be in a voice channel to add songs to the queue.", ephemeral=True)
            logging.warning("User not in a voice channel")
            return

        try:
            await self.music_cog.play(ctx, url)
            await interaction.followup.send(f"Added song to queue from URL: {url}", ephemeral=True)
            logging.info(f"Added song to queue from URL: {url}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred while adding the song: {str(e)}", ephemeral=True)
            logging.error(f"Error in callback: {e}")

        await self.music_cog.send_or_update_embed(ctx)

async def setup(bot):
    await bot.add_cog(Music(bot))
