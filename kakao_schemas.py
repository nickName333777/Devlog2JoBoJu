"""
카카오 소셜 로그인 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional
from schemas import MemberLoginResponse


class KakaoTokenResponse(BaseModel):
    """카카오 토큰 응답"""
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: int
    scope: Optional[str] = None


class KakaoUserInfo(BaseModel):
    """카카오 사용자 정보"""
    id: int
    kakao_account: Optional[dict] = None
    properties: Optional[dict] = None


class SocialLoginCreate(BaseModel):
    """소셜 로그인 생성 DTO"""
    provider: str
    provider_id: str
    member_no: int


class SocialLoginResponse(BaseModel):
    """소셜 로그인 응답 DTO"""
    social_no: int
    provider: str
    provider_id: str
    member_no: int
    
    class Config:
        from_attributes = True


class MemberKakaoSocialLoginResponse(BaseModel):
    """카카오 소셜 로그인 응답 DTO"""
    member_dto: Optional[MemberLoginResponse] = None
    access_token: str
    kakao_id: str
    
    class Config:
        from_attributes = True
