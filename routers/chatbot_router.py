"""
챗봇 라우터 - FastAPI 엔드포인트

엔드포인트:
- GET /api/chatbot/freeboard/popupBasicChatbot - 무료형 팝업
- GET /api/chatbot/freeboard/popupKongChatbot - 유료형 팝업
- POST /api/chatbot/session/start - 세션 시작
- POST /api/chatbot/session/end/{session_id} - 세션 종료
- POST /api/chatbot/freeboard/{session_id} - 메시지 처리
- POST /api/chatbot/freeboard/updateBeansAmount - 커피콩 업데이트
- GET /api/chatbot/freeboard/usage - 토큰 사용량 조회
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from models import Member
from models import CbSession, CbTokenUsage

from chatbot_schemas import (
    CbSessionCreate,
    SessionStartResponse,
    SessionEndResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    BeansUpdateRequest,
    BeansUpdateResponse,
    TokenUsageSummaryResponse
)
from chatbot_service import ChatbotService

# Jinja2 템플릿
#from core.templates import templates # chatbot은 jinja2를 쓰지않고 FileResponse를 사용한 CSR 정적 렌더링을한다


# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])


# ============================================
# 팝업 화면 제공
# ============================================

@router.get("/freeboard/popupBasicChatbot")
async def popup_basic_chatbot():
    """
    무료형 챗봇 팝업 화면 제공
    """
    return FileResponse("static/fbChatbotRevBasic.html")


@router.get("/freeboard/popupKongChatbot")
async def popup_kong_chatbot():
    """
    유료형 챗봇 팝업 화면 제공
    """
    return FileResponse("static/fbChatbotRevKong.html")


# ============================================
# 세션 관리
# ============================================
# [중요] 여기서  body: CbSessionCreate 이므로 JS에서 전달되는 body 데이터는 CbSessionCreate 객체형식이어야함, 안그러면 세션 시작도 못하고 실패됨 ()
# ==> INFO: 172.19.0.1:57526 - "POST /api/chatbot/session/start HTTP/1.1" 422 Unprocessable Entity발생
@router.post("/session/start", response_model=SessionStartResponse)
async def start_session(
    body: CbSessionCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    챗봇 세션 시작 (팝업 열 때)
    
    Args:
        request: {cbSessionType, cbBoardType, boardNo}
        current_user: 로그인한 회원 (Optional)
        db: 데이터베이스 세션
        
    Returns:
        SessionStartResponse: {success, sessionId, message}
    """
    #print("########## /api/chatbot/session/start started...")
    current_user = req.session.get("user") # dict, 자식창(챗봇창)의 경우 부모창의 Session을 공유하므로 거기서 loginMember 세션정보읽어와야함
    #print("########## current_user, session :", current_user)
    
    # 로그인 체크
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    try:
        logger.info(f"챗봇 세션 시작 요청 - 회원: {current_user['member_no']}, 유형: {body.cb_session_type}, 게시글유형: {body.cb_board_type}, 게시글번호: {body.board_no}")
        
        # 세션 생성
        # 1) Sequence 직접 호출
        result = db.execute(text("SELECT SEQ_CB_SESSION_NO.NEXTVAL FROM dual"))
        new_id = result.scalar()  # 실제 시퀀스 값 (int)

        # 2) CbSession 객체 생성 시 ID 할당
        cb_session = CbSession(
            cb_session_id=new_id,
            cb_session_type=body.cb_session_type,
            cb_board_type=body.cb_board_type,
            member_no=current_user["member_no"],
            board_no=body.board_no
        )

        db.add(cb_session)
        db.commit()
        db.refresh(cb_session)  # 혹은 필요시
                
        #print("########## created  DB 삽입후, cb_session.cb_session_id =", cb_session.cb_session_id)   
        cb_session.cb_session_id = cb_session.cb_session_id or new_id #  db.refresh(cb_session)후에도 cb_session_id가 None이면 수동으로 할당
        
        logger.info(f"챗봇 세션 생성 완료 - 세션ID: {cb_session.cb_session_id}, 회원번호: {current_user['member_no']}, 유형: {body.cb_session_type}")
        
        return SessionStartResponse(
            success=True,
            #session_id=cb_session.cb_session_id, # session_id, snake_case
            sessionId=cb_session.cb_session_id, # front JS에서 sessionId로 변수처리하므로, camelCase로
            message="챗봇 세션이 시작되었습니다."
        )
        
    except Exception as e:
        logger.error(f"챗봇 세션 시작 실패: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="세션 시작 중 오류가 발생했습니다."
        )


@router.post("/session/end/{session_id}", response_model=SessionEndResponse)
async def end_session(
    session_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    챗봇 세션 종료 (팝업 닫을 때)
    
    Args:
        session_id: 세션 ID
        current_user: 로그인한 회원 (Optional)
        db: 데이터베이스 세션
        
    Returns:
        SessionEndResponse: {success, message}
    """
    current_user = req.session.get("user") # dict, 자식창(챗봇창)의 경우 부모창의 Session을 공유하므로 거기서 loginMember 세션정보읽어와야함
        
    # 로그인 체크
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    try:
        logger.info(f"챗봇 세션 종료 요청 - 세션ID: {session_id}, 회원: {current_user['member_no']}")
        
        # 세션 조회
        cb_session = db.query(CbSession).filter(
            CbSession.cb_session_id == session_id
        ).first()
        
        if not cb_session:
            logger.warning(f"세션 {session_id}을 찾을 수 없음")
            return SessionEndResponse(
                success=False,
                message="세션을 찾을 수 없습니다."
            )
        
        # 종료 시간 업데이트
        from sqlalchemy.sql import func
        cb_session.ended_at = func.sysdate()
        db.commit()
        
        # 메모리에서 누적 토큰 정리
        ChatbotService.clear_session(session_id)
        
        logger.info(f"챗봇 세션 종료 완료 - 세션ID: {session_id}")
        
        return SessionEndResponse(
            success=True,
            message="챗봇 세션이 종료되었습니다."
        )
        
    except Exception as e:
        logger.error(f"챗봇 세션 종료 실패: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="세션 종료 중 오류가 발생했습니다."
        )


# ============================================
# 메시지 처리
# ============================================

@router.post("/freeboard/{session_id}", response_model=ChatMessageResponse)
async def chat(
    session_id: int,
    request: Request,  # body를 text/plain으로 받기 위함
    db: Session = Depends(get_db)
):
    """
    챗봇 메시지 처리 (OpenAI API 호출)
    
    Args:
        session_id: 세션 ID
        request: Request (body는 text/plain)
        current_user: 로그인한 회원 (Optional)
        db: 데이터베이스 세션
        
    Returns:
        ChatMessageResponse: {reply, usage}
    """
    current_user = request.session.get("user") # dict, 자식창(챗봇창)의 경우 부모창의 Session을 공유하므로 거기서 loginMember 세션정보읽어와야함
        
    # body를 text로 읽기
    user_message = (await request.body()).decode('utf-8').strip()
    
    if not user_message:
        raise HTTPException(status_code=400, detail="메시지가 비어있습니다.")
    
    logger.info(f"챗봇 요청 - 세션ID: {session_id}, 회원번호: {current_user['member_no'] if current_user else '비회원'}, 메시지: {user_message}")
    
    try:
        # 세션 검증
        cb_session = db.query(CbSession).filter(
            CbSession.cb_session_id == session_id
        ).first()
        
        if not cb_session:
            raise HTTPException(status_code=400, detail="유효하지 않은 세션입니다.")
        
        logger.info(f"현 챗봇 세션 정보: {cb_session}")
        
        cb_session_type = cb_session.cb_session_type
        
        # 커피콩 챗봇인 경우 로그인 체크
        if cb_session_type == "KONG" and not current_user:
            raise HTTPException(status_code=401, detail="커피콩 챗봇은 로그인이 필요합니다.")
        
        # KONG 타입: 커피콩 잔액 체크
        if cb_session_type == "KONG" and current_user:
            if current_user['beans_amount'] <= 0:
                raise HTTPException(status_code=402, detail="커피콩이 부족합니다.")
        
        # OpenAI API 호출
        result = await ChatbotService.send_message(
            session_id,
            cb_session_type,
            user_message,
            # current_user.member_no,
            current_user['member_no'],
            db
        )
        
        return ChatMessageResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"챗봇 처리 중 오류 발생: {e}", exc_info=True)
        return ChatMessageResponse(
            reply="죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            error=str(e)
        )


# ============================================
# 토큰 사용량 조회
# ============================================

@router.get("/freeboard/usage", response_model=TokenUsageSummaryResponse)
async def get_usage(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    회원의 토큰 사용량 조회
    
    Args:
        current_user: 로그인한 회원
        db: 데이터베이스 세션
        
    Returns:
        TokenUsageSummaryResponse: {totalTokens, totalBeans, remainingBeans}
    """
    current_user = request.session.get("user") # dict, 자식창(챗봇창)의 경우 부모창의 Session을 공유하므로 거기서 loginMember 세션정보읽어와야함
    
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    try:
        result = ChatbotService.get_usage_by_member(current_user['member_no'], db)
        return TokenUsageSummaryResponse(**result)
        
    except Exception as e:
        logger.error(f"토큰 사용량 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="토큰 사용량 조회 중 오류가 발생했습니다."
        )


# ============================================
# 커피콩 업데이트
# ============================================

@router.post("/freeboard/updateBeansAmount", response_model=BeansUpdateResponse)
async def update_beans_amount(
    request: BeansUpdateRequest, # 사실 이거는 Request.body 임 => body: BeansUpdateRequest 로 쓰는것이 더 정확
    req: Request,
    db: Session = Depends(get_db)
):
    """
    챗봇 사용 후 회원의 커피콩 잔액 업데이트
    
    Args:
        request: {loginMemberNo, updatedBeansAmount}
        current_user: 로그인한 회원 (Optional)
        db: 데이터베이스 세션
        
    Returns:
        BeansUpdateResponse: {success, message, updatedBeansAmount, beforeAmount, afterAmount}
    """
    current_user = req.session.get("user") # dict, 자식창(챗봇창)의 경우 부모창의 Session을 공유하므로 거기서 loginMember 세션정보읽어와야함
    # print("########## current_user, session :", current_user)    
    
    logger.info("=== updateBeansAmount 호출됨 ===")
    logger.info(f"요청 데이터: {request}") # 사실 이거는 Request.body 임
    logger.info(f"로그인 회원: {current_user}")
    
    try:
        member_no = request.login_member_no
        updated_beans_amount = request.updated_beans_amount
        
        # 로그인한 회원과 요청한 회원이 일치하는지 확인
        if current_user and current_user['member_no'] != member_no:
            logger.warning(f"권한 불일치 - 로그인: {current_user['member_no']}, 요청: {member_no}")
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        # 음수 체크
        if updated_beans_amount < 0:
            logger.warning(f"음수 잔액 시도: {updated_beans_amount}")
            raise HTTPException(status_code=400, detail="잔액이 음수일 수 없습니다.")
        
        # Member 조회
        member = db.query(Member).filter(Member.member_no == member_no).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
        
        logger.info(f"업데이트 전 - 회원 {member_no} 커피콩: {member.beans_amount}")
        
        before_amount = member.beans_amount
        
        # 커피콩 업데이트
        member.beans_amount = updated_beans_amount
        db.commit()
        db.refresh(member)
        
        logger.info(f" 업데이트 후 - 회원 {member_no} 커피콩: {before_amount} → {member.beans_amount}")
        
        return BeansUpdateResponse(
            success=True,
            message="커피콩 잔액이 업데이트되었습니다.",
            updated_beans_amount=updated_beans_amount,
            before_amount=before_amount,
            after_amount=member.beans_amount
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"커피콩 잔액 업데이트 실패: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"커피콩 잔액 업데이트 중 오류가 발생했습니다: {str(e)}"
        )
