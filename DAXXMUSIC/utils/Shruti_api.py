import aiohttp
import asyncio
import os
import logging
from config import SHRUTI_API_KEY, SHRUTI_API_URL

logger = logging.getLogger(__name__)

async def shruti_download_audio(video_id: str, file_path: str) -> str:
    """ShrutiBots API से Audio डाउनलोड करें"""
    if not SHRUTI_API_KEY:
        logger.warning("SHRUTI_API_KEY not set in .env!")
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SHRUTI_API_URL}/download",
                params={
                    "api_key": SHRUTI_API_KEY,
                    "video_id": video_id,
                    "format": "mp3"
                },
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Shruti API Error: HTTP {resp.status}")
                    return None

                data = await resp.json()
                download_url = data.get("download_url") or data.get("url")

                if not download_url:
                    logger.warning("No download URL in Shruti response")
                    return None

                async with session.get(download_url) as dl_resp:
                    if dl_resp.status != 200:
                        return None
                    with open(file_path, "wb") as f:
                        async for chunk in dl_resp.content.iter_chunked(131072):
                            f.write(chunk)

                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return file_path
                return None

    except Exception as e:
        logger.error(f"Shruti download failed: {e}")
        return None

async def shruti_download_video(video_id: str, file_path: str) -> str:
    """ShrutiBots API से Video डाउनलोड करें"""
    if not SHRUTI_API_KEY:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SHRUTI_API_URL}/download",
                params={
                    "api_key": SHRUTI_API_KEY,
                    "video_id": video_id,
                    "format": "mp4"
                },
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()
                download_url = data.get("download_url") or data.get("url")

                if not download_url:
                    return None

                async with session.get(download_url) as dl_resp:
                    if dl_resp.status != 200:
                        return None
                    with open(file_path, "wb") as f:
                        async for chunk in dl_resp.content.iter_chunked(131072):
                            f.write(chunk)

                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return file_path
                return None

    except Exception as e:
        logger.error(f"Shruti video download failed: {e}")
        return None
