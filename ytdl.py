from __future__ import unicode_literals
from dotenv import load_dotenv
import asyncio
import os
import discord
import yt_dlp as youtube_dl


load_dotenv()
pwd = os.getcwd()
download_subdirectory = os.getenv("downloads_subdirectory")
download_path = os.path.join(pwd, download_subdirectory)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': os.path.join(download_path, '%(id)s.mp3'),
    'restrictfilenames': True,
    'noplaylist': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    'before_options': "-reconnect 1 -reconnect_streamed 1  -reconnect_on_network_error 1 -reconnect_on_http_error 1 -reconnect_delay_max 5"
    # https://ffmpeg.org/ffmpeg-protocols.html#http
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(
            discord.FFmpegPCMAudio(
                filename,
                **ffmpeg_options),
            data=data
        )
