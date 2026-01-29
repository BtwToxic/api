import sys, os, asyncio, secrets, time, json
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
import redis
from pathlib import Path

# -------- CONFIG --------
YOUR_VPS_IP = "103.25.175.169"   # Replace with VPS IP
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
CACHE_TTL = 1800   # 30 min cache
FREE_KEY_EXPIRY = 86400  # 24h free keys

# -------- REDIS --------
r_cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
r_queue = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
r_keys = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# -------- IMPORT yt.py --------
sys.path.append("/opt/yt_engine")   # path to your yt.py
from yt import YouTube
yt = YouTube()

# -------- FASTAPI --------
app = FastAPI(title="YT API PRO SINGLE FILE")

# -------- HELPERS --------
def gen_key(plan="free"):
    key = secrets.token_hex(16)
    r_keys.hset(f"key:{key}", mapping={
        "plan": plan,
        "active": 1,
        "created": int(time.time())
    })
    return key

def revoke(key):
    r_keys.hset(f"key:{key}", "active", 0)

def check_key(key):
    data = r_keys.hgetall(f"key:{key}")
    if not data or data.get("active") != "1":
        return False, "Invalid key"
    # Free key expiry
    if data["plan"]=="free" and int(time.time()) - int(data["created"]) > FREE_KEY_EXPIRY:
        revoke(key)
        return False, "Expired"
    return True, data

def add_to_queue(track, key, priority=0):
    job = {
        "track": track,
        "key": key,
        "priority": priority,
        "time": int(time.time())
    }
    r_queue.zadd("queue", {json.dumps(job): priority})

def pop_queue():
    items = r_queue.zrange("queue", 0, 0)
    if not items:
        return None
    r_queue.zrem("queue", items[0])
    return json.loads(items[0])

# -------- ADMIN ENDPOINTS --------
@app.post("/key/gen")
def api_gen_key(plan: str = "free"):
    key = gen_key(plan)
    return {"api_key": key, "plan": plan}

@app.post("/key/revoke")
def api_revoke(key: str):
    revoke(key)
    return {"revoked": True}

# -------- PLAY ENDPOINT --------
@app.get("/v1/play")
async def play(key: str, song: str):
    ok, data = check_key(key)
    if not ok:
        raise HTTPException(403, data)

    # Redis cache
    cache_key = f"song:{song}"
    cached = r_cache.get(cache_key)
    if cached:
        stream_url = cached
    else:
        # Search track
        track = await yt.search(song, m_id=0)
        if not track:
            raise HTTPException(404, "Song not found")
        # Download / prepare
        path = await yt.download(track.id)
        if not path or not Path(path).exists():
            raise HTTPException(500, "Download error")
        stream_url = f"http://{YOUR_VPS_IP}:8000/stream/{os.path.basename(path)}"
        r_cache.setex(cache_key, CACHE_TTL, stream_url)

    # Queue + priority
    priority = 10 if data["plan"]=="pro" else 0
    add_to_queue(song, key, priority)

    return {"title": song, "stream_url": stream_url, "plan": data["plan"]}

# -------- STREAM FILE --------
@app.get("/stream/{file}")
def stream(file: str):
    path = f"downloads/{file}"
    if not Path(path).exists():
        raise HTTPException(404, "File not found")
    return FileResponse(path)

# -------- QUEUE POP EXAMPLE --------
@app.get("/queue/pop")
def get_next():
    job = pop_queue()
    if not job:
        return {"queue": "empty"}
    return job
