from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import User, Analysis
from schemas import ProfileUpdateRequest, PasswordChangeRequest

def process_get_profile(user_id: int, db: Session):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")
    
    joined_date_str = user.created_at.strftime("%Y.%m.%d") if user.created_at else "2026.05.16"
    total_analysis_count = db.query(Analysis).filter(Analysis.user_id == str(user_id)).count()
    
    return {"joinedDate": joined_date_str, "totalAnalysis": total_analysis_count}

def process_update_profile(user_id: int, data: ProfileUpdateRequest, db: Session):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")
    try:
        user.nickname = data.name  
        user.gender = data.gender
        user.height = data.height
        user.weight = data.weight
        db.commit()
        db.refresh(user)
        return {
            "user": {
                "id": str(user.user_id), "name": user.nickname,
                "gender": user.gender, "height": user.height, "weight": user.weight
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="프로필 수정 중 오류가 발생했습니다.")

def process_change_password(user_id: int, data: PasswordChangeRequest, db: Session):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")
    if user.password != data.currentPassword:
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")
    try:
        user.password = data.newPassword
        db.commit()
        return {"message": "비밀번호 변경 성공"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="비밀번호 변경 중 오류가 발생했습니다.")
