import os
import requests
import asyncio

from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped

# ================= CONFIG =================
API_ID = 
API_HASH = ""
SESSION = ""

CHAT_ID = -1001234567890   # VC wala group ID

YT_API = "http://103.25.175.169:8000/toxic/api"
API_KEY = "3e8abdb2e25f02a53dcdef45eb20790e"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ================= CLIENT =================
app = Client(SESSION, api_id=API_ID, api_hash=API_HASH)
vc = PyTgCalls(app)

# ================= HELPERS =================
def download_audio(url: str) -> str:
    filename = url.split("/")[-1]
    path = f"{DOWNLOAD_DIR}/{filename}"

    if os.path.exists(path):
        return path

    r = requests.get(url, stream=True)
    r.raise_for_status()

    with open(path, "wb") as f:
        for chunk in r.iter_content(1024 * 64):
            f.write(chunk)

    return path

# ================= COMMAND =================
@app.on_message(filters.command("play") & filters.group)
async def play_handler(_, message):
    if len(message.command) < 2:
        await message.reply("❌ Usage: `/play song name`")
        return

    song = " ".join(message.command[1:])
    await message.reply(f"🔎 Searching: **{song}**")

    # 1️⃣ API CALL
    r = requests.get(YT_API, params={
        "key": API_KEY,
        "song": song
    })

    if r.status_code != 200:
        await message.reply("❌ API error")
        return

    data = r.json()
    stream_url = data["stream_url"]
    title = data.get("title", song)

    # 2️⃣ DOWNLOAD
    audio_path = download_audio(stream_url)

    # 3️⃣ PLAY
    try:
        await vc.join_group_call(
            message.chat.id,
            AudioPiped(audio_path)
        )
    except:
        await vc.change_stream(
            message.chat.id,
            AudioPiped(audio_path)
        )

    await message.reply(f"▶️ **Now Playing:** `{title}`")

# ================= START =================
async def main():
    await app.start()
    await vc.start()
    print("🎵 Music bot started")
    await asyncio.Event().wait()

asyncio.run(main())
