import os
import asyncio
import typing
import yt_dlp as youtube_dl
import models


async def _from_url(url: str, download_path: str, *, loop: asyncio.AbstractEventLoop = None, download: bool = False)\
        -> typing.Dict:
    ytdl_format_options = get_ytdl_format_options(download_path)
    yt_dl = youtube_dl.YoutubeDL(ytdl_format_options)

    loop = loop or asyncio.get_event_loop()
    query_data = await loop.run_in_executor(None, lambda: yt_dl.extract_info(
        url,
        download=download,
    ))

    if 'entries' in query_data:
        # This means that we are in a playlist, ake the first item from a playlist
        song_data = query_data['entries'][0]
    else:
        song_data = query_data

    filename = yt_dl.prepare_filename(song_data)

    data = {
        "id": song_data.get("id"),
        "filename": filename,
        "title": song_data.get("title"),
        "url": song_data.get("original_url"),
        "author": song_data.get("channel")
    }
    return data


def get_ytdl_format_options(download_path: str):
    ytdl_format_options = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_path, '%(id)s.mp3'),
        # 'download_archive': os.path.join(download_path, 'archive.txt'),
        # 'no_overwrites': True,
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

    return ytdl_format_options


async def search(search: str, download_path: str, loop: asyncio.AbstractEventLoop = None) -> typing.Dict:
    ytdl_format_options = get_ytdl_format_options(download_path)
    yt_dl = youtube_dl.YoutubeDL(ytdl_format_options)

    loop = loop or asyncio.get_event_loop()
    query_data = await loop.run_in_executor(None, lambda: yt_dl.extract_info(
        f"ytsearch:{search}",
        download=False
    ))

    filename = yt_dl.prepare_filename(query_data)

    data = {
        "id": query_data.get("id"),
        "filename": filename,
        "title": query_data.get("title"),
        "url": query_data.get("original_url"),
        "author": query_data.get("channel")
    }
    return data


def file_exists(path: str) -> bool:
    return os.path.isfile(path)


async def yt_dl_from_url(url: str, download_path: str, *, loop: asyncio.AbstractEventLoop = None)\
        -> models.Song:
    # TODO: Option to disable prefetch
    # search_data = await search(url, download_path)
    # data = await _from_url(url, download_path, loop=loop, download=False)
    # if file_exists(data.get("filename")):
    #     return data

    data = await _from_url(url, download_path, loop=loop, download=True)
    song = models.Song(
        song_id=data.get("id"),
        title=data.get("title"),
        url=data.get("url"),
        author=data.get("author"),
        filename=data.get("filename")
    )
    return data

