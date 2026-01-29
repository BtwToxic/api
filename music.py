
import os
import requests
import asyncio
import logging

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
    name="music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

vc = PyTgCalls(app)

# ================= DEBUG WATCHER (Har Message Print Karega) =================
# Ye check karega ki bot message dekh pa raha hai ya nahi
@app.on_message(filters.text, group=-1)
async def watcher(_, message):
    print(f"👀 Message Seen: '{message.text}' from {message.from_user.id if message.from_user else 'Unknown'}")

# ================= PLAY COMMAND =================
# 'filters.group' hata diya hai taaki PM me bhi check kar sako
# 'filters.me' add kiya hai taaki khud ke commands bhi chalne
@app.on_message(filters.command("play", prefixes=["/", "!", "."]))
async def play(client, message):
    print("✅ Play Command Triggered!") 

    if len(message.command) < 2:
        return await message.reply("❌ Usage: `/play song name`")

    query = " ".join(message.command[1:])
    m = await message.reply(f"🔎 **Searching:** `{query}`...")

    try:
        r = requests.get(YT_API, params={"key": API_KEY, "song": query})
        data = r.json()
        
        if "error" in data:
            return await m.edit(f"❌ API Error: {data['error']}")

        stream_url = data.get("stream_url")
        title = data.get("title", query)

        if not stream_url:
            return await m.edit("❌ Song not found.")

    except Exception as e:
        return await m.edit(f"❌ API Error: {e}")

    try:
        # Playing logic
        stream = MediaStream(stream_url, video_flags=MediaStream.Flags.IGNORE)
        await vc.play(message.chat.id, stream)
        await m.edit(f"▶️ **Now Playing:** `{title}`")
    except Exception as e:
        await m.edit(f"❌ VC Error: {e}")

# ================= START =================
async def main():
    print("🔄 Starting Bot...")
    await app.start()
    print("✅ Bot Started. Waiting for commands...")
    
    await vc.start()
    print("✅ PyTgCalls Started.")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
