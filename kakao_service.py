"""
카카오 소셜 로그인 서비스
"""
import os
import requests
from urllib.parse import quote
from sqlalchemy.orm import Session
from typing import Optional

from dotenv import load_dotenv # 로컬 개발일때  + .env 사용
load_dotenv(override=True) # .env 파일 명시적 로드 (최우선)

from models import SocialLogin, Member, Level
from schemas import MemberLoginResponse, LevelDTO
from schemas import MemberLoginResponseMinimal
from kakao_schemas import MemberKakaoSocialLoginResponse

class KakaoService:
    """카카오 로그인 처리 서비스"""
    
    def __init__(self):
        self.kakao_rest_api_key = os.getenv("KAKAO_REST_API_KEY")
        self.kakao_client_secret = os.getenv("KAKAO_CLIENT_SECRET")
        self.kakao_redirect_uri = os.getenv("KAKAO_REDIRECT_URI")
        
        if not all([self.kakao_rest_api_key, self.kakao_redirect_uri]):
            raise ValueError("카카오 로그인 설정이 완료되지 않았습니다. 환경 변수를 확인하세요.")
    
    def get_kakao_auth_url(self) -> str:
        """카카오 인증 URL 생성"""
        base_url = "https://kauth.kakao.com/oauth/authorize"
        params = {
            "response_type": "code",
            "client_id": self.kakao_rest_api_key,
            "redirect_uri": self.kakao_redirect_uri
        }
        
        auth_url = f"{base_url}?response_type={params['response_type']}&client_id={params['client_id']}&redirect_uri={quote(params['redirect_uri'])}"
        return auth_url
    
    def get_kakao_access_token(self, code: str) -> str:
        """인가 코드로 액세스 토큰 받기"""
        token_url = "https://kauth.kakao.com/oauth/token"
        
        data = {
            "grant_type": "authorization_code",
            "client_id": self.kakao_rest_api_key,
            "redirect_uri": self.kakao_redirect_uri,
            "code": code
        }
        
        # client_secret이 있으면 추가
        if self.kakao_client_secret:
            data["client_secret"] = self.kakao_client_secret
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
        }
        
        response = requests.post(token_url, data=data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"카카오 토큰 요청 실패: {response.text}")
        
        token_data = response.json()
        return token_data.get("access_token")
    
    def get_kakao_user_info(self, access_token: str) -> dict:
        """액세스 토큰으로 사용자 정보 가져오기"""
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
        }
        
        response = requests.get(user_info_url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"카카오 사용자 정보 요청 실패: {response.text}")
        
        return response.json()
    
    def process_kakao_login(self, code: str, db: Session) -> MemberKakaoSocialLoginResponse:
        """카카오 로그인 전체 프로세스"""
        
        # 1. 액세스 토큰 받기
        access_token = self.get_kakao_access_token(code)
        print(f"✅ Access Token: {access_token[:20]}...")
        
        # 2. 사용자 정보 가져오기
        user_info = self.get_kakao_user_info(access_token)
        kakao_id = str(user_info.get("id"))
        print(f"✅ Kakao ID: {kakao_id}")
        
        # 3. SOCIAL_LOGIN 테이블 조회
        social_login = db.query(SocialLogin).filter(
            SocialLogin.provider == "kakao",
            SocialLogin.provider_id == kakao_id
        ).first()
        
        if social_login: # SocialLogin DB에 이미 존재 (kakao, kakao_id)
            # 기존 회원 - 로그인 처리
            member = db.query(Member).filter(
                Member.member_no == social_login.member_no
            ).first()
            
            if not member:
                raise Exception("회원 정보를 찾을 수 없습니다.")
            
            # 레벨 정보 조회
            level = db.query(Level).filter(
                Level.level_no == member.member_level_no
            ).first()
            
            level_dto = LevelDTO(
                level_no=level.level_no,
                title=level.title,
                required_total_exp=level.required_total_exp
            )
            
            # MemberLoginResponseMinimal 생성 # JWT 토큰생성 후 최소 필요한 로그인정보들 넘겨줄때 (헤더 정보 경우) 
            member_dto = MemberLoginResponseMinimal(
                member_no=member.member_no,
                member_email=member.member_email,
                member_nickname=member.member_nickname,
                role="ROLE_ADMIN" if member.member_admin == 'Y' else "ROLE_USER",
                profile_img=member.profile_img,
                beans_amount=member.beans_amount,
            )            
            
            return MemberKakaoSocialLoginResponse(
                member_dto=member_dto,
                access_token=access_token,
                kakao_id=kakao_id
            )
        else: # SocialLogin DB에 존재하지 않는 경우
            # 신규 회원 - 회원가입 필요
            return MemberKakaoSocialLoginResponse(
                member_dto=None,
                access_token=access_token,
                kakao_id=kakao_id
            )
