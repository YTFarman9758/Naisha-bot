import requests

from requests import get

from DAXXMUSIC import app

from pyrogram import filters

from pyrogram.types import InputMedia Photo

@app.on_message(filters.command(["image"], prefixes=["/", "1", "%", ".", ""."

async def pinterest(, message):

chat_id = message.chat.id

try:

query message.text.split(None,1) [1]

except:

return await message.reply("**GIVE IMAGE NAME FOR SEARCH **")

images get(f"https://pinterest-api-one.vercel.app/?q={query}").json()

media_group= []

count = 0

msg await message.reply(f"SCRAPING IMAGES FROM PINTERETS...")

for url in images["images"] [:6]:

media_group.append(InputMediaPhoto(media=url))

count += 1

await msg.edit(f"=> owo SCRAPED IMAGES {count}")

await app.send_media_group(

chat_id=chat_id,

media-media_group, reply_to_message_id=message.id)

return await msg.delete()

except Exception as e:

await msg.delete()

return await message.reply(f"ERROR: {e}")
