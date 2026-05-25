from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models import User, Analysis, Recommendation

def remove_user_transaction(user_id: int, db: Session):
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 유저입니다.")
    try:
        user_analysis_ids = [a.id for a in db.query(Analysis).filter(Analysis.user_id == user_id).all()]
        if user_analysis_ids:
            db.query(Recommendation).filter(Recommendation.analysis_id.in_(user_analysis_ids)).delete(synchronize_session="fetch")
            db.query(Analysis).filter(Analysis.user_id == user_id).delete(synchronize_session="fetch")
        db.delete(target_user)
        db.commit()
        return {"status": "success", "message": "User deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="유저 삭제 처리 중 오류가 발생했습니다.")

def remove_history_transaction(analysis_id: int, db: Session):
    target_analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not target_analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 분석 이력입니다.")
    try:
        db.query(Recommendation).filter(Recommendation.analysis_id == analysis_id).delete(synchronize_session="fetch")
        db.delete(target_analysis)
        db.commit()
        return {"status": "success", "message": "History deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="분석 이력 삭제 처리 중 오류가 발생했습니다.")
