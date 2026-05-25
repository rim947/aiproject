import re
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models import User
from schemas import SignupRequest, LoginRequest
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = "fallback-secret-key"  # 주: 실제 환경변수 연동 필요
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

def process_signup(data: SignupRequest, db: Session):
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="비밀번호는 8자 이상이어야 합니다.")
    if not re.match(r"^[a-zA-Z0-9가-힣]+$", data.nickname):
        raise HTTPException(status_code=400, detail="닉네임은 특수문자를 포함할 수 없습니다.")
    if data.gender not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="성별은 'male' 또는 'female'만 가능합니다.")

    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일 주소입니다.")

    try:
        user = User(
            email=data.email, password=data.password, nickname=data.nickname,
            gender=data.gender, height=data.height, weight=data.weight
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"message": "회원가입 성공"}
    except Exception as e:
        db.rollback()
        print("SIGNUP ERROR:", str(e))
        raise HTTPException(status_code=500, detail="회원가입 처리 중 오류가 발생했습니다.")

def process_login(data: LoginRequest, db: Session, secret_key: str):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 이메일입니다.")
    if user.password != data.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비밀번호가 일치하지 않습니다.")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_payload = {"sub": str(user.user_id), "role": user.role, "exp": expire}
    access_token = jwt.encode(token_payload, secret_key, algorithm=ALGORITHM)

    return {
        "accessToken": access_token,
        "user": {
            "id": str(user.user_id), "name": user.nickname, "email": user.email,
            "gender": user.gender, "height": user.height, "weight": user.weight, "role": user.role
        }
    }
