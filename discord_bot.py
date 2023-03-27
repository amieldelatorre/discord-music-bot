import asyncio
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from ytdl import YTDLSource


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.now_playing = {}

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel"""

        if not ctx.message.author.voice:
            return await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

    @commands.command()
    async def leave(self, ctx):
        """Leaves a voice channel"""

        voice_client = ctx.message.guild.voice_client
        if voice_client is not None and voice_client.is_connected():
            await voice_client.disconnect()
            await ctx.send("Disconnected from the voice channel.")
            del self.queues[ctx.guild.id]
            del self.now_playing[ctx.guild.id]
        else:
            await ctx.send("Not connected to a voice channel.")

    @commands.command()
    async def play(self, ctx, *, url):
        """Streams from a url (does not pre-download)"""

        guild_id = ctx.guild.id
        await ctx.send(f'***Searching for song:*** {url}')

        if guild_id not in self.queues:
            self.queues[guild_id] = [url]

        if ctx.voice_client.is_playing():
            self.queues[guild_id].append(url)

            return await ctx.send(
                f'Added song {url} to queue.\n'
                f'*Number of items in queue*: {len(self.queues[guild_id])}'
            )
        else:
            async with ctx.typing():
                player = await YTDLSource.from_url(self.queues[guild_id].pop(0), loop=self.bot.loop, stream=True)

                self.now_playing[guild_id] = {
                    "title": player.title,
                    "url": player.data["original_url"]
                }

                ctx.voice_client.play(player, after=lambda x=None: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))

            await ctx.send(
                f'***Now playing:*** {player.title}\n'
                f'{player.data["original_url"]}'
            )

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        voice_client = ctx.voice_client

        del self.now_playing[guild_id]

        if guild_id in self.queues and len(self.queues[guild_id]) >= 1:
            player = await YTDLSource.from_url(self.queues[guild_id].pop(0), loop=self.bot.loop, stream=True)

            self.now_playing[guild_id] = {
                "title": player.title,
                "url": player.data["original_url"]
            }

            voice_client.play(player,
                              after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            asyncio.run_coroutine_threadsafe(ctx.send(
                f'***Now playing:*** {player.title}\n'
                f'{player.data["original_url"]}'
            ), self.bot.loop)
        # else:
        #     asyncio.sleep(90)
        #     if not voice_client.is_playing():
        #         asyncio.run_coroutine_threadsafe(voice_client.disconnect(), self.bot.loop)
        #         asyncio.run_coroutine_threadsafe(ctx.send("No more songs in queue."), self.bot.loop)

    @commands.command()
    async def now_playing(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.now_playing:
            return await ctx.send("Not currently playing a song!")

        await ctx.send(
            f'***Current Song:*** {self.now_playing[guild_id]["title"]}\n'
            f'{self.now_playing[guild_id]["url"]}'
        )

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel!")
        if not ctx.voice_client.is_playing():
            return await ctx.send("Not currently playing a song!")

        ctx.voice_client.pause()
        await ctx.send("Paused the song!")

    @commands.command()
    async def resume(self, ctx):
        """Pauses the paused song"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel!")
        if ctx.voice_client.is_playing():
            return await ctx.send("Already playing a song!")

        ctx.voice_client.resume()
        await ctx.send("Resumed the song!")

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel!")
        if not ctx.voice_client.is_playing():
            return await ctx.send("Not currently playing a song!")

        if len(self.queues[ctx.guild.id]) == 0:
            await ctx.send(
                "This is the last song in the queue!\n"
                "Stopping the song."
            )
        ctx.voice_client.stop()
        await self.play_next(ctx)

    @commands.command()
    async def queue(self, ctx):
        """Shows current queue"""

        if ctx.guild.id not in self.queues or len(self.queues[ctx.guild.id]) == 0:
            return await ctx.send("There are currently no songs in the queue!")
        else:
            song_list = ""
            num = 1
            for url in self.queues[ctx.guild.id]:
                song_list += f"> **{num}.** {url}\n"
                num += 1

            return await ctx.send(
                f"Number of songs in queue: {len(self.queues[ctx.guild.id])}\n"
                f"{song_list}"
            )

    @commands.command()
    async def dequeue(self, ctx, *, index: int):
        """Removes a song from the queue"""

        if not isinstance(index, int):
            return await ctx.send("The index provided was not an int.")

        guild_id = ctx.guild.id

        if guild_id not in self.queues or len(self.queues[guild_id]) == 0:
            return await ctx.send("There are currently no songs in the queue!")
        if index < 1 or index > len(self.queues[guild_id]):
            await ctx.send(f"The values have to be within the range of *1 - {len(self.queues[guild_id])}!*")
            return await self.queue(ctx)

        url = self.queues[guild_id].pop(index - 1)
        await ctx.send(f"Removed the song from queue: {url}")
        return await self.queue(ctx)

    @commands.command()
    async def queue_swap(self, ctx, first: int, second: int):
        """Swaps the positions of two songs in the queue"""

        guild_id = ctx.guild.id
        if guild_id not in self.queues or len(self.queues[guild_id]) == 0:
            return await ctx.send("There are currently no songs in the queue!")

        queue_length = len(self.queues[guild_id])

        if first < 1 or second < 1 or first > queue_length or second > queue_length:
            await ctx.send(f"The values have to be within the range of *1 - {queue_length}!*")
            return await self.queue(ctx)

        position1 = first - 1
        position2 = second - 1

        await ctx.send(f"Swapping the songs in position *{first}* and *{second}* of the queue.")
        temp = self.queues[guild_id][position1]
        self.queues[guild_id][position1] = self.queues[guild_id][position2]
        self.queues[guild_id][position2] = temp
        await ctx.send(f"Swapped the songs in position *{first}* and *{second}* of the queue.")

        await self.queue(ctx)

    @commands.command()
    async def queue_jump(self, ctx, position: int):
        """Jumps to a position in the queue, skipping everything in between"""

        guild_id = ctx.guild.id
        if guild_id not in self.queues or len(self.queues[guild_id]) == 0:
            return await ctx.send("There are currently no songs in the queue!")

        original_queue_length = len(self.queues[guild_id])
        if position < 1 or position > original_queue_length:
            await ctx.send(f"The values have to be within the range of *1 - {original_queue_length}!*")
            return await self.queue(ctx)

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        del self.queues[guild_id][:position-1]

        await ctx.send(f"Jumping to the song in position *{position}* of the queue.")
        await self.queue(ctx)
        return await self.play_next(ctx)

    @commands.command()
    async def volume(self, ctx, *, volume: int = None):
        """Shows current volume"""

        if not isinstance(volume, int):
            return await ctx.send("The volume provided was not an int.")

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel!")
        if volume is None:
            return await ctx.send(f'***Current Volume:*** {ctx.voice_client.source.volume*100}%')

        if volume < 0:
            return await ctx.send(f'Volume *{volume}*% is too low!')
        elif volume > 150:
            return await ctx.send(f'Volume *{volume}*% is too high!')

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Stops the current song"""
        if ctx.voice_client is None:
            await ctx.send(f"Not connected to a voice channel!")
        if not ctx.voice_client.is_playing():
            await ctx.send(f"Not connected to a voice channel!")

        await ctx.send(f"*Stopping the current song...*")
        ctx.voice_client.stop()
        await ctx.send(f"Song has been stopped.")

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await self.join(ctx)
            else:
                await ctx.send("You are not connected to a voice channel!")
                raise commands.CommandError("Author not connected to a voice channel!")
        elif ctx.voice_client.is_playing():
            # queue the song
            # ctx.voice_client.stop()
            pass


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("^"),
    description='Relatively simple music bot example',
    intents=intents,
)


@bot.event
async def on_guild_join(guild):
    print(f"[join-guild] Joined guild: {guild.id}")
    print("I JOINED A GUILD")


@bot.event
async def on_ready():
    running_message = f'[start] Logged in as {bot.user} (ID: {bot.user.id})'
    print(running_message)
    print('-' * len(running_message))


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

            if voice_client.guild.id in bot.get_cog("Music").queues:
                del bot.get_cog("Music").queues[voice_client.guild.id]
                del bot.get_cog("Music").now_playing[voice_client.guild.id]
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
        DISCORD_TOKEN = os.getenv("discord_token")
        await bot.add_cog(Music(bot))
        await bot.start(DISCORD_TOKEN)
