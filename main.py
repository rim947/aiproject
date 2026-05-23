import re
import traceback
import logging
import jwt
import httpx
import os
import json
import boto3
import fal_client

from google import genai
from google.genai import types
from typing import List, Optional
from fastapi import FastAPI, status, UploadFile, Query, File, Depends, HTTPException, Form, APIRouter, Request, Header
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from io import BytesIO
from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel, GeneratedImage
from PIL import Image

from s3 import s3_client, BUCKET_NAME
from database import engine, get_db, Base 
from models import Recommendation, User, Image, Result, Analysis, History
from schemas import AdminUserResponse, TryOnRequest, AdminHistoryResponse, SignupRequest, LoginRequest, FindPasswordRequest, FindPasswordResponse, AnalyzeRequest, PasswordChangeRequest, ProfileUpdateRequest
from datetime import datetime, timedelta
from uuid import uuid4
from dotenv import load_dotenv
load_dotenv()
print("키 확인:", os.environ.get("GEMINI_API_KEY", "없음"))

Base.metadata.create_all(bind=engine)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

region_name = os.getenv("AWS_REGION", "ap-northeast-2")

app = FastAPI()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  

security = HTTPBearer()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://bodycheck-alpha.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,           
    allow_methods=["*"],              
    allow_headers=["*"],              
)

async def fetch_image_bytes(url: str) -> tuple[bytes, str]:
    print(f"🔍 이미지 다운로드 시도: {url}")
    async with httpx.AsyncClient(follow_redirects=True) as http:
        res = await http.get(url)
        print(f"🔍 응답 상태코드: {res.status_code}")
        res.raise_for_status()
        content_type = res.headers.get("content-type", "image/jpeg").split(";")[0]
        return res.content, content_type


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials  
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="인증 토큰에 유저 정보가 없습니다.")
        return int(user_id)  
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

def get_verified_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials  
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="인증 토큰에 유저 정보(sub)가 없습니다.")
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰 유효기간이 만료되었습니다. 다시 로그인해 주세요.")
    except jwt.PyJWTError:  
        raise HTTPException(status_code=401, detail="유효하지 않거나 손상된 토큰입니다.")

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials  
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 누락되었습니다."
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role = payload.get("role")
        
        if user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="관리자만 접근할 수 있는 권한입니다."
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 만료되었습니다.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")

def upload_to_s3(file: UploadFile) -> str:
    try:
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"uploads/{uuid4()}.{ext}"

        file.file.seek(0)
        
        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            unique_filename,
            ExtraArgs={
                "ContentType": file.content_type  
            }
        )
        
        s3_url = f"https://{BUCKET_NAME}.s3.{region_name}.amazonaws.com/{unique_filename}"
        print(f"✅ 학교 S3에 이미지 업로드 성공! 주소: {s3_url}")
        return s3_url    

    except Exception as e:
        print("❌ S3 업로드 중 에러 발생:", str(e))
        return "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=500"
    
def upload_to_s3_mode2(user_file: UploadFile, item_file: UploadFile) -> str:
    try:
        user_ext = user_file.filename.split(".")[-1] if "." in user_file.filename else "jpg"
        user_unique = f"uploads/{uuid4()}.{user_ext}"
        
        user_file.file.seek(0)
        s3_client.upload_fileobj(
            user_file.file,
            BUCKET_NAME,
            user_unique,
            ExtraArgs={"ContentType": user_file.content_type}
        )
        user_s3_url = f"https://{BUCKET_NAME}.s3.{region_name}.amazonaws.com/{user_unique}"
        print(f"✅ 유저 사진 S3 업로드 성공: {user_s3_url}")

        item_ext = item_file.filename.split(".")[-1] if "." in item_file.filename else "jpg"
        item_unique = f"uploads/{uuid4()}.{item_ext}"
        
        item_file.file.seek(0)
        s3_client.upload_fileobj(
            item_file.file,
            BUCKET_NAME,
            item_unique,
            ExtraArgs={"ContentType": item_file.content_type}
        )
        item_s3_url = f"https://{BUCKET_NAME}.s3.{region_name}.amazonaws.com/{item_unique}"
        print(f"✅ 옷 사진 S3 업로드 성공: {item_s3_url}")

        return user_s3_url, item_s3_url

    except Exception as e:
        print(f"❌ S3 업로드 중 오류 발생: {str(e)}")
        raise e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("=" * 80)
    print(f" ERROR OCCURRED IN: {request.url.path}")
    print(f" ERROR TYPE: {type(exc).__name__}")
    traceback.print_exc() 
    print("=" * 80)

    return JSONResponse(
        status_code=500,
        content={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
    )


@app.post("/api/auth/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):

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
            email=data.email,
            password=data.password,
            nickname=data.nickname,
            gender=data.gender,
            height=data.height,
            weight=data.weight
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {"message": "회원가입 성공"}
        
    except Exception as e:
        db.rollback()
        print("SIGNUP ERROR:", str(e))
        raise HTTPException(status_code=500, detail="회원가입 처리 중 오류가 발생했습니다.")


@app.post("/api/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 이메일입니다.")

    if user.password != data.password:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,  
                detail="비밀번호가 일치하지 않습니다."
            )

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    token_payload = {
        "sub": str(user.user_id),
        "role": user.role,  # 👈 여기에 추가 완료!
        "exp": expire
    }

    access_token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "accessToken": access_token,
        "user": {
            "id": str(user.user_id),  
            "name": user.nickname,
            "email": user.email,
            "gender": user.gender,
            "height": user.height,
            "weight": user.weight,
            "role": user.role
        }
    }


@app.get("/api/auth/me")
def get_current_user_session(
    current_user_id: int = Depends(get_verified_user_id),  
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="토큰의 주인인 유저가 DB에 존재하지 않습니다.")

    return {
        "user": {
            "id": str(user.user_id),
            "name": user.nickname,
            "email": user.email,
            "gender": user.gender,
            "height": user.height,
            "weight": user.weight,
            "role": user.role
        }
    }


@app.post("/api/auth/findpw")
def find_password(data: FindPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="해당 이메일로 가입된 유저를 찾을 수 없습니다.")
    return {"password": user.password}


@app.get("/api/user/profile/{id}")
def get_profile(
    id: int, 
    current_user_id: int = Depends(get_verified_user_id),  
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")

    joined_date_str = user.created_at.strftime("%Y.%m.%d") if user.created_at else "2026.05.16"
    total_analysis_count = db.query(Analysis).filter(Analysis.user_id == str(id)).count()

    return {
        "joinedDate": joined_date_str,
        "totalAnalysis": total_analysis_count
    }


@app.put("/api/user/profile")
def update_profile(
    data: ProfileUpdateRequest,
    current_user_id: int = Depends(get_verified_user_id),  
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == current_user_id).first()
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
                "id": str(user.user_id),
                "name": user.nickname,
                "gender": user.gender,
                "height": user.height,
                "weight": user.weight
            }
        }
    except Exception as e:
        db.rollback()
        print("PROFILE UPDATE ERROR:", str(e))
        raise HTTPException(status_code=500, detail="프로필 수정 중 오류가 발생했습니다.")


@app.put("/api/user/password")
def change_password(
    data: PasswordChangeRequest,
    current_user_id: int = Depends(get_verified_user_id),  
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == current_user_id).first()
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
        print("PASSWORD CHANGE ERROR:", str(e))
        raise HTTPException(status_code=500, detail="비밀번호 변경 중 오류가 발생했습니다.")

@app.get("/api/user/history/{id}")
def get_analysis_history(
    id: int,
    current_user_id: int = Depends(get_verified_user_id),
    db: Session = Depends(get_db)
):
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == id)
        .order_by(Analysis.created_at.desc())
        .all()
    )

    history_list = []
    for analysis_row in analyses:
        tag_array = analysis_row.tags.split(",") if isinstance(analysis_row.tags, str) else analysis_row.tags
        
        recommendations = db.query(Recommendation).filter(Recommendation.analysis_id == analysis_row.id).all()
        
        recommended_items = []
        for rec in recommendations:
            recommended_items.append({
                "id": rec.item_id,
                "name": rec.title,
                "description": rec.description,
                "imageUrl": rec.image_url,
                "category": rec.category,
                "accuracy": rec.score
            })

        history_list.append({
            "id": str(analysis_row.id),
            "date": analysis_row.created_at.strftime("%Y.%m.%d") if analysis_row.created_at else datetime.utcnow().strftime("%Y.%m.%d"),
            "modeName": analysis_row.mode,
            "tags": tag_array,
            "summary": f"{analysis_row.mode} 분석 결과",
            "items": recommended_items
        })

    return {"history": history_list}


@app.post("/api/style/mode1")
async def analyze_mode1(
    userImage: UploadFile = File(...),
    userId: str = Form(...),
    gender: str = Form(...),
    height: int = Form(...),
    weather: str = Form(...),
    color: str = Form(...),
    style: str = Form(...),
    customRequest: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        s3_url = upload_to_s3(userImage)

        AI_SERVER_URL = "http://100.89.62.43:8001/recommend" 

        ai_request_payload = {
            "user_id": userId,
            "body_info": None,  
            "mood_tags": [weather, color, style, gender, f"{height}cm"],  
            "image_s3_url": s3_url,
            "user_height_cm": height,  
            "target_clothing_image_url": None,  
            "top_k": 5 
        }

        fallback_response = {
            "user_id": userId,
            "body_info": {
                "height_cm": float(height),
                "shoulder_width": "normal",
                "torso_length": "normal",
                "waist_shape": "straight",
                "hip_shape": "balanced",
                "overall_build": "average",
                "leg_shape": "normal",
                "semantic_descriptors": ["average build", "normal shoulders", "balanced hips", f"height {height}cm"]
            },
            "smpl_betas": [0.01, -0.05, 0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "generated_prompt": f"pleated midi skirt A-line flowy pastel spring elegant high-waisted chiffon",
            "recommendations": [
                {
                    "id": "item_123",
                    "title": f"Spring Floral {style.capitalize()} Item",
                    "description": f"A beautiful item for {weather} outings.",
                    "image_url": "https://example.com/skirt.jpg",
                    "category": "skirt",
                    "score": 0.89
                }
            ]
        }
        
        final_result = fallback_response

        try:
            async with httpx.AsyncClient() as client:
                ai_response = await client.post(AI_SERVER_URL, json=ai_request_payload, timeout=20.0)
                
                if ai_response.status_code == 200:
                    final_result = ai_response.json()
                else:
                    print(f"⚠️ AI 서버 응답 에러 코드 {ai_response.status_code}: {ai_response.text}")
        except Exception as ai_err:
            print("❌ AI 팀 서버 통신 중 예외 발생 (가짜 데이터 대체):", str(ai_err))

        try:
            new_history = Analysis(
                user_id=int(userId),          
                mode="모드1",                  
                tags=json.dumps([weather, color, style]),
                summary=final_result.get("generated_prompt", f"{style} 추천 결과"),
                gender=gender,
                height=height,
                user_image_url=s3_url,
                item_image_url=None
            )
            db.add(new_history)
            db.flush()

            ai_recommendations = final_result.get("recommendations", [])
            db_recommendation_objects = []

            for item in ai_recommendations:
                new_recommendation = Recommendation(
                    analysis_id=new_history.id,
                    item_id=item.get("id"),
                    title=item.get("title"),
                    description=item.get("description"),
                    image_url=item.get("image_url"),
                    category=item.get("category"),
                    score=item.get("score")
                )
                db.add(new_recommendation)
                db_recommendation_objects.append(new_recommendation)

            db.commit()
            print("DB에 AI 분석 이력 및 세부 추천 아이템 전체 저장 성공!")

            final_result["analysis_id"] = new_history.id

            for idx, item in enumerate(final_result.get("recommendations", [])):
                item["recommendation_id"] = db_recommendation_objects[idx].id

        except Exception as db_err:
            db.rollback()
            print("DB 저장 실패 (로그 출력 후 프론트 튕김 방지):", str(db_err))
            final_result["analysis_id"] = 999
            for item in final_result.get("recommendations", []):
                item["recommendation_id"] = 999

        return final_result

    except Exception as e:
        print("AI ANALYSIS MODE1 CRITICAL ERROR:", str(e))
        raise HTTPException(status_code=500, detail="AI 분석 처리 중 오류가 발생했습니다.")

@app.post("/api/style/mode2")
async def analyze_mode2(
    userImage: UploadFile = File(...),
    itemImage: UploadFile = File(...),
    userId: str = Form(...),
    gender: str = Form(...),
    height: int = Form(...),
    weather: str = Form(...),
    target: str = Form(...),
    tpo: str = Form(...),
    customRequest: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        user_s3_url, target_s3_url = upload_to_s3_mode2(userImage, itemImage)

        AI_SERVER_URL = "http://100.89.62.43:8001/recommend" 

        ai_request_payload = {
            "user_id": userId,
            "body_info": None,  
            "mood_tags": [weather, target, tpo, gender, f"{height}cm"],  
            "image_s3_url": user_s3_url,
            "user_height_cm": height,  
            "target_clothing_image_url": target_s3_url,  
            "top_k": 5 
        }

        fallback_response = {
            "user_id": userId,
            "body_info": {
                "height_cm": float(height),
                "shoulder_width": "normal",
                "torso_length": "normal",
                "waist_shape": "straight",
                "hip_shape": "balanced",
                "overall_build": "average",
                "leg_shape": "normal",
                "semantic_descriptors": ["average build", "normal shoulders", "balanced hips", f"height {height}cm"]
            },
            "smpl_betas": [0.01, -0.05, 0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "generated_prompt": f"pleated midi skirt A-line flowy pastel spring elegant high-waisted chiffon",
            "recommendations": [
                {
                    "id": "item_123",
                    "title": f"Spring Floral {tpo.capitalize()} Item",
                    "description": f"A beautiful item for {weather} outings.",
                    "image_url": "https://example.com/skirt.jpg",
                    "category": "skirt",
                    "score": 0.89
                }
            ]
        }
        
        final_result = fallback_response

        try:
            async with httpx.AsyncClient() as client:
                ai_response = await client.post(AI_SERVER_URL, json=ai_request_payload, timeout=20.0)
                
                if ai_response.status_code == 200:
                    final_result = ai_response.json()
                else:
                    print(f"⚠️ AI 서버 응답 에러 코드 {ai_response.status_code}: {ai_response.text}")
        except Exception as ai_err:
            print("❌ AI 팀 서버 통신 중 예외 발생 (가짜 데이터 대체):", str(ai_err))

        try:
            new_history = Analysis(
                user_id=int(userId),          
                mode="모드2",                  
                tags=json.dumps([weather, target, tpo]),
                summary=final_result.get("generated_prompt", f"{tpo} 추천 결과"),
                gender=gender,
                height=height,
                user_image_url=user_s3_url,
                item_image_url=target_s3_url
            )
            db.add(new_history)
            db.flush()

            ai_recommendations = final_result.get("recommendations", [])
            for item in ai_recommendations:
                new_recommendation = Recommendation(
                    analysis_id=new_history.id,
                    item_id=item.get("id"),
                    title=item.get("title"),
                    description=item.get("description"),
                    image_url=item.get("image_url"),
                    category=item.get("category"),
                    score=item.get("score")
                )
                db.add(new_recommendation)

            db.commit()
            print("DB에 AI 분석 이력 및 세부 추천 아이템 전체 저장 성공!")
            
        except Exception as db_err:
            db.rollback()
            print("DB 저장 실패 (로그 출력 후 프론트 튕김 방지):", str(db_err))

        return final_result

    except Exception as e:
        print("AI ANALYSIS MODE2 CRITICAL ERROR:", str(e))
        raise HTTPException(status_code=500, detail="AI 분석 처리 중 오류가 발생했습니다.")


@app.get("/api/admin/user", response_model=List[AdminUserResponse])
def get_all_users_for_admin(
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(verify_admin_token)  
):
    users = db.query(User).all()
    return [
        {
            "userId": user.user_id,
            "nickname": user.nickname,
            "email": user.email,
            "createdAt": user.created_at
        }
        for user in users
    ]

@app.delete("/api/admin/user/{user_id}")
def delete_user_by_admin(
    user_id: int, 
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(verify_admin_token)  
):
    # 1. 삭제할 유저가 존재하는지 먼저 확인
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 유저입니다.")

    try:
        # 2. 🌟 외래키 제약조건 방지 (고아 데이터 방지)
        # 이 유저가 작성한 모든 분석 이력(Analysis)의 ID들을 먼저 추출합니다.
        user_analysis_ids = [a.id for a in db.query(Analysis).filter(Analysis.user_id == user_id).all()]
        
        if user_analysis_ids:
            # 해당 분석 이력들에 물려있는 자식 추천 데이터(Recommendation)들을 먼저 싹 삭제
            db.query(Recommendation).\
                filter(Recommendation.analysis_id.in_(user_analysis_ids)).\
                delete(synchronize_session="fetch")
            
            # 유저의 분석 이력(Analysis) 본체들을 삭제
            db.query(Analysis).\
                filter(Analysis.user_id == user_id).\
                delete(synchronize_session="fetch")

        # 3. 마지막으로 부모인 유저(User) 데이터 삭제
        db.delete(target_user)
        
        # 4. 🌟 DB에 최종적으로 완전히 영구 반영 (커밋)
        db.commit()
        
        # 🌟 프론트엔드가 요구한 성공 메시지 포맷 그대로 리턴
        return {"status": "success", "message": "User deleted"}
        
    except Exception as e:
        # 과정 중 하나라도 실패하면 안전하게 복구(롤백)
        db.rollback()
        print("ADMIN DELETE USER ERROR:", str(e))
        raise HTTPException(status_code=500, detail="유저 삭제 처리 중 오류가 발생했습니다.")

# @app.get("/api/admin/history", response_model=List[AdminHistoryResponse])
# def get_all_analysis_history_for_admin(
#     db: Session = Depends(get_db),
#     admin_payload: dict = Depends(verify_admin_token)  
# ):
#     results = db.query(History, User.nickname).\
#         join(User, History.user_id == User.user_id).\
#         all()
    
#     history_list = []
#     for history, nickname in results:
#         parsed_tags = history.tags
#         if isinstance(parsed_tags, str):
#             try:
#                 parsed_tags = json.loads(history.tags)
#             except Exception:
#                 parsed_tags = [history.tags]

#         history_list.append({
#             "request_id": history.request_id,
#             "userId": history.user_id,
#             "nickname": nickname,
#             "mode": history.mode,
#             "tags": parsed_tags,
#             "createdAt": history.created_at
#         })

#     return history_list


@app.get("/api/admin/history")
def get_all_analysis_history_for_admin(
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(verify_admin_token)  
):
    # 1. Analysis 테이블과 User 테이블을 조인하여 데이터 전체 조회
    results = db.query(Analysis, User.nickname).\
        join(User, Analysis.user_id == User.user_id).\
        order_by(Analysis.created_at.desc()).\
        all()
    
    history_list = []
    for analysis_row, nickname in results:
        # 2. 태그 안전하게 파싱 (문자열이면 리스트로 분할)
        tag_array = analysis_row.tags.split(",") if isinstance(analysis_row.tags, str) else analysis_row.tags
        
        # 3. 🌟 프론트엔드가 요구한 구조 [ { request_id, userId, nickname, mode, tags, createdAt }, ... ] 와 완벽히 일치시킴
        history_list.append({
            "request_id": analysis_row.id,  # 👈 프론트가 요구한 ID 이름 (Analysis.id를 매핑)
            "userId": analysis_row.user_id,
            "nickname": nickname,
            "mode": analysis_row.mode,      # 👈 프론트가 요구한 mode 이름
            "tags": tag_array,
            "createdAt": analysis_row.created_at.isoformat() if analysis_row.created_at else datetime.utcnow().isoformat() # 👈 프론트가 요구한 날짜 이름 (ISO 포맷 또는 strftime 사용)
        })

    # 🌟 감싸지 않고 순수 리스트로 리턴하여 e.map 에러 해결!
    return history_list

@app.delete("/api/admin/history/{analysis_id}")
def delete_analysis_history_by_admin(
    analysis_id: int, 
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(verify_admin_token)  
):
    # 1. 지우려는 본체(Analysis)가 있는지 먼저 확인
    target_analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not target_analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="존재하지 않는 분석 이력입니다.")

    try:
        # 🌟 중요: synchronize_session="fetch" 옵션을 주어 
        # 자식(Recommendation) 데이터를 지운 상태를 세션에 완벽히 동기화합니다.
        db.query(Recommendation).\
            filter(Recommendation.analysis_id == analysis_id).\
            delete(synchronize_session="fetch")
        
        # 2. 본체 삭제
        db.delete(target_analysis)
        
        # 3. 🌟 최종적으로 DB에 완전히 영구 반영 (커밋)
        db.commit()
        
        return {"status": "success", "message": "History deleted"}
        
    except Exception as e:
        # 하나라도 실패하면 안전하게 이전 상태로 복구
        db.rollback()
        print("ADMIN DELETE ANALYSIS ERROR:", str(e))
        raise HTTPException(status_code=500, detail="분석 이력 삭제 처리 중 오류가 발생했습니다.")

@app.post("/api/style/sync")
async def try_on_clothing(
    request_data: TryOnRequest,
    db: Session = Depends(get_db)
):
    print(f"🍌 [나노바나나 가상피팅] 요청 분석 ID: {request_data.analysisId}")

    analysis_row = db.query(Analysis).filter(Analysis.id == request_data.analysisId).first()
    rec_row      = db.query(Recommendation).filter(Recommendation.id == request_data.recommendationId).first()

    if not analysis_row or not rec_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="데이터를 찾을 수 없습니다.")

    # FAL API Key 검증
    fal_key = os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY")
    if not fal_key:
        print("⚠️ 환경변수에 FAL_KEY 또는 FAL_API_KEY가 설정되지 않았습니다.")

    output_url = "https://picsum.photos/seed/fallback/400/600"

    try:
        print("📡 [fal.ai FASHN Try-On API 호출 중...]")
        result = await fal_client.subscribe_async(
            "fal-ai/fashn/tryon/v1.6",
            arguments={
                "model_image": analysis_row.user_image_url,
                "garment_image": rec_row.image_url,
            }
        )
        print("✅ [fal.ai 응답 수신 완료]")
        
        images = result.get("images", [])
        if not images or not images[0].get("url"):
            raise ValueError("fal.ai가 생성된 이미지 정보를 반환하지 않았습니다.")
            
        cdn_url = images[0]["url"]
        print(f"🔗 fal.ai 생성 이미지 URL: {cdn_url}")

        output_url = cdn_url

        analysis_row.fitted_image_url = output_url
        db.commit()
        db.refresh(analysis_row)
        print("💾 [DB 저장 완료]")

    except Exception as ai_err:
        db.rollback()
        print(f"❌ [fal.ai 에러]: {ai_err}")

    return {
        "success": True,
        "fittedImageUrl": output_url,
        "synthesized_image_url": output_url,
    }

