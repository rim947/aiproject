from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Analysis, Recommendation
from schemas import ProfileUpdateRequest, PasswordChangeRequest
from core.security import get_verified_user_id
from services.user_service import process_get_profile, process_update_profile, process_change_password

router = APIRouter(prefix="/api/user", tags=["User"])

@router.get("/profile/{id}")
def get_profile(id: int, current_user_id: int = Depends(get_verified_user_id), db: Session = Depends(get_db)):
    return process_get_profile(id, db)

@router.put("/profile")
def update_profile(data: ProfileUpdateRequest, current_user_id: int = Depends(get_verified_user_id), db: Session = Depends(get_db)):
    return process_update_profile(current_user_id, data, db)

@router.put("/password")
def change_password(data: PasswordChangeRequest, current_user_id: int = Depends(get_verified_user_id), db: Session = Depends(get_db)):
    return process_change_password(current_user_id, data, db)

@router.get("/history/{id}")
def get_analysis_history(id: int, current_user_id: int = Depends(get_verified_user_id), db: Session = Depends(get_db)):
    analyses = db.query(Analysis).filter(Analysis.user_id == id).order_by(Analysis.created_at.desc()).all()
    history_list = []
    for analysis_row in analyses:
        tag_array = analysis_row.tags.split(",") if isinstance(analysis_row.tags, str) else analysis_row.tags
        recommendations = db.query(Recommendation).filter(Recommendation.analysis_id == analysis_row.id).all()
        
        recommended_items = [{
            "id": rec.item_id, "name": rec.title, "description": rec.description,
            "imageUrl": rec.image_url, "category": rec.category, "accuracy": rec.score
        } for rec in recommendations]

        history_list.append({
            "id": str(analysis_row.id),
            "date": analysis_row.created_at.strftime("%Y.%m.%d") if analysis_row.created_at else datetime.utcnow().strftime("%Y.%m.%d"),
            "modeName": analysis_row.mode, "tags": tag_array, "summary": f"{analysis_row.mode} 분석 결과", "items": recommended_items
        })
    return {"history": history_list}
