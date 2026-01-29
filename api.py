import os, asyncio, secrets, time, json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

import redis
import yt_dlp

# ================= CONFIG =================
YOUR_VPS_IP = "103.25.175.169"
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

CACHE_TTL = 1800
FREE_KEY_EXPIRY = 86400
DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ================= REDIS =================
r_cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
r_queue = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
r_keys  = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# ================= FASTAPI =================
app = FastAPI(title="YT Audio Streaming API")

# ================= YT LOGIC =================
class YTApi:
    base = "https://www.youtube.com/watch?v="

    async def search(self, query: str):
        def _search():
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                data = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if data and data.get("entries"):
                    e = data["entries"][0]
                    return {
                        "id": e["id"],
                        "title": e["title"],
                        "duration": e.get("duration", 0)
                    }
                return None
        return await asyncio.to_thread(_search)

    async def download(self, video_id: str):
        out = f"{DOWNLOAD_FOLDER}/{video_id}.m4a"
        if Path(out).exists():
            return out

        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "format": "bestaudio/best",

            # ✅ MOST STABLE FIX
            "extractor_args": {
                "youtube": {
                    "player_client": ["web"]
                }
            },

            "http_headers": {
                "User-Agent": "Mozilla/5.0"
            },

            "outtmpl": out,
            "merge_output_format": "m4a",
        }

        def _dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.base + video_id])
            return out

        return await asyncio.to_thread(_dl)

yt_api = YTApi()

# ================= KEY SYSTEM =================
def gen_key(plan="free"):
    key = secrets.token_hex(16)
    r_keys.hset(f"key:{key}", mapping={
        "plan": plan,
        "active": 1,
        "created": int(time.time())
    })
    return key

def revoke_key(key: str):
    r_keys.hset(f"key:{key}", "active", 0)

def check_key(key: str):
    data = r_keys.hgetall(f"key:{key}")
    if not data or data.get("active") != "1":
        return False, "Invalid API key"

    if data["plan"] == "free":
        if int(time.time()) - int(data["created"]) > FREE_KEY_EXPIRY:
            revoke_key(key)
            return False, "API key expired"

    return True, data

# ================= QUEUE =================
def add_to_queue(title, key, priority):
    r_queue.zadd(
        "queue",
        {json.dumps({
            "title": title,
            "key": key,
            "time": int(time.time())
        }): priority}
    )

def pop_queue():
    items = r_queue.zrange("queue", 0, 0)
    if not items:
        return None
    r_queue.zrem("queue", items[0])
    return json.loads(items[0])

# ================= ADMIN =================
@app.get("/key")
async def gen_key_web():
    return {"api_key": gen_key("free"), "plan": "free"}

@app.post("/key/revoke")
async def api_revoke(key: str):
    revoke_key(key)
    return {"revoked": True}

# ================= PLAY =================
@app.get("/toxic/api")
async def play(key: str, song: str):
    ok, data = check_key(key)
    if not ok:
        raise HTTPException(403, data)

    cache_key = f"song:{song.lower()}"
    cached = r_cache.get(cache_key)

    if cached:
        return {"stream_url": cached, "plan": data["plan"]}

    track = await yt_api.search(song)
    if not track:
        raise HTTPException(404, "Song not found")

    path = await yt_api.download(track["id"])
    if not Path(path).exists():
        raise HTTPException(500, "Download failed")

    stream_url = f"http://{YOUR_VPS_IP}:8000/stream/{os.path.basename(path)}"
    r_cache.setex(cache_key, CACHE_TTL, stream_url)

    priority = 10 if data["plan"] == "pro" else 0
    add_to_queue(track["title"], key, priority)

    return {
        "title": track["title"],
        "stream_url": stream_url,
        "plan": data["plan"]
    }

# ================= STREAM =================
@app.get("/stream/{file}")
async def stream(file: str):
    path = f"{DOWNLOAD_FOLDER}/{file}"
    if not Path(path).exists():
        raise HTTPException(404, "File not found")
    return FileResponse(path)

# ================= QUEUE POP =================
@app.get("/queue/pop")
async def queue_pop():
    job = pop_queue()
    return job or {"queue": "empty"}
