"""
챗봇 기능 Pydantic 스키마

스키마:
- CbSessionCreate: 세션 시작 요청
- CbSessionResponse: 세션 응답
- CbTokenUsageCreate: 토큰 사용 기록 요청
- CbTokenUsageResponse: 토큰 사용 응답
- ChatMessageRequest: 챗봇 메시지 요청
- ChatMessageResponse: 챗봇 메시지 응답
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


# ============================================
# CbSession 관련 스키마
# ============================================

class CbSessionCreate(BaseModel):
    """챗봇 세션 시작 요청"""
    cb_session_type: str = Field(..., description="챗봇 유형 (BASIC, KONG)")
    cb_board_type: str = Field(..., description="게시글 유형 (INSERT, UPDATE)")
    board_no: Optional[int] = Field(None, description="게시글 번호 (수정 시만)")
    
    @validator('cb_session_type')
    def validate_session_type(cls, v):
        if v not in ['BASIC', 'KONG']:
            raise ValueError('cb_session_type은 BASIC 또는 KONG이어야 합니다')
        return v.upper()
    
    @validator('cb_board_type')
    def validate_board_type(cls, v):
        if v not in ['INSERT', 'UPDATE']:
            raise ValueError('cb_board_type은 INSERT 또는 UPDATE이어야 합니다')
        return v.upper()


class CbSessionResponse(BaseModel):
    """챗봇 세션 응답"""
    cb_session_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    cb_session_type: str
    cb_board_type: str
    member_no: int
    board_no: Optional[int] = None
    
    class Config:
        from_attributes = True  # Pydantic v2 (orm_mode 대체)


class CbSessionEnd(BaseModel):
    """챗봇 세션 종료 요청"""
    cb_session_id: int


# ============================================
# CbTokenUsage 관련 스키마
# ============================================

class CbTokenUsageCreate(BaseModel):
    """토큰 사용 기록 요청"""
    prompt_text: str = Field(..., description="사용자 질문")
    answer_text: str = Field(..., description="챗봇 답변")
    prompt_tokens: int = Field(..., ge=0, description="질문 토큰 수")
    answer_tokens: int = Field(..., ge=0, description="답변 토큰 수")
    total_tokens: int = Field(..., ge=0, description="총 토큰 수")
    bean_swe: Optional[int] = Field(None, ge=0, description="차감 커피콩")
    model_name: str = Field(default="gpt-4o-mini", description="모델명")
    cb_session_id: int = Field(..., description="세션 ID")


class CbTokenUsageResponse(BaseModel):
    """토큰 사용 응답"""
    tk_usage_id: int
    prompt_tokens: int
    answer_tokens: int
    total_tokens: int
    bean_swe: Optional[int] = None
    model_name: str
    member_no: int
    cb_session_id: int
    
    class Config:
        from_attributes = True


# ============================================
# 챗봇 메시지 관련 스키마
# ============================================
class ChatMessageRequest(BaseModel):
    """챗봇 메시지 요청 (단순 텍스트)"""
    message: str = Field(..., min_length=1, max_length=4000, description="사용자 질문")
    
    @validator('message')
    def validate_message(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('메시지가 비어있습니다')
        return v


class UsageMetadata(BaseModel):
    """토큰 사용량 메타데이터"""
    prompt_tokens: int = Field(..., description="질문 토큰 수")
    completion_tokens: int = Field(..., description="답변 토큰 수", alias="answer_tokens")
    total_tokens: int = Field(..., description="총 토큰 수")
    accumulated_tokens: int = Field(..., description="세션 누적 토큰 수")
    accumulated_used_beans: int = Field(..., description="누적 사용 커피콩")
    
    class Config:
        allow_population_by_field_name = True  # alias 사용 시 필요


class ChatMessageResponse(BaseModel):
    """챗봇 메시지 응답"""
    reply: str = Field(..., description="챗봇 답변")
    usage: Optional[UsageMetadata] = Field(None, description="토큰 사용량 정보")
    error: Optional[str] = Field(None, description="에러 메시지")


# ============================================
# 커피콩 업데이트 관련 스키마
# ============================================

class BeansUpdateRequest(BaseModel):
    """커피콩 잔액 업데이트 요청"""
    login_member_no: int = Field(..., description="로그인 회원 번호", alias="loginMemberNo")
    updated_beans_amount: int = Field(..., ge=0, description="업데이트할 커피콩 잔액", alias="updatedBeansAmount")
    
    class Config:
        allow_population_by_field_name = True


class BeansUpdateResponse(BaseModel):
    """커피콩 잔액 업데이트 응답"""
    success: bool
    message: str
    updated_beans_amount: Optional[int] = None
    before_amount: Optional[int] = None
    after_amount: Optional[int] = None


# ============================================
# 토큰 사용량 조회 관련 스키마
# ============================================

class TokenUsageSummaryResponse(BaseModel):
    """회원의 토큰 사용량 요약 응답"""
    total_tokens: int = Field(..., description="총 사용 토큰 수")
    total_beans: int = Field(..., description="총 사용 커피콩")
    remaining_beans: int = Field(..., description="남은 커피콩")


# ============================================
# 세션 시작/종료 응답 스키마
# ============================================

class SessionStartResponse(BaseModel):
    """세션 시작 응답"""
    success: bool
    session_id: int = Field(..., description="생성된 세션 ID", alias="sessionId")   # Pydantic validation error로 sqlalchemy.engine.Engine ROLLBACK 발생이슈가능
                                                                                    # front에서는 sessionId로 값처리하려고 하므로 alias 있어야함
    #session_id: int = Field(..., description="생성된 세션 ID")
    message: str
    
    class Config:
        allow_population_by_field_name = True


class SessionEndResponse(BaseModel):
    """세션 종료 응답"""
    success: bool
    message: str
