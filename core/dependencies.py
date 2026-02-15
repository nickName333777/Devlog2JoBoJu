"""
spring-boot의 Interceptor의 loginFilter같은 느낌(Interceptor 체인처럼 동작)

[A. Controller(라우터)에 적용 ]
- 단일 API에 적용
@router.get("/admin")
def admin_page(
    request: Request,
    user=Depends(admin_required)
):
    return templates.TemplateResponse(
        "pages/admin/index.html",
        {
            "request": request,
            "user": user
        }
    )

- Router 전체에 적용 (추천)
admin_router = APIRouter(
    prefix="/admin", # /admin/** 전부 관리자만 접근 가능
    dependencies=[Depends(admin_required)]
)

@admin_router.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse(
        "pages/admin/dashboard.html",
        {"request": request}
    )

[ B. ROLE 여러 개일 때 (실무형) ]
def role_required(*allowed_roles):
    def checker(user=Depends(login_required)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403)
        return user
    return checker

사용:

@router.get("/manage")
def manage(
    user=Depends(role_required("ROLE_ADMIN", "MANAGER")) # ROLE_ADMIN" if member.member_admin == 'Y' else "ROLE_USER"
):
    ...

"""
from fastapi import Request, HTTPException, status
from fastapi import Depends
from fastapi.responses import RedirectResponse

# 기본 로그인 체크 재사용
def login_required(request: Request):
    user = request.session.get("user") # user ==> loginMember
    if not user:
        # 1) AJAX 요청이면 JSON 에러 반환
        if request.headers.get("accept", "").startswith("application/json"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다")
        # 2) 일반 페이지 요청이면 redirect ==> NG: 이거 return 하면, 비회원인데도 "글쓰기"버튼보이고, 헤더에 "로그인 | 회원가입" 메뉴도 사라지는 문제있음
        #return RedirectResponse("/login", status_code=302) # FastAPI에서의 철칙: Dependency는 “데이터”만 반환해야 한다 =>  Response, RedirectResponse 반환하면 안 됨
        
    return user

# 관리자 권한 체크 Dependency
def admin_required(user=Depends(login_required)):
    if user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다"
        )
    return user
