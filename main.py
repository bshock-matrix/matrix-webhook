from __future__ import annotations
import os, uuid, urllib.parse, requests, json
from fastapi import FastAPI, Request, HTTPException

# ─── Config ──────────────────────────────────────────────────────────
MX      = os.getenv("MATRIX_URL", "http://localhost:8008").rstrip("/")
AS_TOK  = os.environ["AS_TOKEN"]
LOCAL   = os.getenv("BOT_LOCALPART", "webhook_bot")
SERVER  = os.getenv("SERVER_NAME",   "localhost")
USER_ID = f"@{LOCAL}:{SERVER}"

app = FastAPI()


# ─── Helper for HTTP calls ───────────────────────────────────────────
def mx(method: str, path: str, **kw) -> requests.Response:
    return requests.request(method, f"{MX}{path}", timeout=5, **kw)


# ─── Ensure the ghost user exists ────────────────────────────────────
def ensure_registered() -> None:
    payload = {"username": LOCAL, "type": "m.login.application_service"}
    r = mx("POST",
           "/_matrix/client/v3/register",
           params={"access_token": AS_TOK},
           json=payload)
    if r.status_code == 200:
        return                                # success
    if r.status_code == 400:                  # could be already registered
        try:
            err = r.json().get("errcode", "")
        except json.JSONDecodeError:
            err = ""
        if err in ("M_USER_IN_USE", "M_EXCLUSIVE"):
            return                            # already exists → fine
    r.raise_for_status()


# ─── Matrix primitives ───────────────────────────────────────────────
def alias_to_room_id(alias: str) -> str:
    enc = urllib.parse.quote(alias)
    r = mx("GET",
           f"/_matrix/client/v3/directory/room/{enc}",
           params={"access_token": AS_TOK})
    r.raise_for_status()
    return r.json()["room_id"]


def ensure_join(room: str) -> None:
    enc = urllib.parse.quote(room)
    mx("POST",
       f"/_matrix/client/v3/join/{enc}",
       params={"access_token": AS_TOK, "user_id": USER_ID})


def send(room_id: str, body: str, html: bool) -> str:
    txn  = uuid.uuid4().hex
    content = {"msgtype": "m.text", "body": body}
    if html:
        content |= {
            "format": "org.matrix.custom.html",
            "formatted_body": body
        }
    r = mx("PUT",
           f"/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn}",
           params={"access_token": AS_TOK, "user_id": USER_ID},
           json=content)
    r.raise_for_status()
    return r.json()["event_id"]


# ─── Webhook endpoint ────────────────────────────────────────────────
@app.post("/webhook")
async def webhook(req: Request):
    p = await req.json()

    text = p.get("text")
    if not text:
        raise HTTPException(400, "`text` field is required")

    target = p.get("channel") or p.get("room_id")
    if not target:
        raise HTTPException(400, "`channel` or `room_id` is required")

    # make sure bot exists
    ensure_registered()

    # alias → room-ID
    room_id = alias_to_room_id(target) if target.startswith("#") else target

    # join (idempotent)
    try:
        ensure_join(room_id)
    except Exception:
        pass                                   # invite-only room w/out invite

    #  send
    try:
        eid = send(room_id, text, p.get("format") == "html")
    except requests.HTTPError as e:
        raise HTTPException(500, f"Matrix error: {e.response.text}")

    return {"ok": True, "event_id": eid}