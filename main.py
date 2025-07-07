import os, uuid, urllib.parse, requests
from fastapi import FastAPI, Request, HTTPException

MATRIX_URL    = os.getenv("MATRIX_URL", "http://localhost:8008")
AS_TOKEN      = os.environ["AS_TOKEN"]                       # must exist
BOT_LOCALPART = os.getenv("BOT_LOCALPART", "webhook_bot")
SERVER_NAME   = os.getenv("SERVER_NAME", "localhost")
USER_ID       = f"@{BOT_LOCALPART}:{SERVER_NAME}"

app = FastAPI()


# ───────────────────────── Matrix helpers ──────────────────────────
def mx_get(path: str, **kwargs):
    return requests.get(f"{MATRIX_URL}{path}", timeout=5, **kwargs)

def mx_post(path: str, **kwargs):
    return requests.post(f"{MATRIX_URL}{path}", timeout=5, **kwargs)

def mx_put(path: str, **kwargs):
    return requests.put(f"{MATRIX_URL}{path}", timeout=5, **kwargs)


def alias_to_room_id(alias: str) -> str:
    """#alias:server → !roomId"""
    enc = urllib.parse.quote(alias)
    r = mx_get(f"/_matrix/client/v3/directory/room/{enc}",
               params={"access_token": AS_TOKEN})
    r.raise_for_status()
    return r.json()["room_id"]


def ensure_joined(room: str):
    """POST /join; Synapse is idempotent – safe to call every time."""
    enc = urllib.parse.quote(room)
    mx_post(f"/_matrix/client/v3/join/{enc}",
            params={"access_token": AS_TOKEN,
                    "user_id": USER_ID})


def send_message(room_id: str, body: str, format: str | None = None) -> str:
    """Send a message to a room with optional HTML formatting."""
    txn = uuid.uuid4().hex
    content = {
        "msgtype": "m.text",
        "body": body
    }
    
    if format == "html":
        content["format"] = "org.matrix.custom.html"
        content["formatted_body"] = body

    r = mx_put(f"/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn}",
               params={"access_token": AS_TOKEN,
                       "user_id": USER_ID},
               json=content)
    r.raise_for_status()
    return r.json()["event_id"]


# ──────────────────────────── Webhook API ───────────────────────────
@app.post("/webhook")
async def incoming(req: Request):
    data = await req.json()
    text = data.get("text")
    if not text:
        raise HTTPException(400, "`text` field is required")

    # Get message format
    format = data.get("format")

    # Determine room
    channel = data.get("channel")          # e.g. "#general"
    room_id_or_alias = channel or data.get("room_id")     # allow explicit room_id
    if not room_id_or_alias:
        raise HTTPException(400, "`channel` or `room_id` required")

    # If it starts with '#', resolve alias first
    if room_id_or_alias.startswith("#"):
        room_id = alias_to_room_id(room_id_or_alias)
    else:
        room_id = room_id_or_alias

    # Join (harmless if already a member) then send
    try:
        ensure_joined(room_id)
    except Exception:
        pass                                            # ignore errors; may be invite-only
    try:
        event_id = send_message(room_id, text, format)
    except requests.HTTPError as e:
        raise HTTPException(500, f"Matrix error: {e.response.text}")

    return {"ok": True, "event_id": event_id}