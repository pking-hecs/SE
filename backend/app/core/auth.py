from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from backend.app.models.schema import Base, User, UserRole
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from backend.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthHandler:
    def __init__(self):
        self.secret = settings.JWT_SECRET
        self.algorithm = "HS256"
        self.expire_minutes = settings.JWT_EXPIRE_MINUTES

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return pwd_context.verify(password, hashed_password)

    def create_access_token(self, user_id: int, role: str):
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        to_encode = {"exp": expire, "sub": str(user_id), "role": role}
        return jwt.encode(to_encode, self.secret, algorithm=self.algorithm)

    def decode_token(self, token: str):
        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

auth_handler = AuthHandler()
