from os import getcwd, path as ospath
from shlex import split
from re import search
from bs4 import BeautifulSoup
from aiofiles import open as aiopen
from aiofiles.os import mkdir, path as aiopath, remove as aioremove
from aiohttp import ClientSession
from aiopath import AsyncPath
import httpx
import re

from .. import LOGGER
from ..core.tg_client import TgClient
from ..helper.ext_utils.bot_utils import cmd_exec
from ..helper.ext_utils.telegraph_helper import telegraph
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.message_utils import send_message, edit_message

async def katbin_paste(text: str) -> str:
    """
	paste the text in katb.in website.
	"""

    katbin_url = "https://katb.in"
    client = httpx.AsyncClient()
    response = await client.get(katbin_url)

    soup = BeautifulSoup(response.content, "html.parser")
    csrf_token = soup.find('input', {"name": "_csrf_token"}).get("value")

    try:
        paste_post = await client.post(katbin_url, data={"_csrf_token": csrf_token, "paste[content]": text},
                                       follow_redirects=False)
        output_url = f"{katbin_url}{paste_post.headers['location']}"
        await client.aclose()
        return output_url

    except:
        return "something went wrong while pasting text in katb.in."
        
section_dict = {
    "General": "🗒", 
    "Video": "🎞", 
    "Audio": "🔊", 
    "Text": "🔠", 
    "Menu": "🗃"
}

def get_readable_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    while size_bytes >= 1000 and unit_index < len(units)-1:
        size_bytes /= 1000.0
        unit_index += 1
    return f"{size_bytes:.2f} {units[unit_index]}"

async def gen_mediainfo(message, link=None, media=None, mmsg=None):
    temp_send = await send_message(message, "<i>Generating MediaInfo...</i>")
    try:
        path = "mediainfo/"
        if not await AsyncPath(path).is_dir():
            await AsyncPath(path).mkdir()
        file_size = 0
        if link:
            filename = re.search(".+/(.+)", link).group(1)
            des_path = os.path.join(path, filename)
            headers = {
                "user-agent": "Mozilla/5.0 (Linux; Android 12; 2201116PI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36"
            }
            async with ClientSession() as session:
                async with session.get(link, headers=headers) as response:
                    file_size = int(response.headers.get("Content-Length", 0))
                    async with AsyncPath(des_path).open("wb") as f:
                        async for chunk in response.content.iter_chunked(10000000):
                            await f.write(chunk)
                            break
        elif media:
            des_path = os.path.join(path, media.file_name)
            file_size = media.file_size
            if file_size <= 50000000:
                await mmsg.download(os.path.join(os.getcwd(), des_path))
            else:
                async for chunk in TgClient.bot.stream_media(media, limit=5):
                    async with AsyncPath(des_path).open("ab") as f:
                        await f.write(chunk)

        stdout, _, _ = await cmd_exec(split(f'mediainfo "{des_path}"'))
        tc = f"📌 {os.path.basename(des_path)}\n\n"
        if len(stdout) != 0:
            tc += parseinfo(stdout, file_size)

        # Paste the MediaInfo output to katb.in
        katb_link = await katbin_paste(tc)

    except Exception as e:
        LOGGER.error(e)
        await edit_message(temp_send, f"MediaInfo Stopped due to {str(e)}")
    finally:
        await AsyncPath(des_path).unlink()

    await temp_send.edit(
        f"<b>MediaInfo:</b>\n\n➲ <b>Link :</b> {katb_link}",
        disable_web_page_preview=False,
    )


def parseinfo(out, size):
    tc = ""
    size_line = f"File size : {get_readable_size(size)}"
    in_conformance_errors = False

    for line in out.splitlines():
        # Check for section headers
        section_found = False
        for section, emoji in section_dict.items():
            if line.startswith(section):
                in_conformance_errors = False  # Reset when new section found
                if tc:  # Add newline between sections
                    tc += "\n"
                tc += f"{emoji} {line.replace('Text', 'Subtitle')}\n"
                section_found = True
                break
        
        if section_found:
            continue
        
        # Handle Conformance errors section
        if line.startswith("Conformance errors"):
            in_conformance_errors = True
            continue
        
        if in_conformance_errors:
            continue  # Skip all lines in Conformance errors section
        
        # Process remaining lines
        if line.startswith("File size"):
            tc += f"{size_line}\n"
        elif line.startswith("Complete name"):
            key_part, value_part = line.split(':', 1)
            value_part = value_part.strip()
            filename = os.path.basename(value_part)
            line = f"{key_part}: {filename}"
            tc += f"{line}\n"
        else:
            # Reformat line to have single space after colon
            key_part, value_part = line.split(':', 1)
            value_part = value_part.strip()
            line = f"{key_part}: {value_part}"
            tc += f"{line}\n"

    return tc


async def mediainfo(_, message):
    rply = message.reply_to_message
    help_msg = f"""
<b>By replying to media:</b>
<code>/{BotCommands.MediaInfoCommand[0]} or /{BotCommands.MediaInfoCommand[1]} [media]</code>

<b>By reply/sending download link:</b>
<code>/{BotCommands.MediaInfoCommand[0]} or /{BotCommands.MediaInfoCommand[1]} [link]</code>
"""
    if len(message.command) > 1 or rply and rply.text:
        link = rply.text if rply else message.command[1]
        return await gen_mediainfo(message, link)
    elif rply:
        if file := next(
            (
                i
                for i in [
                    rply.document,
                    rply.video,
                    rply.audio,
                    rply.voice,
                    rply.animation,
                    rply.video_note,
                ]
                if i is not None
            ),
            None,
        ):
            return await gen_mediainfo(message, None, file, rply)
        else:
            return await send_message(message, help_msg)
    else:
        return await send_message(message, help_msg)
