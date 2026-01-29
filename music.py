import os
import requests
import asyncio
import logging
from hydrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# ================= LOGGING (ERROR DEKHNE KE LIYE) =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ================= CONFIG =================
# ⚠️ Apna API_ID, HASH aur SESSION dhyan se daalein
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

# ================= PING COMMAND (TESTING) =================
# Pehle ye check karo ki bot zinda hai ya nahi
@app.on_message(filters.command("ping", prefixes=["/", "!", "."]))
async def ping(client, message):
    print(f"Ping received from {message.chat.title or message.chat.first_name}")
    await message.reply("✅ **Bot is Alive!**")

# ================= PLAY COMMAND =================
# Prefixes add kiye hain: /play, .play, !play sab chalega
@app.on_message(filters.command("play", prefixes=["/", "!", "."]))
async def play(client, message):
    print(f"Play command received in: {message.chat.id}") # Terminal me print hoga

    if len(message.command) < 2:
        return await message.reply("❌ **Usage:** `/play song name`")

    query = " ".join(message.command[1:])
    m = await message.reply(f"🔎 **Searching:** `{query}`...")

    try:
        # API Request
        print(f"Requesting API for: {query}")
        r = requests.get(YT_API, params={"key": API_KEY, "song": query})
        
        if r.status_code != 200:
            print("API Status Code Error")
            return await m.edit("❌ API Down.")
            
        data = r.json()
        
        if "error" in data:
            print(f"API Error: {data['error']}")
            return await m.edit(f"❌ API Error: {data['error']}")

        stream_url = data.get("stream_url")
        title = data.get("title", query)

        if not stream_url:
            return await m.edit("❌ Link nahi mila.")

    except Exception as e:
        print(f"Exception in Fetching: {e}")
        return await m.edit(f"❌ Error: {e}")

    # Stream Setup
    try:
        print(f"Joining VC for: {title}")
        stream = MediaStream(
            stream_url,
            video_flags=MediaStream.Flags.IGNORE
        )

        await vc.play(message.chat.id, stream)
        await m.edit(f"▶️ **Now Playing:** `{title}`")
        print("Playing successfully")
        
    except Exception as e:
        print(f"VC Error: {e}")
        await m.edit(f"❌ **VC Error:** {e}\n\nCheck Terminal for logs.")

# ================= START =================
async def main():
    print("🔄 Connecting to Telegram...")
    try:
        await app.start()
        me = await app.get_me()
        print(f"✅ Bot Logged in as: {me.first_name} (@{me.username})")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    print("🔄 Starting PyTgCalls...")
    await vc.start()
    print("✅ System Ready! Send /ping to check.")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
        
