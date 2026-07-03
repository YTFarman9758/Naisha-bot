"""
🎆 Light Mode — when enabled for a chat, instead of streaming plain audio
(with a static assistant photo in the VC), the bot renders a colorful,
audio-reactive "disco light" visualizer video (using ffmpeg's built-in
`showcqt` filter, which draws bars that jump with the music's frequencies)
and streams THAT — audio and visual perfectly in sync since both come from
the same source file.
"""
import asyncio
import hashlib
import os

LIGHT_MODE_CHATS = set()  # in-memory toggle; resets on restart

VISUALIZER_DIR = "downloads/visualizer"
os.makedirs(VISUALIZER_DIR, exist_ok=True)


def is_light_mode(chat_id: int) -> bool:
    return chat_id in LIGHT_MODE_CHATS


def enable_light_mode(chat_id: int):
    LIGHT_MODE_CHATS.add(chat_id)


def disable_light_mode(chat_id: int):
    LIGHT_MODE_CHATS.discard(chat_id)


async def generate_visualizer(audio_path: str) -> str:
    """
    Renders `audio_path` into a colorful audio-reactive video (bars that
    jump with the beat, like a disco light) and returns the path to the
    merged video file (video + original audio).

    Cached by a hash of the input path so replaying the same file doesn't
    re-render every time. Falls back to the original audio_path (silently
    disabling the visual for that play) if ffmpeg fails for any reason,
    so a broken/unusual file never breaks playback.
    """
    if not os.path.exists(audio_path):
        return audio_path

    key = hashlib.md5(os.path.abspath(audio_path).encode()).hexdigest()
    out_path = os.path.join(VISUALIZER_DIR, f"{key}.mp4")

    if os.path.exists(out_path):
        return out_path

    # showcqt: colorful frequency-bar spectrum that visually "jumps" with
    # the music — the closest built-in ffmpeg filter to a disco light.
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-filter_complex",
        "[0:a]showcqt=s=1280x720:fps=30:bar_g=2,format=yuv420p[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        out_path,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0 or not os.path.exists(out_path):
            print(f"[LightMode] ffmpeg failed, falling back to plain audio: {stderr.decode()[-500:]}")
            return audio_path
        return out_path
    except Exception as e:
        print(f"[LightMode] visualizer generation failed, falling back to plain audio: {e}")
        return audio_path
