from pyrogram import filters
from pyrogram.types import Message

from DAXXMUSIC import app
from DAXXMUSIC.utils.daxx_ban import admin_filter
from DAXXMUSIC.utils.visualizer import (
    is_light_mode,
    enable_light_mode,
    disable_light_mode,
)


@app.on_message(filters.command(["light"]) & filters.group & admin_filter)
async def light_toggle(client, message: Message):
    chat_id = message.chat.id

    if len(message.command) < 2:
        status = "🟢 ON" if is_light_mode(chat_id) else "🔴 OFF"
        return await message.reply_text(
            f"🎆 <b>Light Mode:</b> {status}\n\n"
            f"Usage: <code>/light on</code> or <code>/light off</code>\n\n"
            f"When ON, songs play with a colorful audio-reactive light "
            f"visualizer video in the voice chat instead of a static photo."
        )

    arg = message.command[1].lower()
    if arg in ("on", "enable"):
        enable_light_mode(chat_id)
        await message.reply_text(
            "🎆 <b>Light Mode enabled!</b>\n\n"
            "From the next song played, you'll see a colorful audio-reactive "
            "visualizer in the voice chat instead of a static photo.\n\n"
            "<i>Note: this adds a few extra seconds before playback starts, "
            "since the light video is rendered on the fly.</i>"
        )
    elif arg in ("off", "disable"):
        disable_light_mode(chat_id)
        await message.reply_text("🎆 <b>Light Mode disabled.</b> Back to normal playback.")
    else:
        await message.reply_text("Usage: <code>/light on</code> or <code>/light off</code>")
