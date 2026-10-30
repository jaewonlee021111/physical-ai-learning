import time
from uuid import uuid4
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from ..deps import current_user, database
from ..schemas import Signup

router = APIRouter(prefix="/auth", tags=["auth"])
hasher = PasswordHash.recommended()
dummy_hash = hasher.hash("dummy-password-for-timing")

@router.post("/signup", status_code=201)
def signup(data: Signup, db=Depends(database)):
    uid = uuid4().hex
    try:
        db.execute("INSERT INTO users (id,email,password_hash) VALUES (:id,:email,:hash)",
                   id=uid, email=data.email, hash=hasher.hash(data.password))
    except IntegrityError:
        raise HTTPException(409, "Account already exists")
    return {"id": uid, "email": data.email}

@router.post("/token")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db=Depends(database)):
    user = db.one("SELECT * FROM users WHERE email=:email", email=form.username.strip().lower())
    valid = hasher.verify(form.password, user["password_hash"] if user else dummy_hash)
    if not user or not valid:
        raise HTTPException(401, "Incorrect credentials", headers={"WWW-Authenticate": "Bearer"})
    now = int(time.time())
    token = jwt.encode({"sub": user["id"], "iat": now, "exp": now+1800,
                        "iss": "oct27-learning", "aud": "oct27-api"}, request.app.state.secret, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "expires_in": 1800}

@router.get("/me")
def me(user=Depends(current_user)):
    return user
