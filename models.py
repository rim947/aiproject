from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, Numeric, Text, DateTime, JSON, TIMESTAMP
from datetime import datetime
from database import Base, engine
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "User"

    # ⭐️ String(50)에서 Integer로 수정! autoincrement가 이제 정상 작동합니다.
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(100), nullable=False)
    nickname = Column(String(30), nullable=False)
    height = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Image(Base):
    __tablename__ = "images"

    image_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # ⭐️ User.user_id가 Integer가 되었으므로 여기도 Integer로 변경!
    user_id = Column(Integer, ForeignKey("User.user_id"))
    image_url = Column(String(255))
    tags = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # ⭐️ 외래키 참조 타입을 Integer로 변경!
    user_id = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    mode = Column(String(10), nullable=False)
    tags = Column(JSON, nullable=False)
    custom_request = Column(Text, nullable=True)
    gender = Column(String(10), nullable=True)
    height = Column(Integer, nullable=True)
    summary = Column(String(255), nullable=True)
    user_image_url = Column(String(255), nullable=False)
    item_image_url = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    fitted_image_url = Column(String(512), nullable=True)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_id = Column(BigInteger, ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(String(100), nullable=False)  # AI가 준 "item_123" 저장
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=False)
    category = Column(String(50), nullable=True)
    score = Column(Numeric(4, 2), nullable=False)  # 0.89 같은 소수점 스코어 저장
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Result(Base):
    __tablename__ = "Result"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(BigInteger, ForeignKey("analysis.id")) # 외래키 문자열 형식 통일
    # ⭐️ 외래키 참조 타입을 Integer로 변경!
    user_id = Column(Integer, ForeignKey("User.user_id"))
    result_items = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

class History(Base):
    __tablename__ = "history"  # 또는 "histories"
    history_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.user_id"))
    tags = Column(Text)  # JSON 문자열이 들어가는 필드

# 💡 테이블 생성 코드는 클래스 정의가 다 끝난 '맨 아래'에 있어야 
# 파이썬이 테이블 구조를 모두 인식하고 MySQL에 완벽하게 만들어 줍니다!
Base.metadata.create_all(bind=engine)

