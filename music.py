import asyncio
import requests

from pyrogram import Client, filters
from pytgcalls import PyTgCallsClient
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream.quality import HighQualityAudio

# ================= CONFIG =================
API_ID = 21705136
API_HASH = "78730e89d196e160b0f1992018c6cb19"
SESSION = "BQHjcR4AkzdKizjCZVXQ4KhaaS1IUvjvsBjIlNySDNNSskwJGwrql4RhgW3MBAlAfjJVXB2fM-aH0AmJBcVWYyuVSuDMw9D5493u7v60qDsbpRzD0vnFcHxzCSn0MRLacfgpYhtM-8_n0Qzcso8ety4NpASwXYSuXz1vFXWA5LRsXyKhkwE1bHroYix1rGkjkPCTY_bC3Uby3V5RMxckxlhf8ivZX098cZNutTw_yNXEod2ILMjwG6Taswze1wuD4u29p5GCRPP7wU56FYLB5DtH6qpWiq26vUcZZJifV2S7HUTPGatyIBhLmbbFOTX7aGczONHZgtwRqFUjRlOwz-26zlDAPwAAAAGd7PcCAA"

YT_API = "http://103.25.175.169:8000/toxic/api"
API_KEY = "3e8abdb2e25f02a53dcdef45eb20790e"

# ================= CLIENT =================
app = Client(
    "music",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

vc = PyTgCallsClient(app)

# ================= COMMAND =================
@app.on_message(filters.command("play") & filters.group)
async def play(_, message):
    if len(message.command) < 2:
        return await message.reply("❌ Usage: /play song name")

    song = " ".join(message.command[1:])
    await message.reply(f"🔎 Searching **{song}**")

    # API call
    r = requests.get(YT_API, params={
        "key": API_KEY,
        "song": song
    })

    if r.status_code != 200:
        return await message.reply("❌ API error")

    data = r.json()
    stream_url = data["stream_url"]
    title = data.get("title", song)

    # JOIN / CHANGE VC STREAM
    try:
        await vc.join_group_call(
            message.chat.id,
            InputAudioStream(
                stream_url,
                HighQualityAudio()
            )
        )
    except:
        await vc.change_stream(
            message.chat.id,
            InputAudioStream(
                stream_url,
                HighQualityAudio()
            )
        )

    await message.reply(f"▶️ **Now Playing:** `{title}`")

# ================= START =================
async def main():
    await app.start()
    await vc.start()
    print("🎵 VC Music Bot Started")
    await asyncio.Event().wait()

asyncio.run(main())
