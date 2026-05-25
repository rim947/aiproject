from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, Analysis
from schemas import AdminUserResponse
from core.security import verify_admin_token
from services.admin_service import remove_user_transaction, remove_history_transaction

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/user", response_model=List[AdminUserResponse])
def get_all_users_for_admin(db: Session = Depends(get_db), admin_payload: dict = Depends(verify_admin_token)):
    users = db.query(User).all()
    return [{"userId": u.user_id, "nickname": u.nickname, "email": u.email, "createdAt": u.created_at} for u in users]

@router.delete("/user/{user_id}")
def delete_user_by_admin(user_id: int, db: Session = Depends(get_db), admin_payload: dict = Depends(verify_admin_token)):
    return remove_user_transaction(user_id, db)

@router.get("/history")
def get_all_analysis_history_for_admin(db: Session = Depends(get_db), admin_payload: dict = Depends(verify_admin_token)):
    results = db.query(Analysis, User.nickname).join(User, Analysis.user_id == User.user_id).order_by(Analysis.created_at.desc()).all()
    history_list = []
    for analysis_row, nickname in results:
        tag_array = analysis_row.tags.split(",") if isinstance(analysis_row.tags, str) else analysis_row.tags
        history_list.append({
            "request_id": analysis_row.id, "userId": analysis_row.user_id, "nickname": nickname,
            "mode": analysis_row.mode, "tags": tag_array,
            "createdAt": analysis_row.created_at.isoformat() if analysis_row.created_at else datetime.utcnow().isoformat()
        })
    return history_list

@router.delete("/history/{analysis_id}")
def delete_analysis_history_by_admin(analysis_id: int, db: Session = Depends(get_db), admin_payload: dict = Depends(verify_admin_token)):
    return remove_history_transaction(analysis_id, db)
