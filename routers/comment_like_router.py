"""
Comment & Like Router
좋아요 토글 + 댓글 CRUD (AJAX 호출용 → JSON 응답)
"""
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db

from models import Board, BoardLike, Comment, Member
from auth import get_current_user_optional
from utils import Util
from exceptions import (
    NotFoundException,
    ForbiddenException,
    UnauthorizedException,
    ValidationException
)

# Jinja2 템플릿
from core.templates import templates

# loginMember Session에 저장
from core.dependencies import login_required, admin_required


router = APIRouter(prefix="/api/board", tags=["좋아요/댓글-API"])


# ============================================
# Pydantic 요청/응답 모델
# ============================================

class CommentCreateRequest(BaseModel):
    """댓글 작성 요청"""
    comment_content: str
    parents_comment_no: Optional[int] = None  # 대댓글일 때만
    secret_yn: str = "N"                      # 비밀댓글 여부


class CommentUpdateRequest(BaseModel):
    """댓글 수정 요청"""
    comment_content: str


# ============================================
# 좋아요 토글 API
# ============================================

@router.post("/ajax/{board_no}/like")
async def toggle_like(
    board_no: int,
    #current_user = Depends(get_current_user_optional),# JWT
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """
    좋아요 토글 (AJAX)
    - 좋아요 없음 → 추가
    - 좋아요 있음 → 제거
    
    Response JSON:
        { "is_liked": bool, "like_count": int }
    """
    
    # 로그인 체크
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"code": "AUTH_001", "message": "로그인이 필요합니다."}
        )
    
    # 게시글 존재 체크
    board = db.query(Board).filter(
        Board.board_no == board_no,
        Board.board_del_fl == 'N'
    ).first()
    
    if not board:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"code": "DATA_001", "message": "게시글을 찾을 수 없습니다."}
        )
    
    #member_no = current_user['memberNo']
    member_no = current_user['member_no']    
    
    # 기존 좋아요 조회
    existing_like = db.query(BoardLike).filter(
        BoardLike.board_no == board_no,
        BoardLike.member_no == member_no
    ).first()
    
    if existing_like:
        # 좋아요 제거
        db.delete(existing_like)
        db.commit()
        is_liked = False
    else:
        # 좋아요 추가
        new_like = BoardLike(
            board_no=board_no,
            member_no=member_no
        )
        db.add(new_like)
        db.commit()
        is_liked = True
    
    # 현재 좋아요 수 조회
    like_count = db.query(func.count(BoardLike.member_no)).filter(
        BoardLike.board_no == board_no
    ).scalar() or 0
    
    return JSONResponse(content={
        "is_liked": is_liked,
        "like_count": like_count
    })


# ============================================
# 댓글 목록 조회 API
# ============================================

@router.get("/ajax/{board_no}/comments")
async def get_comments(
    board_no: int,
    #current_user = Depends(get_current_user_optional), # JWT
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """
    댓글 목록 조회 (AJAX)
    - 루트 댓글 + 대댓글 재귀 구조
    - 비밀댓글: 작성자/게시글작성자만 내용 표시
    
    Response JSON:
        { "comments": [...], "total": int }
    """
    
    # 게시글 존재 체크
    board = db.query(Board).filter(
        Board.board_no == board_no,
        Board.board_del_fl == 'N'
    ).first()
    
    if not board:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"code": "DATA_001", "message": "게시글을 찾을 수 없습니다."}
        )
    
    # 루트 댓글 조회 (parents_comment_no IS NULL)
    root_comments = db.query(Comment).options(
        joinedload(Comment.author)
    ).filter(
        Comment.board_no == board_no,
        Comment.parents_comment_no == None
    ).order_by(Comment.c_create_date.asc()).all()
    
    #current_member_no = current_user['memberNo'] if current_user else None
    current_member_no = current_user['member_no'] if current_user else None
    board_author_no = board.member_no
    
    # 재귀적으로 댓글 구성
    def build_comment_tree(parent_comment_no):
        """부모 댓글의 자식 댓글 재귀 조회"""
        children = db.query(Comment).options(
            joinedload(Comment.author)
        ).filter(
            Comment.board_no == board_no,
            Comment.parents_comment_no == parent_comment_no
        ).order_by(Comment.c_create_date.asc()).all()
        
        return [serialize_comment(c) for c in children]
    
    def serialize_comment(comment: Comment) -> dict:
        """댓글 객체를 JSON 직렬화"""
        
        # 비밀댓글 처리
        is_secret = comment.secret_yn == 'Y'
        can_view = (
            not is_secret or                            # 비밀댓글 아님
            current_member_no == comment.member_no or   # 댓글 작성자
            current_member_no == board_author_no        # 게시글 작성자
        )
        
        # 삭제된 댓글 처리
        if comment.comment_del_fl == 'Y':
            return {
                "comment_no": comment.comment_no,
                "comment_content": "삭제된 댓글입니다.",
                "author_nickname": "",
                "author_profile": None,
                "c_create_date": comment.c_create_date.strftime("%Y.%m.%d %H:%M"),
                "is_secret": False,
                "is_deleted": True,
                "is_mine": False,
                "modify_yn": "N",
                "parents_comment_no": comment.parents_comment_no,
                "replies": build_comment_tree(comment.comment_no)
            }
        
        return {
            "comment_no": comment.comment_no,
            "comment_content": comment.comment_content if can_view else "비밀댓글입니다.",
            "author_nickname": comment.author.member_nickname if can_view else "비밀",
            "author_profile": f"/uploads{comment.author.profile_img}" if (can_view and comment.author.profile_img) else None,
            "c_create_date": comment.c_create_date.strftime("%Y.%m.%d %H:%M"),
            "is_secret": is_secret,
            "is_deleted": False,
            "is_mine": current_member_no == comment.member_no,
            "modify_yn": comment.modify_yn,
            "parents_comment_no": comment.parents_comment_no,
            "replies": build_comment_tree(comment.comment_no)
        }
    
    # 루트 댓글 직렬화
    comments_data = [serialize_comment(c) for c in root_comments]
    
    # 전체 댓글 수 (삭제 제외)
    total = db.query(func.count(Comment.comment_no)).filter(
        Comment.board_no == board_no,
        Comment.comment_del_fl == 'N'
    ).scalar() or 0
    
    return JSONResponse(content={
        "comments": comments_data,
        "total": total
    })


# ============================================
# 댓글 작성 API
# ============================================

@router.post("/ajax/{board_no}/comments")
async def create_comment(
    board_no: int,
    request: Request,
    #current_user = Depends(get_current_user_optional), # JWT
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """
    댓글 작성 (AJAX)
    - XSS 방지 처리
    - 대댓글 지원 (parents_comment_no)
    - 비밀댓글 지원 (secret_yn)
    """
    
    # 로그인 체크
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"code": "AUTH_001", "message": "로그인이 필요합니다."}
        )
    
    # 요청 본문 파싱
    body = await request.json()
    comment_content = body.get("comment_content", "").strip()
    parents_comment_no = body.get("parents_comment_no", None)
    secret_yn = body.get("secret_yn", "N")
    
    # 내용 검증
    if not comment_content:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"code": "DATA_003", "message": "댓글 내용을 입력해주세요."}
        )
    
    if len(comment_content) > 2000:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"code": "DATA_003", "message": "댓글은 2000자 이내로 작성해주세요."}
        )
    
    # 게시글 존재 체크
    board = db.query(Board).filter(
        Board.board_no == board_no,
        Board.board_del_fl == 'N'
    ).first()
    
    if not board:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"code": "DATA_001", "message": "게시글을 찾을 수 없습니다."}
        )
    
    # 대댓글인 경우 부모 댓글 존재 체크
    if parents_comment_no:
        parent = db.query(Comment).filter(
            Comment.comment_no == parents_comment_no,
            Comment.board_no == board_no
        ).first()
        if not parent:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"code": "DATA_001", "message": "부모 댓글을 찾을 수 없습니다."}
            )
    
    # XSS 방지
    comment_content = Util.xss_handling(comment_content)
    
    # 댓글 생성
    new_comment = Comment(
        comment_content=comment_content,
        #member_no=current_user['memberNo'],
        member_no=current_user['member_no'],
        board_no=board_no,
        parents_comment_no=parents_comment_no,
        secret_yn=secret_yn
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    # 생성된 댓글 정보 반환
    #author = db.query(Member).filter(Member.member_no == current_user['memberNo']).first()
    author = db.query(Member).filter(Member.member_no == current_user['member_no']).first()
        
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "comment_no": new_comment.comment_no,
            "comment_content": new_comment.comment_content,
            "author_nickname": author.member_nickname,
            "author_profile": f"/uploads{author.profile_img}" if author.profile_img else None,
            "c_create_date": new_comment.c_create_date.strftime("%Y.%m.%d %H:%M"),
            "is_secret": secret_yn == 'Y',
            "is_mine": True,
            "modify_yn": "N",
            "parents_comment_no": parents_comment_no,
            "replies": []
        }
    )


# ============================================
# 댓글 수정 API
# ============================================

@router.put("/ajax/comments/{comment_no}")
async def update_comment(
    comment_no: int,
    request: Request,
    #current_user = Depends(get_current_user_optional), # JWT
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """댓글 수정 (AJAX) - 작성자만 가능"""
    
    # 로그인 체크
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"code": "AUTH_001", "message": "로그인이 필요합니다."}
        )
    
    # 요청 본문
    body = await request.json()
    comment_content = body.get("comment_content", "").strip()
    
    if not comment_content:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"code": "DATA_003", "message": "댓글 내용을 입력해주세요."}
        )
    
    # 댓글 조회
    comment = db.query(Comment).filter(
        Comment.comment_no == comment_no,
        Comment.comment_del_fl == 'N'
    ).first()
    
    if not comment:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"code": "DATA_001", "message": "댓글을 찾을 수 없습니다."}
        )
    
    # 작성자 체크
    #if comment.member_no != current_user['memberNo']:
    if comment.member_no != current_user['member_no']:    
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"code": "AUTH_002", "message": "댓글을 수정할 권한이 없습니다."}
        )
    
    # XSS 방지 + 수정
    comment.comment_content = Util.xss_handling(comment_content)
    comment.modify_yn = 'Y'
    db.commit()
    
    return JSONResponse(content={
        "comment_no": comment.comment_no,
        "comment_content": comment.comment_content,
        "modify_yn": "Y"
    })


# ============================================
# 댓글 삭제 API
# ============================================

@router.delete("/ajax/comments/{comment_no}")
async def delete_comment(
    comment_no: int,
    #current_user = Depends(get_current_user_optional), # JWT
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """
    댓글 삭제 (소프트 삭제)
    - 대댓글이 있으면 소프트 삭제 (COMMENT_DEL_FL = 'Y')
    - 대댓글이 없으면 실제 삭제
    """
    
    # 로그인 체크
    if not current_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"code": "AUTH_001", "message": "로그인이 필요합니다."}
        )
    
    # 댓글 조회
    comment = db.query(Comment).filter(
        Comment.comment_no == comment_no,
        Comment.comment_del_fl == 'N'
    ).first()
    
    if not comment:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"code": "DATA_001", "message": "댓글을 찾을 수 없습니다."}
        )
    
    # 작성자 체크
    #if comment.member_no != current_user['memberNo']:
    if comment.member_no != current_user['member_no']:    
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"code": "AUTH_002", "message": "댓글을 삭제할 권한이 없습니다."}
        )
    
    # 대댓글 존재 여부 체크
    has_replies = db.query(Comment).filter(
        Comment.parents_comment_no == comment_no,
        Comment.comment_del_fl == 'N'
    ).first()
    
    if has_replies:
        # 대댓글 있음 → 소프트 삭제
        comment.comment_del_fl = 'Y'
        db.commit()
    else:
        # 대댓글 없음 → 실제 삭제
        db.delete(comment)
        db.commit()
    
    return JSONResponse(content={
        "message": "댓글이 삭제되었습니다.",
        "comment_no": comment_no
    })
