import asyncio
import json
import os
import re
from typing import Union
from pytgcalls.types.input_stream import InputStream
from pytgcalls.types.input_stream import InputAudioStream

import aiohttp
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from DAXXMUSIC.utils.database import is_on_off
from DAXXMUSIC.utils.formatters import time_to_seconds


import os
import glob
import random
import logging

def cookie_txt_file():
    """Deprecated: this bot no longer uses cookies. Kept as a no-op so any
    stray reference elsewhere doesn't crash; returns None."""
    return None


# ---------------------------------------------------------------------------
# API-based download (shrutibots) — used as the primary download method.
# Falls back to cookie-free yt-dlp (below) if the API fails or is unreachable.
# ---------------------------------------------------------------------------
API_URL = os.environ.get("SHRUTI_API_URL", "https://api01.shrutibots.site")
_DEFAULT_SHRUTI_KEY = "ShrutiBotsCMJel4aMwKOc8ZHhkWHr"
API_KEY = os.environ.get("SHRUTI_API_KEY", _DEFAULT_SHRUTI_KEY)  ## Get this API KEY from Telegram bot: @SHRUTIAPIBOT

if API_KEY == _DEFAULT_SHRUTI_KEY:
    print(
        "[ShrutiAPI] WARNING: SHRUTI_API_KEY env var is not set (or failed to load) — "
        "using the shared default demo key. This is likely rate-limited/unreliable. "
        "Get your own key from @SHRUTIAPIBOT on Telegram and set SHRUTI_API_KEY."
    )
else:
    print("[ShrutiAPI] Using your own SHRUTI_API_KEY from the environment.")


def _extract_video_id(link: str) -> str:
    if "v=" in link:
        return link.split("v=")[-1].split("&")[0]
    if "youtu.be/" in link:
        return link.split("youtu.be/")[-1].split("?")[0]
    return link


async def api_download_song(link: str) -> str:
    """Download audio via the shrutibots API. Returns file path or None on failure."""
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params={"url": video_id, "type": "audio", "api_key": API_KEY},
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                if resp.status != 200:
                    body_preview = (await resp.text())[:300]
                    logging.warning(
                        f"[shrutibots API] audio request failed: HTTP {resp.status} — {body_preview}"
                    )
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception as e:
        logging.warning(f"[shrutibots API] audio download failed: {e}")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


async def api_download_video(link: str) -> str:
    """Download video via the shrutibots API. Returns file path or None on failure."""
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params={"url": video_id, "type": "video", "api_key": API_KEY},
                timeout=aiohttp.ClientTimeout(total=600),
            ) as resp:
                if resp.status != 200:
                    body_preview = (await resp.text())[:300]
                    logging.warning(
                        f"[shrutibots API] video request failed: HTTP {resp.status} — {body_preview}"
                    )
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception as e:
        logging.warning(f"[shrutibots API] video download failed: {e}")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


# ---------------------------------------------------------------------------
# Cookie-free YouTube access (fallback path).
# We avoid --cookies / cookiefile entirely and instead ask yt-dlp to use the
# "android" / "web" InnerTube player clients, which (unlike the default web
# client) do not require a signed-in session to fetch playback URLs. If
# YouTube tightens this further in the future, keep yt-dlp itself updated
# (`pip install -U yt-dlp`) — this trick relies on yt-dlp's extractor, not on
# this bot's code.
# ---------------------------------------------------------------------------
NO_COOKIE_YTDL_OPTS = {
    "geo_bypass": True,
    "nocheckcertificate": True,
    "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
}
NO_COOKIE_CLI_ARGS = ["--extractor-args", "youtube:player_client=android,ios,tv_embedded,web"]



async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            *NO_COOKIE_CLI_ARGS,
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format:
                total_size += format['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        print("No formats found.")
        return None
    
    total_size = parse_size(formats)
    return total_size

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        """
        Returns a direct streamable URL (used by pytgcalls InputStream).
        This stays on yt-dlp's -g flag since the API only returns downloadable
        files, not a direct stream URL.
        """
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            *NO_COOKIE_CLI_ARGS,
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --extractor-args \"youtube:player_client=android,ios,tv_embedded,web\" --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True, **NO_COOKIE_YTDL_OPTS}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        def audio_dl_ytdlp():
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl_ytdlp():
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {"youtube": {"player_client": ["android", "ios", "tv_embedded", "web"]}},
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        # format_id-specific downloads (used by /songvideo and /songaudio) stay
        # on yt-dlp since the API doesn't support arbitrary format selection.
        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath
        elif video:
            if await is_on_off(1):
                # API first, yt-dlp fallback
                direct = True
                downloaded_file = await api_download_video(link)
                if not downloaded_file:
                    logging.warning("[shrutibots API] video download failed, falling back to yt-dlp")
                    downloaded_file = await loop.run_in_executor(None, video_dl_ytdlp)
            else:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    *NO_COOKIE_CLI_ARGS,
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    f"{link}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = False
                else:
                   file_size = await check_file_size(link)
                   if not file_size:
                     print("None file Size")
                     return
                   total_size_mb = file_size / (1024 * 1024)
                   if total_size_mb > 250:
                     print(f"File size {total_size_mb:.2f} MB exceeds the 100MB limit.")
                     return None
                   direct = True
                   downloaded_file = await api_download_video(link)
                   if not downloaded_file:
                       downloaded_file = await loop.run_in_executor(None, video_dl_ytdlp)
        else:
            # Plain audio download — API first, yt-dlp fallback
            direct = True
            downloaded_file = await api_download_song(link)
            if not downloaded_file:
                logging.warning("[shrutibots API] audio download failed, falling back to yt-dlp")
                downloaded_file = await loop.run_in_executor(None, audio_dl_ytdlp)
        return downloaded_file, direct
