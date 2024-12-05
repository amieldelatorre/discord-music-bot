import os
import logging
import asyncio

import discord
import yt
from dataclasses import dataclass
from discord.ext import commands, tasks
from config import logger,  get_required_environment_variable, get_environment_variable_with_default
from persistence.queue_service import QueueService
from persistence.key_value_service import KeyValueService
from persistence.analytics_service import EventAnalyticsService, SongAnalyticsService


@dataclass
class MusicBotConfig:
    auto_disconnect_timer_seconds: int
    downloads_directory: str
    cleanup_after_song: bool
    mongodb_host: str
    mongodb_port: str
    mongodb_database: str
    mongodb_username: str
    mongodb_password: str
    enable_stats: bool

    opensearch_host: str
    opensearch_port: int
    opensearch_username: str
    opensearch_password: str
    opensearch_verify_certs: bool
    opensearch_ssl_assert_hostname: bool
    opensearch_ssl_show_warn: bool


class DiscordPlayer(discord.PCMVolumeTransformer):
    def __init__(self, source, *, volume=0.5):
        ffmpeg_options = {
            'options': '-vn',
        }
        discord_ffmpeg_audio = discord.FFmpegPCMAudio(
            source,
            **ffmpeg_options
        )
        super().__init__(discord_ffmpeg_audio, volume)


def get_music_bot_config() -> MusicBotConfig:
    auto_disconnect_timer_seconds = int(get_environment_variable_with_default("AUTO_DISCONNECT_TIMER_SECONDS", 300))
    downloads_directory = get_environment_variable_with_default("DOWNLOADS_DIRECTORY", "Downloads")
    cleanup_after_song = get_environment_variable_with_default("CLEANUP_AFTER_SONG", "True").lower() == "true"
    enable_stats = get_environment_variable_with_default("ENABLE_STATS", "False").lower() == "true"

    mongodb_host = get_required_environment_variable("MONGODB_HOST")
    mongodb_port = get_required_environment_variable("MONGODB_PORT")
    mongodb_database = get_required_environment_variable("MONGODB_DATABASE")
    mongodb_username = get_required_environment_variable("MONGODB_USERNAME")
    mongodb_password = get_required_environment_variable("MONGODB_PASSWORD")

    logger.log(logging.INFO, f"CLEANUP_AFTER_SONG: {cleanup_after_song}")
    logger.log(logging.INFO, f"AUTO_DISCONNECT_TIMER_SECONDS: {auto_disconnect_timer_seconds}")
    logger.log(logging.INFO, f"ENABLE_STATS: {enable_stats}")

    opensearch_host = get_required_environment_variable("OPENSEARCH_HOST") if enable_stats else "not required"
    opensearch_port = int(get_required_environment_variable("OPENSEARCH_PORT")) if enable_stats else 0
    opensearch_username = get_required_environment_variable("OPENSEARCH_USERNAME") if enable_stats else "not required"
    opensearch_password = get_required_environment_variable("OPENSEARCH_PASSWORD") if enable_stats else "not required"
    opensearch_verify_certs = get_environment_variable_with_default("OPENSEARCH_VERIFY_CERTS", "False").lower() == "true"
    opensearch_ssl_assert_hostname = get_environment_variable_with_default("OPENSEARCH_SSL_ASSERT_HOSTNAME", "False").lower() == "true"
    opensearch_ssl_show_warn = get_environment_variable_with_default("OPENSEARCH_SSL_SHOW_WARN", "False").lower() == "true"

    return MusicBotConfig(
        auto_disconnect_timer_seconds=auto_disconnect_timer_seconds,
        downloads_directory=downloads_directory,
        cleanup_after_song=cleanup_after_song,
        enable_stats=enable_stats,
        mongodb_host=mongodb_host,
        mongodb_port=mongodb_port,
        mongodb_database=mongodb_database,
        mongodb_username=mongodb_username,
        mongodb_password=mongodb_password,
        opensearch_host=opensearch_host,
        opensearch_port=opensearch_port,
        opensearch_username=opensearch_username,
        opensearch_password=opensearch_password,
        opensearch_verify_certs=opensearch_verify_certs,
        opensearch_ssl_assert_hostname=opensearch_ssl_assert_hostname,
        opensearch_ssl_show_warn=opensearch_ssl_show_warn,
    )


class MusicBot(commands.Cog):
    def __init__(self,
                 bot: commands.Bot,
                 config: MusicBotConfig,
                 music_queue_service: QueueService,
                 now_playing_service: KeyValueService,
                 event_analytics_service: EventAnalyticsService,
                 song_analytics_service: SongAnalyticsService
                 ):
        self.bot = bot
        self.config = config
        self.music_queue_service = music_queue_service
        self.now_playing_service = now_playing_service
        self.event_analytics_service = event_analytics_service
        self.song_analytics_service = song_analytics_service

        @bot.event
        async def on_voice_state_update(member, before, after):
            channel_before = before.channel
            channel_after = after.channel

            if len(bot.voice_clients) == 0:
                return

            if channel_before is not None and (channel_after is None or channel_before != channel_after):
                if len(before.channel.members) == 1 and self.is_bot_in_voice_channel(channel_before):
                    voice_client = self.get_voice_client(channel_before)

                    if voice_client.is_playing():
                        voice_client.stop()
                    await self.cleanup_guild(voice_client.guild.id)
                    return await voice_client.disconnect()
            elif bot.application_id == member.id and (channel_before is not None and channel_after is None):
                voice_client = self.get_voice_client(channel_before)
                await self.cleanup_guild(voice_client.guild.id)
                return
            else:
                return

    def is_bot_in_voice_channel(self, channel: str) -> bool:
        """Checks if the bot is in the matching channel"""

        for voice_client in self.bot.voice_clients:
            if voice_client.channel == channel:
                return True
        return False

    def get_voice_client(self, channel):
        """Gets the matching voice client, does not check if channel exists. Returns None if no channels are found"""

        for voice_client in self.bot.voice_clients:
            if voice_client.channel == channel:
                return voice_client
        return None

    # async def auto_disconnect_handler(self, ctx):
    #     asyncio.run_coroutine_threadsafe(self.auto_disconnect(ctx), self.bot.loop)

    async def auto_disconnect(self, ctx):
        """Disconnect based on an inactivity timer"""

        voice_client = ctx.voice_client
        await asyncio.sleep(self.config.auto_disconnect_timer_seconds)

        if (voice_client is not None and not voice_client.is_playing() and not voice_client.is_paused()
                and voice_client.is_connected()):
            logger.log(logging.INFO,
                       f"Disconnecting after {self.config.auto_disconnect_timer_seconds} seconds of inactivity.")
            asyncio.run_coroutine_threadsafe(self.leave(ctx), self.bot.loop)
            asyncio.run_coroutine_threadsafe(await ctx.send("Leaving due to inactivity."), self.bot.loop)
        else:
            logger.log(logging.INFO, f"Staying in voice channel, bot is not idle or not in a voice channel")
            await self.auto_disconnect(ctx)

    @commands.command()
    async def join(self, ctx):
        """Join a voice channel"""

        logger.log(logging.INFO, "Attempting to join a channel")
        if not ctx.message.author.voice:
            logging.log(logging.INFO, "Requesting user is not in a voice channel. Not joining voice channel")
            return await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
            logging.log(logging.INFO, "Joined voice channel")
        else:
            await ctx.voice_client.move_to(voice_channel)

        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)
        asyncio.run_coroutine_threadsafe(self.auto_disconnect(ctx), self.bot.loop)

    @commands.command()
    async def leave(self, ctx):
        """Leave a voice channel"""
        logger.log(logging.INFO, f"Leaving the voice channel")

        voice_client = ctx.message.guild.voice_client
        if voice_client is not None and voice_client.is_connected():
            await voice_client.disconnect()
            await ctx.send("Disconnected from the voice channel.")
        else:
            await ctx.send("Not connected to a voice channel.")

    @leave.after_invoke
    async def leave_cleanup(self, ctx):
        guild_id = ctx.guild.id
        await self.cleanup_guild(guild_id)

    @commands.command()
    async def play(self, ctx, *, url: str = None):
        """Downloads and then plays"""

        if ctx.voice_client is None:
            return

        logger.log(logging.INFO, f"Play a song.")
        if ctx.voice_client is not None and ctx.voice_client.is_paused():
            return ctx.voice_client.resume()

        if url is None:
            return await ctx.send(f"A search term or url is needed! for the `play` command!")

        guild_id = ctx.guild.id
        await ctx.send(f'***Searching for song:*** {url}')

        async with ctx.typing():
            song_data = await yt.yt_dl_from_url(url, self.config.downloads_directory)

        await self.music_queue_service.add_to_queue(guild_id, song_data)
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            await ctx.send(
                f'Added song ***{song_data.get("title")}*** to queue.\n'
                f'*Number of items in queue*: {await self.music_queue_service.get_queue_size(guild_id)}'
            )
        else:
            await self.play_next(ctx)
        return await self.queue(ctx)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        """Makes sure that the user is connected to a voice channel before a play command is executed"""

        logger.log(logging.INFO, "Checking voice before going to the play command.")

        if ctx.voice_client is None:
            if ctx.author.voice:
                await self.join(ctx)
            else:
                return await ctx.send("You are not connected to a voice channel!")

    @commands.command()
    async def queue(self, ctx):
        """Shows current queue"""

        logger.log(logging.INFO, f"Showing items in queue.")

        if await self.music_queue_service.is_queue_empty(ctx.guild.id):
            return await ctx.send("There are currently no songs in the queue!")
        else:
            song_list = ""
            num = 1
            queue = await self.music_queue_service.get_queue_by_id(ctx.guild.id)
            for song in queue:
                song_list += f"> **{num}.** {song.get('title')}\n"
                num += 1

            return await ctx.send(
                f"Number of songs in queue: {await self.music_queue_service.get_queue_size(ctx.guild.id)}\n"
                f"{song_list}"
            )

    async def play_song(self, ctx, guild_id: str, voice_client):
        song = await self.music_queue_service.queue_index_pop(guild_id, 0)
        player = DiscordPlayer(song.get("filename"))

        await self.now_playing_service.set_key_overwrite_existing(guild_id, song)

        logger.log(logging.INFO, f"Playing the song.")
        voice_client.play(
            player,
            after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
        )

        await ctx.send(
            f'***Now playing:*** {song.get("title")}\n'
            f'{song.get("url")}'
        )

    async def play_next(self, ctx):
        logger.log(logging.INFO, "Attempting to play the next song")
        guild_id = ctx.guild.id
        voice_client = ctx.voice_client
        finished_song = await self.now_playing_service.get(guild_id)

        await self.now_playing_service.delete(guild_id)
        if finished_song is not None:
            await self.cleanup_song(finished_song.get("filename"))

        if not await self.music_queue_service.is_queue_empty(guild_id):
            await self.play_song(ctx, guild_id, voice_client)

    @commands.command()
    async def now_playing(self, ctx):
        """Show the currently playing song"""
        logger.log(logging.DEBUG, f"Showing the current song")

        guild_id = ctx.guild.id
        now_playing = await self.now_playing_service.get(guild_id)
        if now_playing is None:
            return await ctx.send("Not currently playing a song!")

        await ctx.send(
            f'***Current Song:*** {now_playing.get("title")}\n'
            f'{now_playing.get("url")}'
        )

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel!")
        elif not ctx.voice_client.is_playing():
            return await ctx.send("Not currently playing a song!")
        elif ctx.voice_client.is_paused():
            return await ctx.send("The song is already paused!")

        ctx.voice_client.pause()
        logger.log(logging.INFO, f"Pausing the playing song.")
        await ctx.send("Paused the song!")

    @commands.command()
    async def resume(self, ctx):
        """Resumes the paused song"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel!")
        elif ctx.voice_client.is_playing():
            return await ctx.send("Already playing a song!")
        elif not ctx.voice_client.is_paused():
            return await ctx.send("There is no song paused!")

        ctx.voice_client.resume()
        logger.log(logging.INFO, f"Resuming the paused song.")
        await ctx.send("Resumed the song!")

    @commands.command()
    async def stop(self, ctx):
        """Stops the current song and clears the queue"""

        logger.log(logging.INFO, "Stopping the current song. ")

        if ctx.voice_client is None:
            await ctx.send(f"Not connected to a voice channel!")
        elif not ctx.voice_client.is_playing():
            await ctx.send(f"Not connected to a voice channel!")

        await self.stop_guild(ctx)

        await ctx.send(f"Song has been stopped and queue has been cleared.")
        return await self.queue(ctx)

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel!")
        elif not ctx.voice_client.is_playing():
            return await ctx.send("Not currently playing a song!")
        elif await self.music_queue_service.is_queue_empty(ctx.guild.id):
            await ctx.send("This is the last song in the queue!")

        logger.log(logging.INFO, f"Skipping the current song.")
        ctx.voice_client.stop()
        # Stopping the voice client automatically plays the next song because this goes back to the play_next function

    @commands.command()
    async def dequeue(self, ctx, *, index: int):
        """Removes a song from the queue"""

        if not isinstance(index, int):
            return await ctx.send("The index provided was not an int.")

        guild_id = ctx.guild.id

        if await self.music_queue_service.is_queue_empty(guild_id):
            return await ctx.send("There are currently no songs in the queue!")
        elif not await self.music_queue_service.is_1_base_index_valid(guild_id, index):
            await ctx.send(
                f"The values have to be within the range of *1 - {await self.music_queue_service.get_queue_size(guild_id)}!*")
            return await self.queue(ctx)

        song = await self.dequeue_song(guild_id, index)
        if song is None:
            return await ctx.send(f"Error popping index from queue.")

        await ctx.send(f"Removed the song from queue: {song.get('title')}")
        logger.log(logging.INFO, f"Removed the song from queue: {song.get('title')}")
        return await self.queue(ctx)

    @commands.command()
    async def queue_swap(self, ctx, first: int, second: int):
        """Swaps the positions of two songs in the queue"""

        guild_id = ctx.guild.id
        if await self.music_queue_service.is_queue_empty(guild_id):
            return await ctx.send("There are currently no songs in the queue!")

        queue_size = await self.music_queue_service.get_queue_size(guild_id)

        if (not await self.music_queue_service.is_1_base_index_valid(guild_id, first) or
                not await self.music_queue_service.is_1_base_index_valid(guild_id, second)):
            await ctx.send(f"The values have to be within the range of *1 - {queue_size}!*")
            return await self.queue(ctx)

        await ctx.send(f"Swapping the songs in position *{first}* and *{second}* of the queue.")
        swap_result = await self.music_queue_service.queue_swap_items(guild_id, first - 1, second - 1)

        if swap_result:
            await ctx.send(f"Swapped the songs in position *{first}* and *{second}* of the queue.")
            logger.log(logging.INFO, f"Swapped the songs in position *{first}* and *{second}* of the queue.")
        else:
            await ctx.send(f"Failed swapping songs in position *{first}* and *{second}* of the queue.")

        await self.queue(ctx)

    @commands.command()
    async def queue_jump(self, ctx, index: int):
        """Jumps to a position in the queue, skipping everything in between"""

        guild_id = ctx.guild.id
        if await self.music_queue_service.is_queue_empty(guild_id):
            return await ctx.send("There are currently no songs in the queue!")

        original_queue_length = await self.music_queue_service.get_queue_size(guild_id)
        if not await self.music_queue_service.is_1_base_index_valid(guild_id, index):
            await ctx.send(f"The values have to be within the range of *1 - {original_queue_length}!*")
            return await self.queue(ctx)

        await ctx.send(f"Jumping to the song in position *{index}* of the queue.")
        if index == 1:
            jump_result = [await self.now_playing_service.get(guild_id)]
        else:
            jump_result = await self.music_queue_service.queue_jump(guild_id, index - 1)

        if jump_result:
            logger.log(logging.INFO, f"Jumped to the song in position *{index}* of the queue.")
            ctx.voice_client.stop()
            for song in jump_result:
                await self.cleanup_song(song.get("filename"))
            # Stopping the voice client automatically plays the next song because this goes
            # back to the play_next function
        else:
            await ctx.send(f"Failed to jump to position *{index}* of the queue.")
        # return await self.queue(ctx)

    @commands.command()
    async def queue_move(self, ctx, index_from: int, index_to: int):
        """Moves a song from its original position in the queue to a new position"""

        guild_id = ctx.guild.id
        if await self.music_queue_service.is_queue_empty(guild_id):
            return await ctx.send("There are currently no songs in the queue!")

        original_queue_length = await self.music_queue_service.get_queue_size(guild_id)

        if (not await self.music_queue_service.is_1_base_index_valid(guild_id, index_from) or
                not await self.music_queue_service.is_1_base_index_valid(guild_id, index_to)):
            return await ctx.send(f"The values have to be within the range of *1 - {original_queue_length}!*")
        elif index_from == index_to:
            return await ctx.send(f"The song is already in that position!")

        await ctx.send(f"Moving the song in position {index_from} to {index_to} of the queue.")

        move_result = await self.music_queue_service.queue_move(guild_id, index_from - 1, index_to - 1)
        if move_result:
            logger.log(logging.INFO, "Moved the song in position {index_from} to {index_to} of the queue.")
            await ctx.send(f"Moved the song in position {index_from} to {index_to} of the queue.")
        else:
            await ctx.send(f"Failed to move the song in position {index_from} to {index_to} of the queue.")

        return await self.queue(ctx)

    async def dequeue_song(self, guild_id, index):
        song = await self.music_queue_service.queue_index_pop(guild_id, index - 1)
        await self.cleanup_song(song.get("filename"))
        return song

    async def stop_guild(self, ctx):
        await self.cleanup_guild(guild_id=ctx.guild.id)
        ctx.voice_client.stop()
        # TODO: Delete if delete file
        # for player in players:
        #     self.delete_file(player)

    async def cleanup_guild(self, guild_id):
        logger.log(logging.INFO, f"Cleaning up the queue and the now playing values")
        await self.music_queue_service.delete_queue_by_id(guild_id)
        await self.now_playing_service.delete(guild_id)

    async def cleanup_song(self, filename: str):
        if not self.config.cleanup_after_song:
            return

        if not await self.music_queue_service.is_field_item_in_any_queue("filename", filename):
            try:
                os.remove(filename)
                logger.log(logging.INFO, f"Deleted file {filename}")
            except Exception as e:
                logger.log(logging.ERROR, f"Error deleting file. Message: {e}")
