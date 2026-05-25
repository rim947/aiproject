import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import SignupRequest, LoginRequest
from core.security import get_verified_user_id
from services.auth_service import process_signup, process_login

router = APIRouter(prefix="/api/auth", tags=["Auth"])
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")

@router.post("/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    return process_signup(data, db)

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return process_login(data, db, SECRET_KEY)

@router.get("/me")
def get_current_user_session(current_user_id: int = Depends(get_verified_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="토큰의 주인인 유저가 DB에 존재하지 않습니다.")
    return {
        "user": {
            "id": str(user.user_id), "name": user.nickname, "email": user.email,
            "gender": user.gender, "height": user.height, "weight": user.weight, "role": user.role
        }
    }

@router.post("/findpw")
def find_password(data: SignupRequest, db: Session = Depends(get_db)):  # 명세 유지
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="해당 이메일로 가입된 유저를 찾을 수 없습니다.")
    return {"password": user.password}
