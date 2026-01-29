import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# ================= CONFIG =================

API_ID = 21705136
API_HASH = "78730e89d196e160b0f1992018c6cb19"

BOT_TOKEN = "8094733589:AAGTYB6rmrT5Z7UOrRAxTBfbdzthlV9hZW4"   
USER_SESSION = "BQHjcR4AqDhgN5wBQ0HGXdB-EuCqpJR-X5WSkzIl4rtnE2Th0GuKdTkiB7cBGv1yQktvkMX_IYNbmyc50ttgcbbiEh1aq9zRsZqsulQmLz412A_2PCC2z6iN0S0_09c2KgS-iB-MZppIs2ejlfFRwt1_lzzvsJdDC2BD6LkCKx_BXTS2xiXOLqBcraop--fRM1LxQ0i3BkZVfgAPnURFuJLhiWpF7HlmrlvHalduG6Q2zKw6hAtcnTbtZmmcM58U8oXdt3_KYMgi1s4BDiT31_lf6ncgcJZnZd3XH4sXX4EBYZne4uSiH2fVa-ChQN8Ff74YbJQo15NqD-dXpYY7P9o_kDPRngAAAAGd7PcCAA"  

YT_API = "http://103.25.175.169:8000/toxic/api"
API_KEY = "3e8abdb2e25f02a53dcdef45eb20790e"

# ================= CLIENTS =================

bot = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

userbot = Client(
    "assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_name=USER_SESSION, # Change session_string to session_name
    in_memory=True
)


vc = PyTgCalls(userbot)

# ================= HELPER =================

async def ensure_assistant(chat_id):
    try:
        await userbot.get_chat_member(chat_id, "me")
        return
    except:
        link = await bot.create_chat_invite_link(chat_id, member_limit=1)
        await userbot.join_chat(link.invite_link)

# ================= PLAY COMMAND =================

@bot.on_message(filters.command("play") & filters.group)
async def play_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply("❌ Usage: /play song name")

    query = " ".join(message.command[1:])
    msg = await message.reply("🔎 Searching...")

    try:
        await ensure_assistant(message.chat.id)

        r = requests.get(
            YT_API,
            params={"key": API_KEY, "song": query},
            timeout=15
        ).json()

        if "stream_url" not in r:
            return await msg.edit("❌ Song not found")

        await vc.play(
            message.chat.id,
            MediaStream(r["stream_url"])
        )

        await msg.edit(f"▶️ Now Playing: `{r.get('title', query)}`")

    except Exception as e:
        await msg.edit(f"❌ Error: `{e}`")

# ================= START =================

async def main():
    await bot.start()
    await userbot.start()
    await vc.start()
    print("✅ Bot + Assistant Online")
    await asyncio.Event().wait()

asyncio.run(main())
