"""
FastAPI 메인 애플리케이션
Jinja2 템플릿 엔진 통합
"""
### web-framework
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware # 로그인 유지/만료 세션에서 관리위함

### StaticFiles/FileResponse -> 정적파일서빙
from fastapi.staticfiles import StaticFiles # 
from fastapi.responses import FileResponse  # FileResponse: 요청 시 특정 파일을 직접 반환

### StaticFiles/Jinja2Templates -> 동적 템플릿 렌더링 
from core.templates import templates # jinja2 관련 처리 여기서 (원형 임포트(main → router → main) 방지)

# jinja2 SSR 동적 URL 페이지 렌더링용(여기서는 "/" only)
from fastapi import Request
from fastapi.responses import HTMLResponse

from pathlib import Path
import os
from dotenv import load_dotenv
# 환경 변수 로드
load_dotenv(override=True) # .env 파일 명시적 로드 (최우선)


# web-server
import uvicorn


from database import engine, Base

# loginMember Session에 저장 (header UI위한 loginMember 정보 저장용)
from fastapi import Depends
from core.dependencies import login_required, admin_required


app = FastAPI(
    title="JoBoJu API",
    description="재생에너지 장비 관리 플랫폼 API",
    version="1.0.0"
)


# Session 설정(CORS 미들웨어보다 먼저) (=> JWT 토큰 설정과 비교/조정할 필요가 있다)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY"), # 세션 암호화위한 key
    max_age=60 * 60,   # 60분 활동없으면 자동 로그아웃 
    same_site="lax",   # CSRF 기본 방어
    https_only=False  # HTTPS에서만 쿠키 전달, 운영에서는 True
)


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8880"],  # 프론트엔드 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

allow_credentials=True #중요 (세션은 쿠키 기반) # docker restart jbj-fastapi


# ============================================
# 정적 파일 & 템플릿 설정
# ============================================

##### 정적 파일 (CSS, JS, images) 서빙 BY StaticFiles/FileResponse 
app.mount("/static", StaticFiles(directory="static"), name="static")

# 업로드 파일 (사용자 업로드 이미지)
UPLOAD_DIR = os.getenv("UPLOAD_DIR")
if os.path.exists(UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ============================================
# 라우터 등록
# ============================================

# 기존 라우터 (API): 라우터 등록
from routers import member_router, email_router, kakao_router, board_router # for bypass
app.include_router(member_router.router) # router = APIRouter(prefix="/member", tags=["member"])
app.include_router(email_router.router) # router = APIRouter(prefix="/sendEmail", tags=["email"])
app.include_router(kakao_router.router) # for 카카오 소셜로그인, router = APIRouter(prefix="/app/login", tags=["kakao"])
app.include_router(board_router.router) # board 동기 목록조회, router = APIRouter(prefix="/board", tags=["게시판"]) # 게시판 동기 목록 조회(URL 페이지 렌더링, VIEW)
app.include_router(board_router.router_ajax) # board 비동기 목록조회, router_ajax = APIRouter(prefix="/api/board", tags=["게시판비동기"]) # 게시판 비동기 목록 조회(AJAX 데이터용, JSON)

from routers import board_write_router
app.include_router(board_write_router.bcu_router) # (board write, update, delete), bcu_router = APIRouter(prefix="/board2", tags=["게시판-작성/수정"])

# 좋아요 + 댓글 CRUD API 라우터 (AJAX용 JSON)
from routers import comment_like_router
app.include_router(comment_like_router.router) # router = APIRouter(prefix="/api/board", tags=["좋아요/댓글-API"])

# 전역 예외 핸들러 등록
from exceptions import register_exception_handlers # FastAPI 앱에 전역 예외 핸들러 등록
register_exception_handlers(app)

# 챗봇 라우터
from routers import chatbot_router
app.include_router(chatbot_router.router) # router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

# 로그인인증 api, JWT-Session 혼용시 index.html 페이지 로드시 서버 세션확인 api
app.include_router(member_router.router_auth)  # router_auth = APIRouter(prefix="/api/auth/", tags=["auth_me"])
app.include_router(member_router.router_session)  # router_session = APIRouter(prefix="/api/session", tags=["session_check"])

# ============================================
# 테이블 생성
# ============================================
# DB 접속시점 안정화: import 시점 실행 → DB 잠깐만 늦어도 폭사하므로 이거 방지
@app.on_event("startup") # 이거 안통하면 컨테이너 재시작: $ docker restart jbj-fastapi
def startup():
    Base.metadata.create_all(bind=engine)

# ============================================
# 헬스 체크
# ============================================
# Health Check
@app.get("/health")
async def health_check():
    print("####################################FastAPI works, anyway...")
    #return {"status": "healthy"}
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "message": "FastAPI server is running",
        "environment": os.getenv("ENVIRONMENT", "development_default")
    }    

# ============================================
# favicon.icon 로딩
# ============================================
# favicon.icon 경로 설정
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

# ============================================
# 메인 페이지 (old): FileResponse 정적 서빙?
# 모두 GET 요청주소
# ============================================
# 루트 경로 - index.html 서빙
@app.get("/")
async def read_root():
    return FileResponse("static/index.html") # FileResponse: 요청 시 특정 파일을 직접 반환

@app.get("/index.html")
async def index_page():
    return FileResponse("static/index.html")

# HTML 페이지 라우팅
@app.get("/login.html")
async def login_page():
    return FileResponse("templates/auth/login.html") # working for jinja2 case

@app.get("/signup.html")
async def signup_page():
    return FileResponse("templates/auth/signup.html")  # working for jinja2 case

@app.get("/signupKakao.html")
async def signup_kakao_page():
    return FileResponse("templates/auth/signupKakao.html")  # working for jinja2 case

# ============================================
# 메인 페이지(임시): jinja2-HTMLResponse 동적 렌더링
# ============================================

@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    current_user = Depends(login_required),
               ): # inja2는 반드시 request를 넘겨야 함
    """메인 페이지"""
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "current_user": current_user,
        "title": "제이비제이 JoBoJu"
    })

# 임시 화면 테스트용 => 테스트후  해당_router.py 만들어서 router (.get & .post)작성해서 정식 요청경로로 app 에 등록
@app.get("/testMonitoringDashboard", response_class=HTMLResponse)
async def test_monitoring_dashboard(
    request: Request,
    current_user = Depends(login_required), # header에 loginMember 정보 저장용
    ): # 
    """메인 페이지"""
    return templates.TemplateResponse("monitoringDashboard/monitoringDashboard.html", {
        "request": request, 
        "current_user": current_user,
        "title": "모니터링 대시보드"
    })

# ============================================
# 앱 시작
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8880,
        reload=True  # 개발 환경에서만 True
    )
