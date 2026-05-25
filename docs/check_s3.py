import os
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

print(f"🔍 검사 대상 버킷: {BUCKET_NAME}")

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# 1. Bucket Policy (버킷 정책) 검사
try:
    policy = s3_client.get_bucket_policy(Bucket=BUCKET_NAME)
    print("\n✅ [Bucket Policy (버킷 정책)]이 존재합니다:")
    print(policy['Policy'])
except Exception as e:
    print("\n❌ [Bucket Policy]가 없거나 읽을 수 없습니다:", str(e))

# 2. CORS (교차 출처 리소스 공유) 규칙 검사
try:
    cors = s3_client.get_bucket_cors(Bucket=BUCKET_NAME)
    print("\n✅ [CORS 규칙]이 설정되어 있습니다:")
    print(cors['CORSRules'])
except Exception as e:
    print("\n❌ [CORS 규칙]이 설정되지 않았거나 접근할 수 없습니다:", str(e))

# 3. Public Access Block (퍼블릭 액세스 차단) 검사
try:
    pub_block = s3_client.get_public_access_block(Bucket=BUCKET_NAME)
    print("\nℹ️ [퍼블릭 액세스 차단(Public Access Block) 설정]:")
    print(pub_block['PublicAccessBlockConfiguration'])
except Exception as e:
    print("\nℹ️ [퍼블릭 액세스 차단 설정] 정보 없음:", str(e))

# 4. 버킷 ACL (액세스 제어 목록)
try:
    acl = s3_client.get_bucket_acl(Bucket=BUCKET_NAME)
    print("\nℹ️ [버킷 ACL (Access Control List)]:")
    for grant in acl['Grants']:
        grantee = grant.get('Grantee', {})
        print(f" - 권한: {grant.get('Permission')}, 대상: {grantee.get('URI', grantee.get('DisplayName', 'Unknown'))}")
except Exception as e:
    print("\n❌ [버킷 ACL] 에러:", str(e))
