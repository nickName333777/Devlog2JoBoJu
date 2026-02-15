"""
카카오 소셜 로그인 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from database import get_db
from kakao_service import KakaoService
from models import Member, SocialLogin
from auth import get_password_hash, create_access_token
from schemas import MemberSignUpRequest
from datetime import timedelta

from schemas import MemberLoginResponse, LevelDTO
from schemas import MemberLoginResponseMinimal
from schemas import SessionLoginMemberDTO

router = APIRouter(prefix="/app/login", tags=["kakao"])

kakao_service = KakaoService()


@router.get("/kakao")
async def kakao_auth_redirect():
    """카카오 인증 서버로 리다이렉트"""
    kakao_auth_url = kakao_service.get_kakao_auth_url()
    return RedirectResponse(url=kakao_auth_url)


@router.get("/kakao/callback")
async def kakao_callback(
    code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """카카오 인증 콜백 처리"""
    
    try:
        # 카카오 로그인 처리
        result = kakao_service.process_kakao_login(code, db)
        
        if result.member_dto: # SocialLogin DB에 이미 존재(kakao, kakao_id)-> memberNo존재 -> MemberLoginResponse-DTO 반환
            # 기존 회원 - JWT 토큰 생성 후 메인 페이지로
            access_token_expires = timedelta(minutes=60 * 24)  # 24시간 in minutes
            jwt_token = create_access_token(
                data={
                    "sub": result.member_dto.member_email,
                    "member_no": result.member_dto.member_no,
                    "member_nickname": result.member_dto.member_nickname,
                    "role": result.member_dto.role,
                    "profile_img": result.member_dto.profile_img if result.member_dto.profile_img is not None else None,
                    "beans_amount": result.member_dto.beans_amount
                },
                expires_delta=access_token_expires
            )
            
            # loginMember의 access_token 필드에 유효 JWT 토큰 추가
            result.member_dto.access_token = jwt_token
            
            
			# loginMember 세션 설정: 로그인 성공 시 loginMember 필수정보 Session저장 관리(JWT말고 Session에)
			# -> SessionLoginMemberDTO() from schemas.py
			# -> core/dependencies.py로 loginFilter처럼 로그인체크 처리
            request.session["user"] = SessionLoginMemberDTO(
				member_no=result.member_dto.member_no,
				member_email=result.member_dto.member_email,
				member_nickname=result.member_dto.member_nickname,
				role="ROLE_ADMIN" if result.member_dto.member_admin == 'Y' else "ROLE_USER",
				profile_img=result.member_dto.profile_img,
                beans_amount=result.member_dto.beans_amount # for chatbot
			).dict()               
            
            
            # HTML 응답으로 토큰을 localStorage에 저장하고 메인페이지로 리다이렉트
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>로그인 중...</title>
            </head>
            <body>
                <script>
                    // 로그인 정보 저장
                    localStorage.setItem('access_token', '{jwt_token}');
                    localStorage.setItem('loginMember', '{result.member_dto.json()}');
                    
                    // 메인 페이지로 이동
                    window.location.href = '/';
                </script>
                <p>로그인 중입니다. 잠시만 기다려주세요...</p>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        else: # # SocialLogin DB에 존재하지 않아 memberNo없음(MemberLoginResponse-DTO 생성불가) 
            # 신규 회원 - 회원가입 페이지로 리다이렉트
            # kakao_id를 세션에 저장 (쿠키 방식)
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>필수 회원정보 입력 필요</title>
            </head>
            <body>
                <script>
                    // 카카오 ID를 sessionStorage에 저장
                    sessionStorage.setItem('kakaoId', '{result.kakao_id}');
                    
                    // 필수 회원정보 입력 페이지로 이동
                    alert('카카오 로그인에 성공했습니다.\\nJoBoJu 서비스를 원활히 이용하시기 위해서는 필수 회원 정보가 필요합니다.\\n회원 정보를 입력해 주세요. 감사합니다.');
                    window.location.href = '/app/login/kakao/signup';
                </script>
                <p>필수 회원정보 입력 페이지로 이동 중입니다...</p>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
    
    except Exception as e:
        print(f"❌ 카카오 로그인 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카카오 로그인 처리 중 오류가 발생했습니다: {str(e)}"
        )

###################    
# Jinja2 템플릿
from core.templates import templates
# 템플릿 렌더링
@router.get("/kakao/signup") # 요청경로: "http://localhost:8880/kakao/signup"
def signup_kakao_page(request: Request):    # 또는 signup_kakao_page() of main.py에 FileResponse("templates/auth/signupKakao.html") 쓸수도있음
                                            # => 이때 요청경로는 "http://localhost:8880/signupKakao.html" 
    return templates.TemplateResponse("auth/signupKakao.html", {
        "request": request,
    })    

@router.post("/kakao/signup")
async def kakao_signup(
    request: MemberSignUpRequest,
    kakao_id: str,
    req: Request,
    db: Session = Depends(get_db)
):
    """카카오 로그인 후 필수 회원정보 입력 완료"""
    
    # 이메일 중복 체크
    existing_member = db.query(Member).filter(
        Member.member_email == request.member_email
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다"
        )
    
    # 기본 레벨 조회
    from models import Level
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
        member_subscribe=request.member_subscribe or 'N', # 기본값 설정패턴: 왼쪽값이 참(truthy)면 그걸쓰고 거짓(falsy)이면 'N'을 쓴다
        member_admin='N',
        member_level_no=1,
        member_del_fl='N'
    )
    
    db.add(new_member)
    db.flush()  # member_no 생성
    
    # SocialLogin 레코드 생성
    social_login = SocialLogin(
        provider="kakao",
        provider_id=kakao_id,
        member_no=new_member.member_no
    )
    
    db.add(social_login)
    db.commit()
    db.refresh(new_member)
    
    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=60 * 24) # in minutes: 
    access_token = create_access_token(
        data={
            "sub": new_member.member_email,
            "member_no": new_member.member_no,
            "member_nickname": new_member.member_nickname,
            "role": "ROLE_USER", # kakao login회원은 "ROLE_USER" only
            "profile_img": new_member.profile_img if member.profile_img is not None else None, # kakao new_member 는 무조건 None 경우
            "beans_amount": new_member.beans_amount           
        },
        expires_delta=access_token_expires
    )
    
    ################
    # 필수회원정보를 입력한 카카오 소셜로그인 신규 회원은 재로그인 할 필요없이 그대로 사이트 이용할 수 있도록
    # 1단계: default_level로 부터 레벨 DTO생성하고, new_member로부터 MemberLoginResponse생성.  
    # 1단계: loginMember 세션 설정: 로그인 성공 시 loginMember 필수정보 Session저장 
    # 2단계: HTML 응답으로 토큰을 localStorage에 저장후 메인화면으로 리다이렉트
    # [1단계] 레벨 정보 조회
    level_dto = LevelDTO(
        level_no=default_level.level_no,
        title=default_level.title,
        required_total_exp=default_level.required_total_exp
    )
    # [1단계] 방금 필수회원정보를 입력완료한 카카오 소셜로그인 신규 회원 정보 가져오기: # 회원 조회
    member = db.query(Member).filter(
        Member.member_email == new_member.member_email,
        Member.member_del_fl == 'N'
    ).first()
    
    # [1단계] MemberLoginResponse 생성
    member_dto = MemberLoginResponseMinimal( # JWT 토큰생성 후 최소 필요한 로그인정보들 넘겨줄때 (헤더 정보 경우) (Session 에 로그인정보 저장의 경우와 같다)
        member_no=member.member_no,
        member_email=member.member_email,
        member_nickname=member.member_nickname,
        role="ROLE_ADMIN" if member.member_admin == 'Y' else "ROLE_USER",
        profile_img=member.profile_img,
        beans_amount=member.beans_amount,
    )
    
    
    # [1단계] loginMember 세션 설정: 로그인 성공 시 loginMember 필수정보 Session저장 관리(JWT말고 Session에)
    # -> SessionLoginMemberDTO() from schemas.py
    # -> core/dependencies.py로 loginFilter처럼 로그인체크 처리
    req.session["user"] = SessionLoginMemberDTO(
        member_no=member.member_no,
        member_email=member.member_email,
        member_nickname=member.member_nickname,
        role="ROLE_ADMIN" if member.member_admin == 'Y' else "ROLE_USER",
        profile_img=member.profile_img,
        beans_amount=member.beans_amount # for chatbot
    ).dict()    
    
    # # [2단계]:  HTML 응답으로 토큰을 localStorage에 저장후 메인화면으로 리다이렉트대신 JSON 반환
    # html_content = f"""
    # <!DOCTYPE html>
    # <html>
    # <head>
    #     <title>로그인 중...</title>
    # </head>
    # <body>
    #     <script>
    #         // 로그인 정보 저장
    #         localStorage.setItem('access_token', '{access_token}');
    #         localStorage.setItem('loginMember', '{member_dto.json()}');
            
    #         // 메인 페이지로 이동
    #         window.location.href = '/index.html';
    #     </script>
    #     <p>로그인 중입니다. 잠시만 기다려주세요...</p>
    # </body>
    # </html>
    # """
    # HTMLResponse(content=html_content) 
    
    return {
        "message": f"{request.member_nickname}님, 필수 회원정보 입력이 완료되었습니다!",
        "access_token": access_token,
        "member_no": new_member.member_no,
        "member_dto": member_dto # 필수회원정보입력 완료후 로그인 상태 유지위함
    }
