"""
JWT 인증 및 비밀번호 해싱 유틸리티
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt 
from fastapi import Depends, HTTPException, status

from passlib.context import CryptContext  # for pwd encrypt
from fastapi.security import OAuth2PasswordBearer # for 정적렌더링시 혹은 그냥 first 인가관리 방법 
#from sqlalchemy.orm import Session

import os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # for jinja2 + HTMLResponse? 혹은 그냥 second 인가관리 방법



# 환경변수로 관리해야 할 값들
# SECRET_KEY = "your-secret-key-change-this-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES =int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
# ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7")) # 24 사간 * 7
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # login pwd 검증용 

#####  OAuth2PasswordBearer & HTTPBearer: “Authorization: Bearer <token>” 헤더를 읽어오는 보안 의존성 클래스, 전제하고 있는 인증/프로토콜 수준이 다릅
# A) OAuth2PasswordBearer 클래스는 “OAuth2 패스워드 플로우용 고수준 래퍼
# OAuth2 기반 보안 스키마, 생성 시 tokenUrl="/member/login" 처럼 “클라이언트가 토큰을 받으러 갈 엔드포인트”를 지정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/member/login")  # for 정적렌더링시 or kakao login 혹은 그냥 first 인가관리 방법 

# B) HTTPBearer 클래스는 “프로토콜에 중립적인 로우레벨 Bearer 토큰 리더
# 저수준의 일반적인 HTTP Bearer 인증 스키마, OAuth2를 전제로 하지 않고, 그냥 “Authorization: Bearer <token>” 형식인지 검사하고, <token>을 꺼내 HTTPAuthorizationCredentials 객체로 넘겨 줍
security = HTTPBearer() #  for jinja2 + HTMLResponse? 혹은 그냥 second 인가관리 방법


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """비밀번호 검증"""
#     return pwd_context.verify(plain_password, hashed_password)
#
# def get_password_hash(password: str) -> str:
#     """비밀번호 해싱"""
#     return pwd_context.hash(password)

##### bcrypt 3.2.2 의 72바이트 제한 방어 (bcrypt는 무조건 72 byte 제한필요 아니면 제한없는 argon2-cffi 해시알고리즘사용 )
MAX_BCRYPT_LEN = 72

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password[:MAX_BCRYPT_LEN], hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password[:MAX_BCRYPT_LEN])



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None): # jose JWT: data in kakao_signup() of kakao_router.py
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        # expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    print("SECRET_KEY:", SECRET_KEY, type(SECRET_KEY))
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


##################################################################
##### first 인가관리: jose JWT
##################################################################

def decode_token(token: str): # jose JWT
    """JWT 토큰 디코딩"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)): # oauth2_scheme for 정적렌더링시 or kakao login 혹은 그냥 first 인가관리 방법 
    """현재 로그인한 사용자 정보 가져오기"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 토큰입니다.\n 인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    member_email: str = payload.get("sub") # see data in kakao_signup() of kakao_router.py (also loginMember.access_token in login.js) 
    if member_email is None:
        raise credentials_exception
    
    return {"member_email": member_email, "member_no": payload.get("member_no")} # loginMember의  두 필드값만 반환



##################################################################
##### second 인가관리 방법도 결국은 first 인가관리 방법, jose JWT
##################################################################
def verify_token(token: str) -> dict: # 위에 decode_token(token: str)과 결국 같은 함수
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user2(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict: #  security for jinja2 + HTMLResponse? 혹은 그냥 second 인가관리 방법
    """
    현재 로그인한 사용자 정보 가져오기 (필수):  HTTPAuthorizationCredentials 로 부터 가져온다 -> 그러면 localStrorage에 저장된 loginMember, access_code와는 어떤 관계?
    로그인하지 않은 경우 401 에러 발생
    """
    token = credentials.credentials # 요청에 담겨온 JWT token 
    payload = verify_token(token)
    return payload


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[dict]:
    """
    현재 로그인한 사용자 정보 가져오기 (선택)
    로그인하지 않은 경우 None 반환 (401에러 발생않시킨다는 말)
    - GET/POST 모두 안전
    """
    #if credentials is None:
    if credentials is None or not credentials.credentials:    
        return None
    
    token = credentials.credentials # 요청에 담겨온 JWT token 
    try:
        #token = credentials.credentials
        payload = verify_token(token) # 기존 토큰 검증
        return payload
    #except HTTPException:
    except Exception:
        # 토큰 검증 실패시에도 None 반환 (로그인 필요 없는 페이지용)
        return None




#####
def generate_auth_code() -> str: # for EmailAuth 용 인증코드 생성 햠스
    """6자리 인증 코드 생성 for Email-Auth (회원가입/필수 회원정보입력 페이지)"""
    import random
    import string
    
    code = ""
    for _ in range(6):
        sel = random.randint(0, 2)
        if sel == 0:
            code += str(random.randint(0, 9))
        else:
            ch = random.choice(string.ascii_uppercase)
            if random.randint(0, 1) == 0:
                ch = ch.lower()
            code += ch
    return code
