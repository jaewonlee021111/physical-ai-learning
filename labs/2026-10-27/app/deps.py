import hashlib
import hmac
import time
import jwt
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

oauth = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def database(request: Request):
    return request.app.state.db

def current_user(request: Request, token: str = Depends(oauth), db=Depends(database)):
    try:
        data = jwt.decode(token, request.app.state.secret, algorithms=["HS256"],
                          issuer="oct27-learning", audience="oct27-api", options={"require": ["sub", "exp", "iss", "aud"]})
        user = db.one("SELECT id,email FROM users WHERE id=:id", id=data["sub"])
        if not user:
            raise ValueError("user missing")
        return user
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})

def device_auth(device_id: str, x_device_key: str = Header(default=""), db=Depends(database)):
    device = db.one("SELECT * FROM devices WHERE id=:id", id=device_id)
    digest = hashlib.sha256(x_device_key.encode()).hexdigest()
    if not device or not hmac.compare_digest(device["key_hash"], digest):
        raise HTTPException(401, "Invalid device credentials")
    return device
