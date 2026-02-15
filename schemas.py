"""
Pydantic Schemas (DTO) for Request/Response validation (Member, EmailAuth, Dupcheck)
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re


class LevelDTO(BaseModel):
    level_no: int
    title: str
    required_total_exp: int
    
    class Config:
        from_attributes = True


class MemberSignUpRequest(BaseModel):
    """회원가입 요청 DTO"""
    member_email: EmailStr
    member_pw: str = Field(..., min_length=6, max_length=20)
    member_name: str = Field(..., min_length=2, max_length=15)
    member_nickname: str = Field(..., min_length=2, max_length=10)
    member_tel: str = Field(..., min_length=10, max_length=11)
    member_career: str = Field(..., min_length=2, max_length=40)
    member_subscribe: Optional[str] = 'N'
    member_admin: Optional[str] = 'N'
    
    @validator('member_pw')
    def validate_password(cls, v):
        if not re.match(r'^[\w!@#\-_]{6,20}$', v):
            raise ValueError('비밀번호는 영어, 숫자, 특수문자(!,@,#,-,_) 6~20자여야 합니다')
        return v
    
    @validator('member_name')
    def validate_name(cls, v):
        if not re.match(r'^[가-힣]{2,15}$', v):
            raise ValueError('이름은 한글 2~15자여야 합니다')
        return v
    
    @validator('member_nickname')
    def validate_nickname(cls, v):
        if not re.match(r'^[가-힣a-zA-Z0-9]{2,10}$', v):
            raise ValueError('닉네임은 한글, 영어, 숫자 2~10자여야 합니다')
        return v
    
    @validator('member_tel')
    def validate_tel(cls, v):
        if not re.match(r'^0(1[01]|2|[3-6][1-5]|70)\d{7,8}$', v):
            raise ValueError('유효하지 않은 전화번호 형식입니다')
        return v
    
    @validator('member_career')
    def validate_career(cls, v):
        if not re.match(r'^(?=.*[가-힣])(?=.*[0-9])[가-힣0-9 ]{2,40}$', v):
            raise ValueError('경력사항은 한글과 숫자를 포함한 2~40자여야 합니다')
        return v


class MemberLoginRequest(BaseModel):
    """로그인 요청 DTO"""
    member_email: EmailStr
    member_pw: str
    save_id: Optional[bool] = False


class MemberLoginResponse(BaseModel): # full로 넘겨줄때 (내정보페이지 같은경우)
    """로그인 응답 DTO"""
    member_no: int
    member_email: str
    member_nickname: str
    role: str
    member_admin: str
    member_subscribe: str
    member_del_fl: str
    member_career: str
    profile_img: Optional[str]
    my_info_intro: Optional[str]
    my_info_git: Optional[str]
    my_info_homepage: Optional[str]
    subscription_price: int
    beans_amount: int
    current_exp: int
    m_create_date: datetime
    level: LevelDTO
    access_token: str
    token_type: str = "bearer"
    
    class Config:
        from_attributes = True

class MemberLoginResponseMinimal(BaseModel): # JWT 토큰생성 후 최소 필요한 로그인정보들 넘겨줄때 (헤더 정보 경우) (Session 에 로그인정보 저장의 경우와 같다)
    """로그인 응답 DTO"""
    member_no: int
    member_email: str
    member_nickname: str
    role: str
    profile_img: Optional[str]
    beans_amount: int   
    class Config:
        from_attributes = True



class EmailAuthRequest(BaseModel):
    """이메일 인증 요청 DTO"""
    email: EmailStr


class EmailAuthCheckRequest(BaseModel):
    """이메일 인증 확인 요청 DTO"""
    input_key: str
    email: EmailStr


class DupCheckResponse(BaseModel):
    """중복 체크 응답 DTO"""
    exists: bool
    message: str

# loginMember (-> user)를 세션에 저장하기위한 DTD -> member_router.py, kakao_service.py
class SessionLoginMemberDTO(BaseModel):
    member_no: int
    member_email: str
    member_nickname: str
    role: str
    profile_img: Optional[str]
    beans_amount: int # for 챗봇, added on 2026/02/06
    