import os
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

cors_configuration = {
    'CORSRules': [{
        'AllowedHeaders': ['*'],
        'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
        'AllowedOrigins': ['*'],
        'ExposeHeaders': ['ETag', 'x-amz-meta-custom-header'],
        'MaxAgeSeconds': 3000
    }]
}

try:
    print(f"⏳ 버킷 '{BUCKET_NAME}'에 CORS 설정을 추가하는 중입니다...")
    s3_client.put_bucket_cors(Bucket=BUCKET_NAME, CORSConfiguration=cors_configuration)
    print("✅ CORS 규칙 설정이 성공적으로 완료되었습니다!")
except Exception as e:
    print(f"❌ CORS 설정 중 에러 발생: {e}")
