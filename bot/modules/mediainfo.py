from os import getcwd, path as ospath
from re import search
from shlex import split
from bs4 import BeautifulSoup
from aiofiles import open as aiopen
from aiofiles.os import mkdir, path as aiopath, remove as aioremove
from aiohttp import ClientSession
import httpx

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
        
async def gen_mediainfo(message, link=None, media=None, mmsg=None):
    temp_send = await send_message(message, "<i>Generating MediaInfo...</i>")
    try:
        path = "mediainfo/"
        if not await aiopath.isdir(path):
            await mkdir(path)
        file_size = 0
        if link:
            filename = search(".+/(.+)", link).group(1)
            des_path = ospath.join(path, filename)
            headers = {
                "user-agent": "Mozilla/5.0 (Linux; Android 12; 2201116PI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36"
            }
            async with ClientSession() as session:
                async with session.get(link, headers=headers) as response:
                    file_size = int(response.headers.get("Content-Length", 0))
                    async with aiopen(des_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(10000000):
                            await f.write(chunk)
                            break
        elif media:
            des_path = ospath.join(path, media.file_name)
            file_size = media.file_size
            if file_size <= 50000000:
                await mmsg.download(ospath.join(getcwd(), des_path))
            else:
                async for chunk in TgClient.bot.stream_media(media, limit=5):
                    async with aiopen(des_path, "ab") as f:
                        await f.write(chunk)

        stdout, _, _ = await cmd_exec(split(f'mediainfo "{des_path}"'))
        tc = f"📌 {ospath.basename(des_path)}\n\n"
        if len(stdout) != 0:
            tc += parseinfo(stdout, file_size)

        # Paste the MediaInfo output to katb.in
        katb_link = await katbin_paste(tc)

    except Exception as e:
        LOGGER.error(e)
        await edit_message(temp_send, f"MediaInfo Stopped due to {str(e)}")
    finally:
        await aioremove(des_path)

    await temp_send.edit(
        f"<b>MediaInfo:</b>\n\n➲ <b>Link :</b> {katb_link}",
        disable_web_page_preview=False,
    )


section_dict = {
    "General": "🗒", 
    "Video": "🎞", 
    "Audio": "🔊", 
    "Text": "🔠", 
    "Menu": "🗃"
}

def parseinfo(out, size):
    tc = ""
    size_line = f"File size                                 : {size / (1024 * 1024):.2f} MiB"
    trigger = False
    skip_conformance_errors = False

    for line in out.splitlines():
        # Check for section headers and format accordingly
        for section, emoji in section_dict.items():
            if line.startswith(section):
                if trigger:
                    tc += "\n"  # Close previous section
                tc += f"{emoji} {line.replace('Text', 'Subtitle')}\n"
                trigger = True
                skip_conformance_errors = False
                break
        else:
            if line.startswith("Conformance errors"):
                skip_conformance_errors = True
            elif skip_conformance_errors and (line.startswith("0x") or line.startswith("General compliance")):
                continue
            if line.startswith("File size"):
                line = size_line
            
            if trigger:
                tc += line + "\n"  
            else:
                tc += line + "\n"

    if trigger:
        tc += "\n"

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
