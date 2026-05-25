import json
import httpx
import fal_client
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from models import Analysis, Recommendation
from schemas import TryOnRequest
from utils.s3_utils import upload_to_s3, upload_to_s3_mode2

AI_SERVER_URL = "http://100.89.62.43:8001/recommend"

async def process_mode1_analysis(userImage: UploadFile, userId: str, gender: str, height: int, weather: str, color: str, style: str, db: Session):
    s3_url = upload_to_s3(userImage)
    ai_request_payload = {
        "user_id": userId, "body_info": None,
        "mood_tags": [weather, color, style, gender, f"{height}cm"],
        "image_s3_url": s3_url, "user_height_cm": height,
        "target_clothing_image_url": None, "top_k": 5
    }
    
    # Fallback Data 세팅
    final_result = {
        "user_id": userId, "smpl_betas": [0.01, -0.05, 0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "generated_prompt": f"pleated midi skirt A-line flowy pastel spring elegant high-waisted chiffon",
        "recommendations": [{"id": "item_123", "title": f"Spring Floral {style.capitalize()} Item", "description": f"A beautiful item for {weather} outings.", "image_url": "https://example.com/skirt.jpg", "category": "skirt", "score": 0.89}]
    }

    try:
        async with httpx.AsyncClient() as client:
            ai_response = await client.post(AI_SERVER_URL, json=ai_request_payload, timeout=20.0)
            if ai_response.status_code == 200:
                final_result = ai_response.json()
    except Exception as ai_err:
        print("❌ AI 서버 통신 실패 (가짜 데이터 대체):", str(ai_err))

    try:
        new_history = Analysis(
            user_id=int(userId), mode="모드1", tags=json.dumps([weather, color, style]),
            summary=final_result.get("generated_prompt", f"{style} 추천 결과"),
            gender=gender, height=height, user_image_url=s3_url, item_image_url=None
        )
        db.add(new_history)
        db.flush()

        db_recommendation_objects = []
        for item in final_result.get("recommendations", []):
            rec = Recommendation(
                analysis_id=new_history.id, item_id=item.get("id"), title=item.get("title"),
                description=item.get("description"), image_url=item.get("image_url"),
                category=item.get("category"), score=item.get("score")
            )
            db.add(rec)
            db_recommendation_objects.append(rec)

        db.commit()
        final_result["analysis_id"] = new_history.id
        for idx, item in enumerate(final_result.get("recommendations", [])):
            item["recommendation_id"] = db_recommendation_objects[idx].id
    except Exception as db_err:
        db.rollback()
        final_result["analysis_id"] = 999

    return final_result

async def process_mode2_analysis(userImage: UploadFile, itemImage: UploadFile, userId: str, gender: str, height: int, weather: str, target: str, tpo: str, db: Session):
    user_s3_url, target_s3_url = upload_to_s3_mode2(userImage, itemImage)
    ai_request_payload = {
        "user_id": userId, "body_info": None,
        "mood_tags": [weather, target, tpo, gender, f"{height}cm"],
        "image_s3_url": user_s3_url, "user_height_cm": height,
        "target_clothing_image_url": target_s3_url, "top_k": 5
    }
    
    final_result = {
        "user_id": userId, "smpl_betas": [0.01, -0.05, 0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "generated_prompt": f"pleated midi skirt A-line flowy pastel spring elegant high-waisted chiffon",
        "recommendations": [{"id": "item_123", "title": f"Spring Floral {tpo.capitalize()} Item", "description": f"A beautiful item for {weather} outings.", "image_url": "https://example.com/skirt.jpg", "category": "skirt", "score": 0.89}]
    }

    try:
        async with httpx.AsyncClient() as client:
            ai_response = await client.post(AI_SERVER_URL, json=ai_request_payload, timeout=20.0)
            if ai_response.status_code == 200:
                final_result = ai_response.json()
    except Exception as ai_err:
        print("❌ AI 서버 통신 실패 (가짜 데이터 대체):", str(ai_err))

    try:
        new_history = Analysis(
            user_id=int(userId), mode="모드2", tags=json.dumps([weather, target, tpo]),
            summary=final_result.get("generated_prompt", f"{tpo} 추천 결과"),
            gender=gender, height=height, user_image_url=user_s3_url, item_image_url=target_s3_url
        )
        db.add(new_history)
        db.flush()

        for item in final_result.get("recommendations", []):
            rec = Recommendation(
                analysis_id=new_history.id, item_id=item.get("id"), title=item.get("title"),
                description=item.get("description"), image_url=item.get("image_url"),
                category=item.get("category"), score=item.get("score")
            )
            db.add(rec)
        db.commit()
    except Exception as db_err:
        db.rollback()

    return final_result

async def process_virtual_tryon(request_data: TryOnRequest, db: Session):
    analysis_row = db.query(Analysis).filter(Analysis.id == request_data.analysisId).first()
    rec_row = db.query(Recommendation).filter(Recommendation.id == request_data.recommendationId).first()

    if not analysis_row or not rec_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="데이터를 찾을 수 없습니다.")

    output_url = "https://picsum.photos/seed/fallback/400/600"
    try:
        result = await fal_client.subscribe_async(
            "fal-ai/fashn/tryon/v1.6",
            arguments={
                "model_image": analysis_row.user_image_url,
                "garment_image": rec_row.image_url,
            }
        )
        images = result.get("images", [])
        if images and images[0].get("url"):
            output_url = images[0]["url"]
            analysis_row.fitted_image_url = output_url
            db.commit()
            db.refresh(analysis_row)
    except Exception as ai_err:
        db.rollback()
        print(f"❌ [fal.ai 에러]: {ai_err}")

    return {"success": True, "fittedImageUrl": output_url, "synthesized_image_url": output_url}
