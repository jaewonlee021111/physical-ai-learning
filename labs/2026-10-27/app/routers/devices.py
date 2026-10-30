import hashlib
import secrets
import time
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Response
from ..deps import current_user, database, device_auth
from ..schemas import Named, Telemetry, LedCommand
from .items import owned

router = APIRouter(tags=["devices"])

@router.post("/devices", status_code=201)
def register(data: Named, user=Depends(current_user), db=Depends(database)):
    uid, key = uuid4().hex, secrets.token_urlsafe(32)
    db.execute("INSERT INTO devices(id,owner,name,key_hash) VALUES(:id,:owner,:name,:hash)",
               id=uid, owner=user["id"], name=data.name, hash=hashlib.sha256(key.encode()).hexdigest())
    return {"id": uid, "name": data.name, "device_key": key, "note": "save locally; key shown once"}

@router.get("/devices")
def devices(user=Depends(current_user), db=Depends(database)):
    rows = db.all("SELECT id,name,raw,touched,led,seen FROM devices WHERE owner=:owner ORDER BY name", owner=user["id"])
    for row in rows:
        row["status"] = "never_seen" if row["seen"] is None else "stale" if time.time()-row["seen"]>10 else "online"
    return rows

@router.post("/devices/{device_id}/commands", status_code=202)
def command(device_id: str, data: LedCommand, user=Depends(current_user), db=Depends(database)):
    owned(db, "devices", device_id, user["id"])
    cid = uuid4().hex
    db.execute("INSERT INTO commands(id,device,led,state,created) VALUES(:id,:device,:led,'pending',:created)",
               id=cid, device=device_id, led=int(data.led), created=time.time())
    return {"id": cid, "state": "pending", "message": "queued; hardware application not yet confirmed"}

@router.get("/devices/{device_id}/commands")
def commands(device_id: str, user=Depends(current_user), db=Depends(database)):
    owned(db, "devices", device_id, user["id"])
    return db.all("SELECT id,led,state,created,acknowledged FROM commands WHERE device=:device ORDER BY created DESC LIMIT 30", device=device_id)

@router.post("/device/{device_id}/telemetry")
def telemetry(device_id: str, data: Telemetry, device=Depends(device_auth), db=Depends(database)):
    db.execute("UPDATE devices SET raw=:raw,touched=:touched,led=:led,seen=:seen WHERE id=:id",
               id=device_id, raw=data.raw, touched=int(data.touched), led=int(data.led), seen=time.time())
    return {"accepted": True}

@router.get("/device/{device_id}/next-command")
def poll(device_id: str, device=Depends(device_auth), db=Depends(database)):
    db.execute("UPDATE commands SET state='expired' WHERE device=:device AND state='pending' AND created<:cutoff",
               device=device_id, cutoff=time.time()-30)
    # Same id is redelivered until ACK, so the board must handle it idempotently.
    row = db.one("SELECT id,led,state FROM commands WHERE device=:device AND state='pending' ORDER BY created LIMIT 1", device=device_id)
    return {"command": row}

@router.post("/device/{device_id}/ack/{command_id}")
def ack(device_id: str, command_id: str, device=Depends(device_auth), db=Depends(database)):
    row = db.one("SELECT * FROM commands WHERE id=:id AND device=:device", id=command_id, device=device_id)
    if not row:
        raise HTTPException(404, "Unknown command")
    if row["state"] == "expired" or (row["state"] == "pending" and time.time()-row["created"] > 30):
        raise HTTPException(409, "Command expired")
    if row["state"] != "applied":
        db.execute("UPDATE commands SET state='applied',acknowledged=:now WHERE id=:id", id=command_id, now=time.time())
    return {"id": command_id, "state": "applied", "meaning": "board software ACK, not optical LED measurement"}
