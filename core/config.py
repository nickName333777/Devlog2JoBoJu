# .env  처리,  config.py 임포트사용
import os
from dotenv import load_dotenv # 로컬 개발일때  + .env 사용
load_dotenv(override=True)

# 이메일 설정 (환경변수로 관리) => email_router.py
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# kakao social login => kakao_service.py
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

# 환경변수에서 DB 정보 가져오기 => database.py
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_SERVICE = os.getenv("DB_SERVICE")
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")


# CORS, Session, UPLOAD_DIR설정 =>  main.py 
#CORS_ORIGINS = os.getenv("CORS_ORIGINS")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
UPLOAD_DIR = os.getenv("UPLOAD_DIR")
