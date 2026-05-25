# 👕 AI Fashion Project

> AI 기술을 활용하여 패션 데이터를 분석하고 요청을 처리하는 웹 서버 프로젝트입니다. 
> 본 프로젝트는 학교 과제/프로젝트 제출용으로 제작되었습니다.

---

## 🛠️ Tech Stack (기술 스택)
- **Language**: Python 3.x
- **Framework**: FastAPI / Flask (※ 실제 사용하신 프레임워크로 수정하세요)
- **Cloud/Infra**: Amazon Web Services (AWS)
- **Data Format**: JSON

## 📂 Project Structure (폴더 구조)
📁 패션-AI-백엔드-프로젝트 (최상위 루트 폴더)

📁 api/ (사용자 요청이 처음 들어오는 문바위)

📄 admin.py

📄 auth.py

📄 style.py

📄 user.py

📁 core/ (DB 연결, 보안 등 프로젝트의 핵심 심장부)

📄 database.py

📄 security.py

📁 docs/ (샘플 데이터 및 일회성 테스트 스크립트 보관함)

📄 ai_request_mode1.json

📄 ai_response_mode1.json

📄 check_s3.py

📄 set_cors.py

📁 models/ (데이터베이스 테이블 설계도)

📄 models.py

📁 schemas/ (데이터가 오갈 때 양식을 체크하는 검사서)

📄 schemas.py

📁 services/ (실제 비즈니스 로직과 핵심 연산이 돌아가는 곳)

📄 admin_service.py

📄 auth_service.py

📄 style_service.py

📄 user_service.py

📁 utils/ (이미지 처리, S3 업로드 등 재사용 가능한 유용한 도구 상자)

📄 image_utils.py

📄 s3_utils.py

📄 LICENSE (오픈소스 라이선스 문서)

📄 README.md (프로젝트 설명서)

📄 install.sh (서버 초기 세팅용 자동화 스크립트)

📄 main.py (전체 백엔드 서버를 켜는 시작점 파일)

📄 requirements.txt (설치해야 할 라이브러리 목록 대장)

## Environment Variables (환경 변수 세팅)
AWS_ACCESS_KEY=YOUR_AWS_ACCESS_KEY_HERE
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY_HERE
AWS_REGION=ap-northeast-2

S3_BUCKET_NAME=YOUR_S3_BUCKET_NAME_HERE

GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

FAL_KEY=YOUR_FAL_KEY_HERE
