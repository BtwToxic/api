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
    name="assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION,
    in_memory=True # Pyrogram session compatibility ke liye
)

vc = PyTgCalls(app)

# ================= PLAY COMMAND =================
# Assistant ke liye 'group=1' rakha hai aur filters simplify kiye hain
@app.on_message(filters.command("play", prefixes=["/", ".", "!"]))
async def play_cmd(client, message):
    # Log to check if command is received
    print(f"📥 Command Received: {message.text}")
    
    if len(message.command) < 2:
        return await message.reply("❌ Usage: `/play song name`")

    query = " ".join(message.command[1:])
    m = await message.reply(f"🔎 Searching: `{query}`...")

    try:
        r = requests.get(YT_API, params={"key": API_KEY, "song": query}, timeout=15)
        data = r.json()
        
        if "stream_url" not in data:
            return await m.edit("❌ Song not found in API.")

        stream_url = data["stream_url"]
        title = data.get("title", "Music")

        # Playing Logic
        await vc.play(
            message.chat.id,
            MediaStream(stream_url)
        )
        await m.edit(f"▶️ **Now Playing:** `{title}`")

    except Exception as e:
        print(f"❌ Error: {e}")
        await m.edit(f"❌ Error: {e}")

# ================= START =================
async def main():
    await app.start()
    await vc.start()
    print("✅ Assistant is Online!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    
