# utils/api_downloader.py

import aiohttp
import asyncio
import logging
from config import SHRUTI_API_URL, SHRUTI_API_KEY

logger = logging.getLogger(__name__)

class ShrutiDownloader:
    
    @staticmethod
    async def get_audio(video_id: str) -> dict:
        """
        ShrutiBots API से Audio Download Link प्राप्त करें
        Returns: {
            'success': True/False,
            'url': 'direct_download_link' or None,
            'error': 'error_message' or None,
            'title': 'Song Title'
        }
        """
        if not SHRUTI_API_KEY:
            logger.error("Shruti API Key not set!")
            return {'success': False, 'error': 'API Key missing'}
        
        params = {
            'api_key': SHRUTI_API_KEY,
            'video_id': video_id,
            'format': 'mp3'  # Audio के लिए
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{SHRUTI_API_URL}/download",
                    params=params,
                    timeout=30
                ) as resp:
                    data = await resp.json()
                    
                    if data.get('status') == 'success':
                        return {
                            'success': True,
                            'url': data.get('download_url'),
                            'title': data.get('title', 'Unknown Song'),
                            'duration': data.get('duration', 0)
                        }
                    else:
                        error_msg = data.get('message', 'Unknown API error')
                        logger.error(f"API Error: {error_msg}")
                        return {'success': False, 'error': error_msg}
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network Error: {e}")
            return {'success': False, 'error': f'Network Error: {e}'}
        except asyncio.TimeoutError:
            logger.error("API Request Timeout")
            return {'success': False, 'error': 'Request Timeout'}
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")
            return {'success': False, 'error': str(e)}
