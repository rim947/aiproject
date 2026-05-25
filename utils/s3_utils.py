import os
import boto3
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

# 💡 아래는 앞으로 utils 폴더에서 자주 쓰게 될 S3 핵심 기능(함수) 예시입니다.
# 💡 필요에 따라 프로젝트에 맞게 수정해서 사용하세요!

def upload_file_to_s3(file_path, object_name=None):
    """
    로컬 파일을 S3 버킷에 업로드하는 함수
    """
    if object_name is None:
        object_name = os.path.basename(file_path)
        
    try:
        s3_client.upload_file(file_path, BUCKET_NAME, object_name)
        # 업로드된 파일의 서비스 URL 반환
        return f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_name}"
    except Exception as e:
        print(f"S3 업로드 실패: {e}")
        return None

def delete_file_from_s3(object_name):
    """
    S3 버킷에서 파일을 삭제하는 함수
    """
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=object_name)
        return True
    except Exception as e:
        print(f"S3 삭제 실패: {e}")
        return False
