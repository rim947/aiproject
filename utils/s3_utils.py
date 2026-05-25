import os
import boto3
from uuid import uuid4
from fastapi import UploadFile
from s3 import s3_client, BUCKET_NAME
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# S3 클라이언트 초기화
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION
)

def upload_to_s3(file: UploadFile) -> str:
    try:
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"uploads/{uuid4()}.{ext}"

        file.file.seek(0)
        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type}
        )
        s3_url = f"https://{BUCKET_NAME}.s3.{region_name}.amazonaws.com/{unique_filename}"
        print(f"✅ S3 이미지 업로드 성공: {s3_url}")
        return s3_url    
    except Exception as e:
        print("❌ S3 업로드 중 에러 발생:", str(e))
        return "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=500"

def upload_to_s3_mode2(user_file: UploadFile, item_file: UploadFile) -> tuple[str, str]:
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

        return user_s3_url, item_s3_url
    except Exception as e:
        print(f"❌ S3 모드2 업로드 중 오류 발생: {str(e)}")
        raise e
