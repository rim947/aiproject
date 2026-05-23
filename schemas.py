from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Any


class LoginRequest(BaseModel):
    email: str
    password: str

class AnalyzeRequest(BaseModel):
    bodyImageId: int
    clothImageId: Optional[int] = None  # Mode 2에서 사용
    weather: Optional[str] = "spring"
    color: Optional[str] = "black"
    style: Optional[str] = "casual"
    targetClothingImageUrl: Optional[str] = None # Mode 2용 URL 직접 전달 시 사용

class SignupRequest(BaseModel):
    nickname: str
    email: EmailStr  # 혹은 그냥 str로 하셔도 됩니다.
    password: str
    gender: str          # "male" / "female"
    height: int          # 프론트의 number는 파이썬에서 int(혹은 float)
    weight: int

# 1. 요청 스펙 (이메일)
class FindPasswordRequest(BaseModel):
    email: EmailStr

# 2. 응답 스펙 (비밀번호)
class FindPasswordResponse(BaseModel):
    password: str

class ProfileUpdateRequest(BaseModel):
    name: str        # 우리 DB의 nickname에 해당
    gender: str      # "male" / "female"
    height: int
    weight: int

class PasswordChangeRequest(BaseModel):
    currentPassword: str
    newPassword: str


# 1. 출력 스펙에 맞춘 개별 이력 아이템 모델
class HistoryItem(BaseModel):
    id: str           # 분석 고유 ID (문자열로 반환)
    date: str         # "YYYY.MM.DD"
    modeName: str
    tags: List[str]   # 문자열 배열
    summary: str

class TryOnRequest(BaseModel):
    analysisId: int       # 어떤 분석 이력인지 (내 몸 사진 찾기용)
    recommendationId: int # 어떤 추천 옷인지 (옷 사진 찾기용)


# 2. 최종 출력 형태 (history 배열을 감싼 모델)
class HistoryListResponse(BaseModel):
    history: List[HistoryItem]



class RecommendedItem(BaseModel):
    name: str
    accuracy: float  # 프론트 명세서의 number (정확도/매칭률)
    imageUrl: str

# 2. 최종 출력 모델 (5개의 아이템 배열)
class AnalysisResponse(BaseModel):
    items: List[RecommendedItem]


# 1. 출력 스펙에 맞춘 개별 아이템 모델 (모드1과 동일하므로 재사용 가능)
class RecommendedItemMode2(BaseModel):
    name: str
    accuracy: float
    imageUrl: str

# 2. 최종 출력 모델 (5개의 아이템 배열)
class AnalysisMode2Response(BaseModel):
    items: List[RecommendedItemMode2]

class AdminUserResponse(BaseModel):
    userId: int       # DB의 User.user_id (Auto-Increment INT)
    nickname: str
    email: EmailStr   # 혹은 str
    createdAt: datetime

    class Config:
        from_attributes = True


# 관리자용 분석 이력 개별 응답 스키마
class AdminHistoryResponse(BaseModel):
    historyId: int    # 👈 request_id에서 historyId로 변경
    userId: int
    nickname: str
    tags: Any         # 또는 List[str] 등 tags 내부 배열 구조에 맞게 설정

    class Config:
        from_attributes = True # 구버전 Pydantic 스키마라면 orm_mode = True
AdminUserResponse.model_rebuild()
