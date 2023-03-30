import asyncio
import os
import discord
import logging
import json
from dotenv import load_dotenv
from discord.ext import commands
from ytdl import YTDLSource
from data.InMemoryDb import InMemoryDb


class Music(commands.Cog):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    def log(self, log_level, message):
        self.bot.logger.log(log_level, message)

    async def auto_disconnect(self, ctx):
        inactivity_timer = 30
        voice_client = ctx.voice_client
        await asyncio.sleep(inactivity_timer)
        if (voice_client is not None and not voice_client.is_playing() and not voice_client.is_paused()
                and voice_client.is_connected()):
            self.log(logging.INFO, f"Disconnecting after {inactivity_timer} seconds of inactivity.")
            asyncio.run_coroutine_threadsafe(self.leave(ctx), self.bot.loop)
            asyncio.run_coroutine_threadsafe(ctx.send("Leaving due to inactivity."), self.bot.loop)

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel"""

        self.log(logging.INFO, f"Joining a channel.")

        if not ctx.message.author.voice:
            return await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)
        asyncio.run_coroutine_threadsafe(self.auto_disconnect(ctx), self.bot.loop)

    @commands.command()
    async def leave(self, ctx):
        """Leaves a voice channel"""

        self.log(logging.INFO, f"Leaving the voice channel.")

        voice_client = ctx.message.guild.voice_client
        if voice_client is not None and voice_client.is_connected():
            await voice_client.disconnect()
            await ctx.send("Disconnected from the voice channel.")
            self.log(logging.INFO, f"Cleaning up the queue and the now playing values")
            self.db.clean_up_for_guild_id(ctx.guild.id)
        else:
            await ctx.send("Not connected to a voice channel.")

    @commands.command()
    async def play(self, ctx, *, url):
        """Downloads and then plays"""

        self.log(logging.INFO, f"Play a song.")

        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()

        guild_id = ctx.guild.id
        await ctx.send(f'***Searching for song:*** {url}')

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)

        self.db.add_to_queue(guild_id, player)
        if ctx.voice_client.is_playing():
            await ctx.send(
                f'Added song ***{player.title}*** to queue.\n'
                f'*Number of items in queue*: {self.db.queue_size(guild_id)}'
            )
            return await self.queue(ctx)

        else:
            voice_client = ctx.voice_client
            await self.play_song(ctx, guild_id, voice_client)

    async def play_song(self, ctx, guild_id, voice_client):
        queue = self.db.get_queue_with_guild_id(guild_id)
        player = queue.pop(0)
        self.db.set_queue(guild_id, queue)

        self.db.set_now_playing(guild_id, player)

        self.log(logging.INFO, f"Playing the song.")

        voice_client.play(player,
                          after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        asyncio.run_coroutine_threadsafe(ctx.send(
            f'***Now playing:*** {player.title}\n'
            f'{player.data["original_url"]}'
        ), self.bot.loop)

    async def play_next(self, ctx):
        self.log(logging.INFO, f"Attempting to play the next song.")

        guild_id = ctx.guild.id
        voice_client = ctx.voice_client

        self.db.delete_now_playing(guild_id)

        if self.db.is_there_item_in_queue_for_guild_id(guild_id):
            await self.play_song(ctx, guild_id, voice_client)
        else:
            await self.auto_disconnect(ctx)

    @commands.command()
    async def now_playing(self, ctx):
        """Show the currently playing song."""

        self.log(logging.INFO, f"Showing the current song.")

        guild_id = ctx.guild.id
        if not self.db.guild_id_in_now_playings(guild_id):
            return await ctx.send("Not currently playing a song!")

        np = self.db.get_now_playing_with_guild_id(guild_id)

        await ctx.send(
            f'***Current Song:*** {np.title}\n'
            f'{np.data["original_url"]}'
        )

        self.log(logging.INFO, f"Showing the current song.")

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
        self.log(logging.INFO, f"Pausing the playing song.")
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
        self.log(logging.INFO, f"Resuming the paused song.")
        await ctx.send("Resumed the song!")

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel!")
        elif not ctx.voice_client.is_playing():
            return await ctx.send("Not currently playing a song!")
        elif self.db.queue_size(ctx.guild.id) == 0:
            await ctx.send("This is the last song in the queue!")

        self.log(logging.INFO, f"Skipping the current song.")
        ctx.voice_client.pause()
        await self.play_next(ctx)

    @commands.command()
    async def queue(self, ctx):
        """Shows current queue"""

        self.log(logging.INFO, f"Showing items in queue.")

        if not self.db.is_there_item_in_queue_for_guild_id(ctx.guild.id):
            return await ctx.send("There are currently no songs in the queue!")
        else:
            song_list = ""
            num = 1
            for player in self.db.get_queue_with_guild_id(ctx.guild.id):
                song_list += f"> **{num}.** {player.title}\n"
                num += 1

            return await ctx.send(
                f"Number of songs in queue: {self.db.queue_size(ctx.guild.id)}\n"
                f"{song_list}"
            )

    @commands.command()
    async def dequeue(self, ctx, *, index: int):
        """Removes a song from the queue"""

        if not isinstance(index, int):
            return await ctx.send("The index provided was not an int.")

        guild_id = ctx.guild.id

        if not self.db.is_there_item_in_queue_for_guild_id(guild_id):
            return await ctx.send("There are currently no songs in the queue!")
        elif not self.db.is_index_valid(index, guild_id):
            await ctx.send(f"The values have to be within the range of *1 - {self.db.queue_size(guild_id)}!*")
            return await self.queue(ctx)

        player = self.db.pop_index_from_queue(index, guild_id)
        if player is None:
            return await ctx.send(f"Error popping index from queue.")

        await ctx.send(f"Removed the song from queue: {player.title}")
        self.log(logging.INFO, f"Removed the song from queue: {player.title}")
        return await self.queue(ctx)

    @commands.command()
    async def queue_swap(self, ctx, first: int, second: int):
        """Swaps the positions of two songs in the queue"""

        guild_id = ctx.guild.id
        if not self.db.is_there_item_in_queue_for_guild_id(guild_id):
            return await ctx.send("There are currently no songs in the queue!")

        queue_length = self.db.queue_size(guild_id)

        if not self.db.is_index_valid(first, guild_id) or not self.db.is_index_valid(second, guild_id):
            await ctx.send(f"The values have to be within the range of *1 - {queue_length}!*")
            return await self.queue(ctx)

        await ctx.send(f"Swapping the songs in position *{first}* and *{second}* of the queue.")

        swap_result = self.db.queue_swap(guild_id, first, second)

        if swap_result:
            await ctx.send(f"Swapped the songs in position *{first}* and *{second}* of the queue.")
            self.log(logging.INFO, f"Swapped the songs in position *{first}* and *{second}* of the queue.")
        else:
            await ctx.send(f"Failed swapping songs in position *{first}* and *{second}* of the queue.")

        await self.queue(ctx)

    @commands.command()
    async def queue_jump(self, ctx, position: int):
        """Jumps to a position in the queue, skipping everything in between"""

        guild_id = ctx.guild.id
        if not self.db.is_there_item_in_queue_for_guild_id(guild_id):
            return await ctx.send("There are currently no songs in the queue!")

        original_queue_length = self.db.queue_size(guild_id)
        if not self.db.is_index_valid(position, guild_id):
            await ctx.send(f"The values have to be within the range of *1 - {original_queue_length}!*")
            return await self.queue(ctx)
        elif ctx.voice_client.is_playing():
            ctx.voice_client.pause()

        jump_result = self.db.queue_jump(guild_id, position)
        if jump_result:
            await ctx.send(f"Jumping to the song in position *{position}* of the queue.")
            self.log(logging.INFO, "Jumped to the song in position *{position}* of the queue.")
            await self.play_next(ctx)
        else:
            await ctx.send(f"Failed to jump to position *{position}* of the queue.")
        return await self.queue(ctx)

    @commands.command()
    async def queue_move(self, ctx, index_from: int, index_to: int):
        """Moves a song from its original position in the queue to a new position"""

        guild_id = ctx.guild.id
        if not self.db.is_there_item_in_queue_for_guild_id(guild_id):
            return await ctx.send("There are currently no songs in the queue!")

        original_queue_length = self.db.queue_size(guild_id)

        if not self.db.is_index_valid(index_from, guild_id) or not self.db.is_index_valid(index_to, guild_id):
            return await ctx.send(f"The values have to be within the range of *1 - {original_queue_length}!*")
        elif index_from == index_to:
            return await ctx.send(f"The song is already in that position!")

        await ctx.send(f"Moving the song in position {index_from} to {index_to} of the queue.")

        move_result = self.db.queue_move(guild_id, index_from, index_to)
        if move_result:
            self.log(logging.INFO, "Moved the song in position {index_from} to {index_to} of the queue.")
            await ctx.send(f"Moved the song in position {index_from} to {index_to} of the queue.")
        else:
            await ctx.send(f"Failed to move the song in position {index_from} to {index_to} of the queue.")

        return await self.queue(ctx)

    @commands.command()
    async def volume(self, ctx, *, volume: int = None):
        """Shows current volume"""

        if not isinstance(volume, int):
            return await ctx.send("The volume provided was not an int.")
        elif ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel!")
        elif volume is None:
            self.log(logging.INFO, "Showing current volume.")
            return await ctx.send(f'***Current Volume:*** {ctx.voice_client.source.volume*100}%')

        if volume < 0:
            return await ctx.send(f'Volume *{volume}*% is too low!')
        elif volume > 150:
            return await ctx.send(f'Volume *{volume}*% is too high!')

        self.log(logging.INFO, "Changing the volume")
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Stops the current song and clears the queue"""

        self.log(logging.INFO, "Stopping the current song. ")

        if ctx.voice_client is None:
            await ctx.send(f"Not connected to a voice channel!")
        elif not ctx.voice_client.is_playing():
            await ctx.send(f"Not connected to a voice channel!")

        self.db.clean_up_for_guild_id(ctx.guild.id)
        ctx.voice_client.stop()
        await ctx.send(f"Song has been stopped and queue has been cleared.")
        return await self.queue(ctx)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        """Makes sure that the user is connected to a voice channel before a play command is executed"""

        self.log(logging.INFO, "Checking voice before going to the play command.")

        if ctx.voice_client is None:
            if ctx.author.voice:
                await self.join(ctx)
            else:
                await ctx.send("You are not connected to a voice channel!")
                raise commands.CommandError("Author not connected to a voice channel!")


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("^"),
    description='Relatively simple music bot example',
    intents=intents,
)


@bot.event
async def on_guild_join(guild):
    bot.logger.log(logging.INFO, f"[join-guild] Joined guild: {guild.id}")


@bot.event
async def on_ready():
    bot.logger.log(logging.INFO, f'[start] Logged in as {bot.user} (ID: {bot.user.id})')


@bot.event
async def on_voice_state_update(member, before, after):
    channel_before = before.channel
    channel_after = after.channel

    if len(bot.voice_clients) == 0:
        return

    if channel_before is not None and (channel_after is None or channel_before != channel_after):
        if len(before.channel.members) == 1 and bot_in_voice_channel(channel_before):
            voice_client = get_voice_client(channel_before)

            if voice_client.is_playing():
                voice_client.stop()

            if bot.get_cog("Music").db.guild_id_in_queues(voice_client.guild.id):
                bot.logger.log(logging.INFO, f"Cleaning up the queue and the now playing values")
                bot.get_cog("Music").db.clean_up_for_guild_id(voice_client.guild.id)
            return await voice_client.disconnect()
    else:
        return


def bot_in_voice_channel(channel) -> bool:
    """Checks if the bot is in the matching channel"""

    for voice_client in bot.voice_clients:
        if voice_client.channel == channel:
            return True
    return False


def get_voice_client(channel):
    """Gets the matching voice client, does not check if channel exists. Returns None if no channels are found"""

    for voice_client in bot.voice_clients:
        if voice_client.channel == channel:
            return voice_client
    return None


async def main():
    async with bot:
        load_dotenv()

        discord_token = os.getenv("discord_token")
        logging_level = os.getenv("logging_level")
        log_format = json.dumps({'time': '%(asctime)s', 'name': '%(name)s', 'level': '%(levelname)s',
                                 'message': '%(message)s'})
        logging.basicConfig(
            format=log_format,
            level=logging_level,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        logger = logging.getLogger()

        bot.logger = logger
        db = InMemoryDb()
        await bot.add_cog(Music(bot, db))
        await bot.start(discord_token)
