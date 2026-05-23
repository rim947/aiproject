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
```text
ai_fashion/
├── main.py            # 서버 실행 및 메인 로직
├── database.py        # 데이터베이스 연결 및 설정
├── schema.py          # 데이터 모델 및 스키마 정의
├── ai_request.json    # AI 요청 데이터 샘플
├── .gitignore         # 깃허브 제외 파일 설정 (.env 차단)
└── README.md          # 프로젝트 설명서 (현재 파일)


## Environment Variables (환경 변수 세팅)
AWS_ACCESS_KEY=YOUR_AWS_ACCESS_KEY_HERE
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY_HERE
AWS_REGION=ap-northeast-2

S3_BUCKET_NAME=YOUR_S3_BUCKET_NAME_HERE

GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

FAL_KEY=YOUR_FAL_KEY_HERE
