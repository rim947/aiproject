# services/analysis_service.py
from utils.image_utils import resize_and_compress_image # 도구 가져오기
from utils.s3_utils import upload_file_to_s3           # 도구 가져오기

async def process_user_body_analysis(file, db):
    # 1. [utils 도구 사용] 이미지 압축해줘!
    compressed_image = resize_and_compress_image(file.file.read())
    
    # 2. [utils 도구 사용] 압축된 파일 S3에 좀 올려줘!
    s3_url = upload_file_to_s3(compressed_image, "my-bucket-name")
    
    # 3. [services 본연의 비즈니스 일 처리] 
    # S3 URL을 가지고 8001번 AI 서버랑 통신해서 체형 분석 결과 받아오기...
    # DB에 저장하기...
    
    return {"analysis_result": "완료", "image_url": s3_url}
