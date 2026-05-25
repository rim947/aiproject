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
📁 패션-AI-백엔드-프로젝트 (Root)
├── 📁 api/  
│   ├── 📄 admin.py  
│   ├── 📄 auth.py  
│   ├── 📄 style.py  
│   └── 📄 user.py   
├── 📁 core/  
│   ├── 📄 database.py  
│   └── 📄 security.py  
├── 📁 docs/  
│   ├── 📄 ai_request_mode1.json  
│   ├── 📄 ai_response_mode1.json  
│   ├── 📄 check_s3.py   
│   └── 📄 set_cors.py   
├── 📁 models/  
│   └── 📄 models.py  
├── 📁 schemas/  
│   └── 📄 schemas.py  
├── 📁 services/  
│   ├── 📄 admin_service.py  
│   ├── 📄 auth_service.py  
│   ├── 📄 style_service.py  
│   └── 📄 user_service.py  
├── 📁 utils/  
│   ├── 📄 image_utils.py  
│   └── 📄 s3_utils.py  
├── 📄 LICENSE  
├── 📄 README.md  
├── 📄 install.sh  
├── 📄 main.py  
└── 📄 requirements.txt  

## Environment Variables (환경 변수 세팅)
AWS_ACCESS_KEY=YOUR_AWS_ACCESS_KEY_HERE
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY_HERE
AWS_REGION=ap-northeast-2

S3_BUCKET_NAME=YOUR_S3_BUCKET_NAME_HERE

GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

FAL_KEY=YOUR_FAL_KEY_HERE
