from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from schemas import TryOnRequest
from services.style_service import process_mode1_analysis, process_mode2_analysis, process_virtual_tryon

router = APIRouter(prefix="/api/style", tags=["Style"])

@router.post("/mode1")
async def analyze_mode1(
    userImage: UploadFile = File(...), userId: str = Form(...), gender: str = Form(...),
    height: int = Form(...), weather: str = Form(...), color: str = Form(...), style: str = Form(...),
    customRequest: Optional[str] = Form(None), db: Session = Depends(get_db)
):
    return await process_mode1_analysis(userImage, userId, gender, height, weather, color, style, db)

@router.post("/mode2")
async def analyze_mode2(
    userImage: UploadFile = File(...), itemImage: UploadFile = File(...), userId: str = Form(...),
    gender: str = Form(...), height: int = Form(...), weather: str = Form(...), target: str = Form(...),
    tpo: str = Form(...), customRequest: Optional[str] = Form(None), db: Session = Depends(get_db)
):
    return await process_mode2_analysis(userImage, itemImage, userId, gender, height, weather, target, tpo, db)

@router.post("/sync")
async def try_on_clothing(request_data: TryOnRequest, db: Session = Depends(get_db)):
    return await process_virtual_tryon(request_data, db)
