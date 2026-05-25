import os
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import JSONResponse
from database import engine, Base 

# 쪼개놓은 라우터들 임포트
from api import auth, user, style, admin

# DB 테이블 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BodyCheck Multi-Module API Server")

# CORS 미들웨어 환경설정
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

# 🌟 전역 에러 핸들러 (오류 역추적 트레이싱 기능)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("=" * 80)
    print(f" ERROR OCCURRED IN: {request.url.path}")
    print(f" ERROR TYPE: {type(exc).__name__}")
    traceback.print_exc() 
    print("=" * 80)
    return JSONResponse(
        status_code=500,
        content={"error_type": type(exc).__name__, "error_message": str(exc)},
    )

# 🌟 쪼개놓은 모듈형 도메인 라우터들을 FastAPI 본체에 전역 등록
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(style.router)
app.include_router(admin.router)

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "BodyCheck API Layer"}
