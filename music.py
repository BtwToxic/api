import os
import requests
import asyncio

from hydrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# ================= CONFIG =================
API_ID = 21705136
API_HASH = "78730e89d196e160b0f1992018c6cb19"
SESSION = "BQHjcR4AkzdKizjCZVXQ4KhaaS1IUvjvsBjIlNySDNNSskwJGwrql4RhgW3MBAlAfjJVXB2fM-aH0AmJBcVWYyuVSuDMw9D5493u7v60qDsbpRzD0vnFcHxzCSn0MRLacfgpYhtM-8_n0Qzcso8ety4NpASwXYSuXz1vFXWA5LRsXyKhkwE1bHroYix1rGkjkPCTY_bC3Uby3V5RMxckxlhf8ivZX098cZNutTw_yNXEod2ILMjwG6Taswze1wuD4u29p5GCRPP7wU56FYLB5DtH6qpWiq26vUcZZJifV2S7HUTPGatyIBhLmbbFOTX7aGczONHZgtwRqFUjRlOwz-26zlDAPwAAAAGd7PcCAA"

YT_API = "http://103.25.175.169:8000/toxic/api"
API_KEY = "3e8abdb2e25f02a53dcdef45eb20790e"

# ================= CLIENT =================
app = Client(
    name="music",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

vc = PyTgCalls(app)

# ================= PLAY COMMAND =================
@app.on_message(filters.command("play") & filters.group)
async def play(_, message):
    if len(message.command) < 2:
        return await message.reply("❌ Usage: /play song name")

    song = " ".join(message.command[1:])
    m = await message.reply(f"🔎 Searching **{song}**")

    try:
        r = requests.get(YT_API, params={"key": API_KEY, "song": song})
        data = r.json()
        stream_url = data["stream_url"]
        title = data.get("title", song)
    except Exception as e:
        return await m.edit(f"❌ API Error: {e}")

    # Latest PyTgCalls (v2.x) syntax
    stream = MediaStream(stream_url)

    try:
        await vc.play(message.chat.id, stream)
        await m.edit(f"▶️ **Now Playing:** `{title}`")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

# ================= START =================
async def main():
    await app.start()
    await vc.start()
    print("🎵 Music Bot Started with Hydrogram!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    
