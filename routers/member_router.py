"""
회원 관련 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, date
from typing import Dict

from database import get_db
from models import Member, Level, Auth
from schemas import (
    MemberSignUpRequest, 
    MemberLoginRequest, 
    MemberLoginResponse,
    MemberLoginResponseMinimal, # # JWT 토큰생성 후 최소 필요한 로그인정보들 넘겨줄때 (헤더 정보 경우) (Session 에 로그인정보 저장의 경우와 같다)
    EmailAuthRequest,
    EmailAuthCheckRequest,
    DupCheckResponse,
    LevelDTO,
    SessionLoginMemberDTO # 세션 req.session["user"]에 loginMember필수정보 저장용
)
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    generate_auth_code,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
# # Jinja2 템플릿
from core.templates import templates

# JWT
from auth import get_current_user_optional #, get_current_user, get_current_user2
# loginMember Session에 저장
from core.dependencies import login_required, admin_required


router = APIRouter(prefix="/member", tags=["member"])

#router_auth = APIRouter(prefix="/api/auth/", tags=["auth_me"]) # AssertionError: A path prefix must not end with '/', as the routes will start with '/'
router_auth = APIRouter(prefix="/api/auth", tags=["auth_me"])

router_session = APIRouter(prefix="/api/session", tags=["session_check"])

##### for JWT + Session 혼용시 서버세션 유효한지 check(/api/session/check) on 2026/02/08 
@router_session.get("/check")
def check_session(request: Request):
    if not request.session.get("user"):
        return {"loggedIn": False}
    return {"loggedIn": True}
    # 혹은 return {"loggedIn": bool(request.session.get("user")) }

##### for chatbot(/api/auth/me) added on 2026/02/05
@router_auth.get("/me")
async def get_current_user_info(
    request: Request,
    #current_user: Member = Depends(get_current_user_optional) #  JWT
    #current_user: Member = Depends(login_required) # Session 
):
    if request.session.get("user"): 
        print("########## LOGIN SESSION:", request.session["user"])
    
    current_user = request.session.get("user") # 부모창과 자식창은 Session공유하므로, 여기서 user정보읽어야함
    print("########### /api/auth/me => current_user :", current_user)
    if current_user is not None: # Session에 loginMember 정보 있을때 (로그인 상태)
        return {
            "success": True,
            "member_no": current_user["member_no"],
            "member_nickname": current_user["member_nickname"],
            "profile_img": current_user["profile_img"],
            "beans_amount": current_user["beans_amount"]
        }
    else:  # Session에 loginMember 정보 없을때 (비로그인 상태)
        return {
            "success": False
        }

###################    
# Jinja2 템플릿
from core.templates import templates
# 템플릿 렌더링
@router.get("/signup") # 요청경로: "http://localhost:8880/member/signup"
def signup_page(request: Request):  # 또는 signup_page() of main.py에 FileResponse("templates/auth/signup.html") 쓸수도있음
                                    # => 이때 요청경로는 "http://localhost:8880/signup.html"
    return templates.TemplateResponse("auth/signup.html", {
        "request": request,
    })    
    
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: MemberSignUpRequest,
    db: Session = Depends(get_db)
):
    """회원가입"""
    # 이메일 중복 체크
    existing_member = db.query(Member).filter(
        Member.member_email == request.member_email
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다"
        )
    
    # 기본 레벨 조회 (LV1)
    default_level = db.query(Level).filter(Level.level_no == 1).first()
    if not default_level:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="기본 레벨이 존재하지 않습니다"
        )
    
    # 새 회원 생성
    new_member = Member(
        member_email=request.member_email,
        member_pw=get_password_hash(request.member_pw),
        member_name=request.member_name,
        member_nickname=request.member_nickname,
        member_tel=request.member_tel,
        member_career=request.member_career,
        member_subscribe=request.member_subscribe or 'N',
        member_admin=request.member_admin or 'N',
        member_level_no=1,
        member_del_fl='N',
        m_create_date=datetime.now(),
        subscription_price=0,
        beans_amount=0,
        current_exp=0
    )
    
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    return {
        "message": f"{request.member_nickname}님의 가입을 환영합니다. 로그인 후 서비스를 이용해 주세요.",
        "member_no": new_member.member_no
    }

###################    
# Jinja2 템플릿
#from core.templates import templates
# 템플릿 렌더링
@router.get("/login") # 요청경로: "http://localhost:8880/member/login"
def login_page(request: Request):   # 또는 login_page() of main.py에 FileResponse("templates/auth/login.html") 쓸수도있음
                                    # => 이때 요청경로는 "http://localhost:8880/login.html" 임
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
    })    

# @router.post("/login", response_model=MemberLoginResponse)
@router.post("/login", response_model=MemberLoginResponseMinimal)
async def login(
    request: MemberLoginRequest,
    response: Response,
    req: Request,
    db: Session = Depends(get_db)
):
    """로그인"""
    # 회원 조회
    member = db.query(Member).filter(
        Member.member_email == request.member_email,
        Member.member_del_fl == 'N'
    ).first()
    
    if not member or not verify_password(request.member_pw, member.member_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 일치하지 않습니다"
        )
    
    # 탈퇴 회원 체크
    if member.member_del_fl == 'Y':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="탈퇴한 회원입니다"
        )
    
    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": member.member_email,
            "member_no": member.member_no,
            "member_nickname": member.member_nickname,
            "role": "ROLE_ADMIN" if member.member_admin == 'Y' else "ROLE_USER",
            "profile_img": member.profile_img if member.profile_img is not None else None,
            "beans_amount": member.beans_amount
        },
        expires_delta=access_token_expires
    )
    
    # 아이디 저장 쿠키 처리
    if request.save_id:
        response.set_cookie(
            key="saveId",
            value=member.member_email,
            max_age=60*60*24*30,  # 30일
            path="/"
        )
    else:
        response.delete_cookie(key="saveId", path="/")
    
    # 하루 1회 로그인 경험치 지급
    today = date.today().isoformat()
    cookie_name = f"EXP_{today}"
    exp_cookie = req.cookies.get(cookie_name, "")
    
    can_gain_exp = f"|{member.member_no}|" not in exp_cookie
    
    if can_gain_exp:
        # 경험치 증가
        member.current_exp += 50
        
        # 레벨업 체크
        new_level = db.query(Level).filter(
            Level.required_total_exp <= member.current_exp
        ).order_by(Level.level_no.desc()).first()
        
        if new_level and new_level.level_no > member.member_level_no:
            member.member_level_no = new_level.level_no
        
        db.commit()
        db.refresh(member)
        
        # 경험치 쿠키 설정
        new_cookie_value = exp_cookie + f"{member.member_no}|"
        now = datetime.now()
        next_midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        seconds_until_midnight = int((next_midnight - now).total_seconds())
        
        response.set_cookie(
            key=cookie_name,
            value=new_cookie_value,
            max_age=seconds_until_midnight,
            path="/"
        )
    
    # 레벨 정보 조회
    level = db.query(Level).filter(Level.level_no == member.member_level_no).first()
    level_dto = LevelDTO(
        level_no=level.level_no,
        title=level.title,
        required_total_exp=level.required_total_exp
    )
    
    # loginMember 세션 설정: 로그인 성공 시 loginMember 필수정보 Session저장 관리(JWT말고 Session에)
    # -> SessionLoginMemberDTO() from schemas.py
    # -> core/dependencies.py로 loginFilter처럼 로그인체크 처리
    req.session["user"] = SessionLoginMemberDTO(
        member_no=member.member_no,
        member_email=member.member_email,
        member_nickname=member.member_nickname,
        role="ROLE_ADMIN" if member.member_admin == 'Y' else "ROLE_USER",
        profile_img=member.profile_img,
        beans_amount=member.beans_amount
    ).dict()
    
    print("########## LOGIN SESSION:", req.session["user"])
    
    # 응답 생성
    # return MemberLoginResponse(
    #     member_no=member.member_no,
    #     member_email=member.member_email,
    #     member_nickname=member.member_nickname,
    #     role="ROLE_ADMIN" if member.member_admin == 'Y' else "ROLE_USER",
    #     member_admin=member.member_admin,
    #     member_subscribe=member.member_subscribe,
    #     member_del_fl=member.member_del_fl,
    #     member_career=member.member_career,
    #     profile_img=member.profile_img,
    #     my_info_intro=member.my_info_intro,
    #     my_info_git=member.my_info_git,
    #     my_info_homepage=member.my_info_homepage,
    #     subscription_price=member.subscription_price,
    #     beans_amount=member.beans_amount,
    #     current_exp=member.current_exp,
    #     m_create_date=member.m_create_date,
    #     level=level_dto,
    #     access_token=access_token # 유효 access_token 추가
    # )
    return MemberLoginResponseMinimal( # JWT 토큰생성 후 최소 필요한 로그인정보들 넘겨줄때 (헤더 정보 경우) (Session 에 로그인정보 저장의 경우와 같다)
        member_no=member.member_no,
        member_email=member.member_email,
        member_nickname=member.member_nickname,
        role="ROLE_ADMIN" if member.member_admin == 'Y' else "ROLE_USER",
        profile_img=member.profile_img,
        beans_amount=member.beans_amount
    )


@router.get("/logout")
async def logout(req: Request):
    """로그아웃"""
    # 즉시 세션 무효화
    req.session.clear()
    # 쿠키 삭제
    #response.delete_cookie(key="saveId", path="/") # 계속 saveId 남기려면 comment-out?
    return {"message": "로그아웃 성공"}

#@router.post("/logout")
#def logout(req: Request):
#    req.session.clear()
#    return {"message": "로그아웃 성공"}

@router.get("/dupcheck/email", response_model=DupCheckResponse)
async def check_email_duplicate(email: str, db: Session = Depends(get_db)):
    """이메일 중복 체크"""
    exists = db.query(Member).filter(Member.member_email == email).first() is not None
    return DupCheckResponse(
        exists=exists,
        message="이미 사용 중인 이메일입니다" if exists else "사용 가능한 이메일입니다"
    )


@router.get("/dupcheck/nickname", response_model=DupCheckResponse)
async def check_nickname_duplicate(nickname: str, db: Session = Depends(get_db)):
    """닉네임 중복 체크"""
    exists = db.query(Member).filter(Member.member_nickname == nickname).first() is not None
    return DupCheckResponse(
        exists=exists,
        message="이미 사용 중인 닉네임입니다" if exists else "사용 가능한 닉네임입니다"
    )
    
    

#@router.post("/checkCode/adminCode") # DB로 관리시
@router.get("/checkCode/adminCode") # hardcode 시
async def check_admin_code(admin_code: str): #FastAPI는 파라미터 이름 엄격: admin_code ≠ adminCode
    """관리자 승인 코드 확인"""
    # 실제로는 DB에서 관리하는 것이 좋음
    ADMIN_CODE = "JoBoJu1234"
    
    if admin_code == ADMIN_CODE:
        return {"result": 1, "message": "승인된 코드입니다"}
    else:
        return {"result": 0, "message": "승인되지 않은 코드입니다"}
