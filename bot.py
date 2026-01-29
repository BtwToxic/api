import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped

# ================= CONFIG =================
API_ID = 21705136
API_HASH = "78730e89d196e160b0f1992018c6cb19"
BOT_TOKEN = "8094733589:AAGTYB6rmrT5Z7UOrRAxTBfbdzthlV9hZW4"

# Assistant Account ka Session (Jo gen_session.py se nikala tha)
STRING_SESSION = "BQHjcR4AqDhgN5wBQ0HGXdB-EuCqpJR-X5WSkzIl4rtnE2Th0GuKdTkiB7cBGv1yQktvkMX_IYNbmyc50ttgcbbiEh1aq9zRsZqsulQmLz412A_2PCC2z6iN0S0_09c2KgS-iB-MZppIs2ejlfFRwt1_lzzvsJdDC2BD6LkCKx_BXTS2xiXOLqBcraop--fRM1LxQ0i3BkZVfgAPnURFuJLhiWpF7HlmrlvHalduG6Q2zKw6hAtcnTbtZmmcM58U8oXdt3_KYMgi1s4BDiT31_lf6ncgcJZnZd3XH4sXX4EBYZne4uSiH2fVa-ChQN8Ff74YbJQo15NqD-dXpYY7P9o_kDPRngAAAAGd7PcCAA" 

API_BASE_URL = "http://103.25.175.169:8000"

# Global Variables
API_KEY = None 

# ================= CLIENTS =================
# 1. Main Bot (Commands ke liye)
bot = Client("main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 2. Assistant Userbot (VC Join karne ke liye)
user = Client("assistant_user", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

# 3. PyTgCalls (Userbot ko wrap karega)
call_py = PyTgCalls(user)

# ================= HELPER FUNCTIONS =================

async def get_api_key():
    global API_KEY
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/key") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    API_KEY = data.get("api_key")
                    print(f"🔑 Key Fetched: {API_KEY}")
                    return API_KEY
        except Exception as e:
            print(f"⚠️ Key Error: {e}")
            return None

async def get_song_stream(query):
    global API_KEY
    if not API_KEY:
        await get_api_key()

    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/toxic/api"
        params = {"key": API_KEY, "song": query}
        
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 403: # Key Expired
                    await get_api_key()
                    params["key"] = API_KEY
                    async with session.get(url, params=params) as r2:
                        return await r2.json() if r2.status == 200 else None
        except Exception as e:
            print(f"API Error: {e}")
            return None
    return None

# ================= COMMANDS =================

@bot.on_message(filters.command("play") & filters.group)
async def play_music(client: Client, message: Message):
    chat_id = message.chat.id
    
    if len(message.command) < 2:
        await message.reply_text("❌ Song name required!\nEx: `/play Diljit`")
        return

    query = " ".join(message.command[1:])
    msg = await message.reply_text(f"🔍 **Searching:** {query}...")

    # 1. API Se Link Nikalo
    data = await get_song_stream(query)
    
    if not data or "stream_url" not in data:
        await msg.edit_text("❌ Song not found on Server (Check VPS API).")
        return

    track_title = data["title"]
    stream_url = data["stream_url"]

    await msg.edit_text(f"⬇️ **Connecting Stream...**\n🎵 {track_title}")

    # 2. Assistant (Userbot) se VC Join karwayo
    try:
        # V2.2.10 Syntax
        await call_py.join_group_call(
            chat_id,
            AudioPiped(stream_url)
        )
        await msg.edit_text(f"▶️ **Playing:** {track_title}\n🔉 Via: Assistant Account")
    
    except Exception as e:
        # Agar already join hai to change stream karo
        if "already connected" in str(e).lower():
            try:
                await call_py.change_stream(
                    chat_id,
                    AudioPiped(stream_url)
                )
                await msg.edit_text(f"▶️ **Playing:** {track_title}\n🔉 Track Changed")
            except Exception as inner_e:
                await msg.edit_text(f"❌ **Change Error:** {inner_e}")
        else:
            await msg.edit_text(f"❌ **Join Error:** {e}\n\nMake sure Assistant is Admin!")

@bot.on_message(filters.command("stop") & filters.group)
async def stop_music(client, message):
    try:
        await call_py.leave_group_call(message.chat.id)
        await message.reply_text("⏹ **Stopped & Left VC.**")
    except Exception as e:
        await message.reply_text("❌ Not connected.")

# ================= RUNNER =================

async def main():
    print("🚀 Starting Clients...")
    await bot.start()
    await user.start()
    await call_py.start()
    
    # Generate initial key
    await get_api_key()
    
    print("✅ System Ready! Bot & Assistant are online.")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
