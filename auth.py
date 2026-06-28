import bcrypt
import hashlib
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import database, models

SECRET_KEY = "mysecretkey_for_edulibrary_pro_change_in_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def _pre_hash(password: str) -> bytes:
    # Pre-hashing as bytes prevents the 72-byte limit error instantly
    return hashlib.sha256(password.encode('utf-8')).hexdigest().encode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Check the pure bcrypt password
    return bcrypt.checkpw(_pre_hash(plain_password), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    # Hash using pure bcrypt and decode to store as string
    return bcrypt.hashpw(_pre_hash(password), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        library_id: str = payload.get("sub")
        if library_id is None:
            return None
    except jwt.InvalidTokenError:
        return None
    
    user = db.query(models.User).filter(models.User.library_id == library_id).first()
    return user

def get_current_user_from_cookie(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    if token.startswith("Bearer "):
        token = token[7:]
    return get_current_user_from_token(token, db)