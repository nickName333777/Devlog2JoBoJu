"""
챗봇 서비스 - OpenAI API 연동
Author: Claude (Anthropic)
Date: 2026-02-05

주요 기능:
- OpenAI gpt-4o-mini 모델 호출
- 시스템 프롬프트 생성 (BASIC/KONG 타입별)
- 토큰 사용량 계산 및 커피콩 환산
- 세션별 누적 토큰 메모리 캐싱
"""
import os
import math
import logging
from typing import Dict, Optional
from openai import OpenAI
from sqlalchemy.orm import Session

#from models_chatbot import CbSession, CbTokenUsage
from models import CbSession, CbTokenUsage
from models import Member

from dotenv import load_dotenv # 로컬 개발일때  + .env 사용
load_dotenv(override=True) # .env 파일 명시적 로드 (최우선)

# 로깅 설정
logger = logging.getLogger(__name__)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 토큰당 커피콩 환산 비율
TOKENS_PER_BEAN = int(os.getenv("TOKENS_PER_BEAN", "5"))  # 테스트용 (실제: 500)

# 세션별 누적 토큰 메모리 캐시 (ConcurrentHashMap → Python dict)
accumulated_tokens_cache: Dict[int, int] = {}


class ChatbotService:
    """
    챗봇 서비스 클래스
    - OpenAI API 연동
    - 토큰 관리
    - 과금 처리
    """
    
    @staticmethod
    def create_system_prompt(cb_session_type: str) -> str:
        """
        챗봇 타입별 시스템 프롬프트 생성
        
        Args:
            cb_session_type: BASIC 또는 KONG
            
        Returns:
            시스템 프롬프트 문자열
        """
        if cb_session_type == "BASIC":
            # BASIC 타입: 20자 제한 (테스트용, 실제는 500자)
            return """당신은 DevLog 자유게시판의 AI 어시스턴트입니다.
사용자의 질문에 친절하고 정확하게 답변해주세요.
**중요: 모든 답변은 반드시 20자 이내로 간결하게 작성해주세요.**
핵심 내용만 포함하고 불필요한 설명은 생략하세요."""
        else:
            # KONG 타입: 제한 없음
            return """당신은 DevLog 자유게시판의 프리미엄 AI 어시스턴트입니다.
사용자의 질문에 친절하고 정확하게 답변해주세요.
필요한 경우 자세한 설명과 예시를 포함하여 답변할 수 있습니다."""
    
    @staticmethod
    def calculate_beans(tokens: int) -> int:
        """
        토큰 수를 커피콩으로 환산
        
        Args:
            tokens: 토큰 수
            
        Returns:
            커피콩 포인트 (올림)
        """
        return math.ceil(tokens / TOKENS_PER_BEAN)
    
    @staticmethod
    async def send_message(
        session_id: int,
        cb_session_type: str,
        user_message: str,
        member_no: int,
        db: Session
    ) -> Dict:
        """
        챗봇 메시지 처리 (OpenAI API 호출 + 토큰 기록)
        
        Args:
            session_id: 챗봇 세션 ID
            cb_session_type: BASIC 또는 KONG
            user_message: 사용자 메시지
            member_no: 회원 번호
            db: 데이터베이스 세션
            
        Returns:
            응답 딕셔너리 {reply, usage}
        """
        logger.info(f"챗봇 요청 - 세션ID: {session_id}, 회원번호: {member_no}, 메시지: {user_message}")
        
        try:
            # 시스템 프롬프트 생성
            system_prompt = ChatbotService.create_system_prompt(cb_session_type)
            
            # OpenAI API 호출
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            # AI 응답 추출
            ai_answer = response.choices[0].message.content
            
            # 토큰 사용량 정보
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            # 세션별 누적 토큰 계산
            accumulated_tokens = accumulated_tokens_cache.get(session_id, 0) + total_tokens
            accumulated_tokens_cache[session_id] = accumulated_tokens
            
            # 커피콩 계산
            current_turn_beans = ChatbotService.calculate_beans(total_tokens)
            accumulated_used_beans = ChatbotService.calculate_beans(accumulated_tokens)
            
            logger.info(f"=== 토큰 사용량 상세 ===")
            logger.info(f"현재 턴 - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
            logger.info(f"누적 - AccumulatedTokens: {accumulated_tokens}")
            logger.info(f"커피콩 - 현재턴: {current_turn_beans}, 누적: {accumulated_used_beans}")
            logger.info(f"=====================")
            
            # 토큰 사용량 DB 저장 (KONG 타입만)
            if cb_session_type == "KONG":
                token_usage = CbTokenUsage(
                    prompt_text=user_message,
                    answer_text=ai_answer,
                    prompt_tokens=prompt_tokens,
                    answer_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    bean_swe=current_turn_beans,
                    model_name="gpt-4o-mini",
                    member_no=member_no,
                    cb_session_id=session_id
                )
                db.add(token_usage)
                db.commit()
                
                logger.info(f"토큰 사용 기록 저장 완료 - 회원번호: {member_no}, 총 토큰: {total_tokens}, 차감할 커피콩: {current_turn_beans}")
                
                # 회원의 현재 잔여콩 확인
                member = db.query(Member).filter(Member.member_no == member_no).first()
                if member:
                    current_beans = member.beans_amount or 0
                    remaining_beans = current_beans - accumulated_used_beans
                    
                    logger.info(f"회원 {member_no} - 보유콩: {current_beans}, 누적사용콩: {accumulated_used_beans}, 잔여콩: {remaining_beans}")
                    
                    if remaining_beans < 0:
                        logger.warning(f"회원 {member_no} 커피콩 부족! 현재: {current_beans}, 사용: {accumulated_used_beans}, 부족: {abs(remaining_beans)}")
                    else:
                        logger.info(f"회원 {member_no} 커피콩 충분 - 잔여: {remaining_beans} 콩")
            
            # 응답 생성
            result = {
                "reply": ai_answer,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "accumulated_tokens": accumulated_tokens,
                    "accumulated_usedBeans": accumulated_used_beans
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"챗봇 처리 중 오류 발생: {e}", exc_info=True)
            return {
                "reply": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "error": str(e)
            }
    
    @staticmethod
    def get_usage_by_member(member_no: int, db: Session) -> Dict:
        """
        회원의 토큰 사용량 조회
        
        Args:
            member_no: 회원 번호
            db: 데이터베이스 세션
            
        Returns:
            토큰 사용량 정보 {totalTokens, totalBeans, remainingBeans}
        """
        # 총 토큰 수 계산
        total_tokens_result = db.query(
            db.func.sum(CbTokenUsage.total_tokens)
        ).filter(CbTokenUsage.member_no == member_no).scalar()
        
        total_tokens = total_tokens_result or 0
        
        # 총 커피콩 계산
        total_beans_result = db.query(
            db.func.sum(CbTokenUsage.bean_swe)
        ).filter(CbTokenUsage.member_no == member_no).scalar()
        
        total_beans = total_beans_result or 0
        
        # 현재 잔여 커피콩
        member = db.query(Member).filter(Member.member_no == member_no).first()
        remaining_beans = member.beans_amount if member and member.beans_amount else 0
        
        return {
            "totalTokens": total_tokens,
            "totalBeans": total_beans,
            "remainingBeans": remaining_beans
        }
    
    @staticmethod
    def clear_session(session_id: int):
        """
        세션 종료 시 메모리에서 누적 토큰 정리
        
        Args:
            session_id: 세션 ID
        """
        removed = accumulated_tokens_cache.pop(session_id, None)
        if removed is not None:
            logger.info(f"세션 {session_id} 메모리 정리 완료 - 누적 토큰: {removed}")
        else:
            logger.warning(f"세션 {session_id} 메모리에 데이터 없음")
    
    @staticmethod
    def clear_all_sessions():
        """
        모든 세션 메모리 정리 (관리자 도구용)
        """
        size = len(accumulated_tokens_cache)
        accumulated_tokens_cache.clear()
        logger.info(f"모든 세션 메모리 정리 완료 - {size} 개 세션")
    
    @staticmethod
    def get_active_session_count() -> int:
        """
        현재 메모리에 있는 세션 수 확인 (디버깅용)
        
        Returns:
            활성 세션 수
        """
        return len(accumulated_tokens_cache)
