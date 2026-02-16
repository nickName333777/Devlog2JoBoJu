"""
Board Router - Jinja2 템플릿 렌더링 방식
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse # URL 페이지(동기) 렌더링: 동기 board 목록조회
from fastapi.responses import JSONResponse # AJAX 비동기 board 목록조회
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_
from typing import Optional, List
import math
import os
from pathlib import Path

from database import get_db
from models import Board, BoardImg, BoardLike, Comment, Member

from auth import get_current_user_optional

# Jinja2 템플릿
from core.templates import templates

# loginMember Session에 저장
from core.dependencies import login_required, admin_required

# AJAX 비동기 board 목록조회용 DTO
from board_schemas import BoardImageResponse, BoardAuthorResponse, BoardListItem, BoardListResponse, BoardDetailResponse

router = APIRouter(prefix="/board", tags=["게시판"]) # 게시판 동기 목록 조회(URL 페이지 렌더링, VIEW)

router_ajax = APIRouter(prefix="/api/board", tags=["게시판비동기"]) # 게시판 비동기 목록 조회(AJAX 데이터용, JSON)

# ============================================
# 페이지 라우터 (HTML)
# 게시판 목록 (Jinja2 렌더링: URL 페이지 렌더링, 동기목록 조회, cf: Spring Controller(VIEW) )
# ============================================

@router.get("/list", response_class=HTMLResponse, name="board_list")
async def board_list_page(
    request: Request,
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=7, ge=1, le=50, description="페이지당 개수"),
    keyword: Optional[str] = Query(default=None, description="검색 키워드"),
    search_type: str = Query(default="title", regex="^(title|content|author|all)$"),
    sort_by: str = Query(default="recent", regex="^(recent|views|likes)$"),
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """
    게시판 목록 페이지 (Jinja2 템플릿)
    """
    
    # 기본 쿼리 (자유게시판, 삭제되지 않은 글)
    query = db.query(Board).filter(
        Board.board_code == 3,
        Board.board_del_fl == 'N'
    ).options(joinedload(Board.author))
    
    # 검색 조건
    if keyword:
        if search_type == "title":
            query = query.filter(Board.board_title.like(f"%{keyword}%"))
        elif search_type == "content":
            query = query.filter(Board.board_content.like(f"%{keyword}%"))
        elif search_type == "author":
            query = query.join(Member).filter(Member.member_nickname.like(f"%{keyword}%"))
        elif search_type == "all":
            query = query.join(Member).filter(
                or_(
                    Board.board_title.like(f"%{keyword}%"),
                    Board.board_content.like(f"%{keyword}%"),
                    Member.member_nickname.like(f"%{keyword}%")
                )
            )
    
    # 전체 개수
    total = query.count()
    
    # 정렬
    # func.count(): SQL의 COUNT() 함수를 파이썬에서 쓰게 해주는 SQLAlchemy 도우미 객체 (from sqlalchemy import func ) -> .count(), .sum(), .avg(), .max(), .now()등있음
    if sort_by == "recent":
        query = query.order_by(desc(Board.b_create_date))
    elif sort_by == "views":
        query = query.order_by(desc(Board.board_count))
    elif sort_by == "likes":
        like_count_subquery = db.query(
            BoardLike.board_no,
            func.count(BoardLike.member_no).label('like_count')
        ).group_by(BoardLike.board_no).subquery()
        
        query = query.outerjoin(
            like_count_subquery,
            Board.board_no == like_count_subquery.c.board_no
        ).order_by(desc(like_count_subquery.c.like_count))
    
    # 페이징
    offset = (page - 1) * limit
    boards = query.offset(offset).limit(limit).all()
    
    # 각 게시글에 통계 정보 추가
    board_list = []
    for board in boards:
        # 썸네일
        thumbnail = None
        first_image = db.query(BoardImg).filter(
            BoardImg.board_no == board.board_no,
            BoardImg.img_order == 0
        ).first()
        if first_image:
            thumbnail = f"/uploads{os.path.join(first_image.img_path, first_image.img_rename)}"
        
        # 좋아요 개수
        like_count = db.query(func.count(BoardLike.member_no)).filter(
            BoardLike.board_no == board.board_no
        ).scalar() or 0
        
        # 댓글 개수
        comment_count = db.query(func.count(Comment.comment_no)).filter(
            Comment.board_no == board.board_no,
            Comment.comment_del_fl == 'N'
        ).scalar() or 0
        
        board_list.append({
            'board': board,
            'thumbnail': thumbnail,
            'like_count': like_count,
            'comment_count': comment_count
        })
    
    # 총 페이지 수
    total_pages = math.ceil(total / limit) if total > 0 else 0 
    
    # 페이지 번호 리스트 (최대 10개)
    start_page = max(1, page - 4)
    end_page = min(total_pages, start_page + 9)
    page_numbers = list(range(start_page, end_page + 1))
    
    # 템플릿 렌더링
    return templates.TemplateResponse("board/freeboardList.html", {
        "request": request,
        "current_user": current_user,
        "board_list": board_list,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
        "keyword": keyword or "",
        "search_type": search_type,
        "sort_by": sort_by
    })

# ============================================
# AJAX 라우터 (JSON)
# 게시판 목록 (비동기 목록 조회,  AJAX 데이터용: /api/board/ajax/list, cf: Spring RestController (JSON) for AJAX 데이터용 )
# ============================================

@router_ajax.get("/ajax/list", response_model=BoardListResponse, name="board_ajax_list") # (FastAPI가 JSONResponse로 처리) 또는 return 에 JSONResponse(content={ })명시
async def board_ajax_list_page(
    page: int = 1,
    limit: int = 7,
    keyword: Optional[str] = None,
    search_type: str = "title",
    sort_by: str = "recent",
    current_user = Depends(login_required),
    db: Session = Depends(get_db)    
):
    """
    게시판 비동기 목록 조회(AJAX 데이터용, JSON)
    """
    
    # 기본 쿼리 (자유게시판, 삭제되지 않은 글)
    query = db.query(Board).filter(
        Board.board_code == 3,
        Board.board_del_fl == 'N'
    ).options(joinedload(Board.author)) # joinedload()는 LEFT OUTER JOIN user ON board.author_id = user.id 개념 (Board + Author를 JOIN으로 한 번에 조회)
    # 만약 joinedload()  안쓰면: Board 조회 → 1번 쿼리, 각 Board마다 author 접근 → N번 쿼리 ==>  N+1 문제 발생
    # options(joinedload(Board.author))으로 N+1 조회하지 않고, 1 번 조회로 끝낸다.
    
    # 검색 조건
    if keyword:
        if search_type == "title":
            query = query.filter(Board.board_title.like(f"%{keyword}%"))
        elif search_type == "content":
            query = query.filter(Board.board_content.like(f"%{keyword}%"))
        elif search_type == "author":
            query = query.join(Member).filter(Member.member_nickname.like(f"%{keyword}%"))
        elif search_type == "all":
            query = query.join(Member).filter(
                or_(
                    Board.board_title.like(f"%{keyword}%"),
                    Board.board_content.like(f"%{keyword}%"),
                    Member.member_nickname.like(f"%{keyword}%")
                )
            )
    
    # 전체 개수
    total = query.count()
    
    # 정렬
    if sort_by == "recent":
        query = query.order_by(desc(Board.b_create_date))
    elif sort_by == "views":
        query = query.order_by(desc(Board.board_count))
    elif sort_by == "likes":
        like_count_subquery = db.query(
            BoardLike.board_no,
            func.count(BoardLike.member_no).label('like_count')
        ).group_by(BoardLike.board_no).subquery()
        
        query = query.outerjoin(
            like_count_subquery,
            Board.board_no == like_count_subquery.c.board_no
        ).order_by(desc(like_count_subquery.c.like_count))
    
    # 페이징
    offset = (page - 1) * limit
    boards = query.offset(offset).limit(limit).all()
    
    # 각 게시글에 통계 정보 추가
    board_list = []
    for board in boards:
        # 썸네일
        thumbnail = None
        first_image = db.query(BoardImg).filter(
            BoardImg.board_no == board.board_no,
            BoardImg.img_order == 0
        ).first()
        if first_image:
            thumbnail = f"/uploads{os.path.join(first_image.img_path, first_image.img_rename)}"
        
        # 좋아요 개수
        like_count = db.query(func.count(BoardLike.member_no)).filter(
            BoardLike.board_no == board.board_no
        ).scalar() or 0
        
        # 댓글 개수
        comment_count = db.query(func.count(Comment.comment_no)).filter(
            Comment.board_no == board.board_no,
            Comment.comment_del_fl == 'N'
        ).scalar() or 0
        
        board_list.append({
            'board': board_to_dict(board), # 
            # 'board': board, # TypeError: Object of type Board is not JSON serializable (Board model entity 직접 프론트전달 불가)
            'thumbnail': thumbnail,
            'like_count': like_count,
            'comment_count': comment_count
        })
    
    # 총 페이지 수
    total_pages = math.ceil(total / limit) if total > 0 else 0
    
    # 페이지 번호 리스트 (최대 10개)
    start_page = max(1, page - 4)
    end_page = min(total_pages, start_page + 9)
    page_numbers = list(range(start_page, end_page + 1))

    # JSON 반환 for AJAX 데이터용: JSON 반환명시, JSONResponse(content={})
    return JSONResponse(content= {
        "boards": board_list,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    })

# Board model entity(이거 직렬화 않됨) -> JSON으로 전달위해 dict으로 (또는 Board model entity 전달용 BoardItemDTO고려 )
def board_to_dict(board: Board):
    return {
        "board_no": board.board_no,
        "board_title": board.board_title,
        "board_content": board.board_content,
        "board_count": board.board_count,
        "b_create_date": board.b_create_date.isoformat(),

        "author": {
            "member_no": board.author.member_no if board.author else None,
            "member_nickname": board.author.member_nickname if board.author else None,
            "profile_img": board.author.profile_img if board.author else None
        }
    }

# ============================================
# 페이지 라우터 (HTML)
# 게시글 상세 (Jinja2 렌더링: URL 페이지 렌더링, cf: Spring Controller(VIEW) )
# ============================================

@router.get("/{board_no}", response_class=HTMLResponse, name="board_detail")
async def board_detail_page(
    request: Request,
    board_no: int,
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """
    게시글 상세 페이지 (Jinja2 템플릿)
    """
    
    # 게시글 조회
    board = db.query(Board).options(
        joinedload(Board.author), # joinedload()는 LEFT OUTER JOIN (Board + Author를 JOIN으로 한 번에 조회)
        joinedload(Board.images)  # joinedload()는 LEFT OUTER JOIN (Board + Images를 JOIN으로 한 번에 조회)
    ).filter(
        Board.board_no == board_no,
        Board.board_del_fl == 'N'
    ).first()
    
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    
    # 조회수 증가
    board.board_count += 1
    db.commit()
    
    # 이미지 목록
    images = sorted(board.images, key=lambda x: x.img_order)
    image_list = [f"/uploads{os.path.join(img.img_path, img.img_rename)}" for img in images]
    
    # 좋아요 개수
    like_count = db.query(func.count(BoardLike.member_no)).filter(
        BoardLike.board_no == board_no
    ).scalar() or 0
    
    # 현재 사용자 좋아요 여부
    is_liked = False
    if current_user:
        is_liked = db.query(BoardLike).filter(
            BoardLike.board_no == board_no,
            BoardLike.member_no == current_user['member_no']
        ).first() is not None
    
    # 댓글 개수
    comment_count = db.query(func.count(Comment.comment_no)).filter(
        Comment.board_no == board_no,
        Comment.comment_del_fl == 'N'
    ).scalar() or 0
    
    # 작성자 여부
    is_author = current_user and current_user['member_no'] == board.member_no
    
    # 템플릿 렌더링
    return templates.TemplateResponse("board/freeboardDetail.html", {
        "request": request,
        "current_user": current_user,
        "board": board,
        "images": image_list, # image_list = [f"/uploads{os.path.join(img.img_path, img.img_rename)}" for img in board.images]
        "like_count": like_count,
        "is_liked": is_liked,
        "comment_count": comment_count,
        "is_author": is_author
    })


# ============================================
# AJAX 라우터 (JSON)
# 게시글 상세 (비동기 게시글 상세 조회,  AJAX 데이터용: /api/board/ajax/detail/{boardNo}, cf: Spring RestController (JSON) for AJAX 데이터용 )
#  ==> 게시글 상세 조회는 사실 AJAX 비동기 조회를 할 이유는 없다. 단지 한번 연습.
# ============================================

@router_ajax.get("/ajax/detail/{board_no}", name="board_ajax_detail") #
async def board_ajax_detail_page(
    board_no: int,
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """
    게시글 상세 페이지 (Jinja2 템플릿)
    """
    
    # 게시글 조회
    board = db.query(Board).options(
        joinedload(Board.author),
        joinedload(Board.images)  
    ).filter(
        Board.board_no == board_no,
        Board.board_del_fl == 'N'
    ).first()
    
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    print(f"################# /api/board/ajax/detail/{board_no} = ", board)
    
    # 조회수 증가
    board.board_count += 1
    db.commit()
    
    # 이미지 목록
    images = sorted(board.images, key=lambda x: x.img_order)
    image_list = [f"/uploads{os.path.join(img.img_path, img.img_rename)}" for img in images]
    
    # 좋아요 개수
    like_count = db.query(func.count(BoardLike.member_no)).filter(
        BoardLike.board_no == board_no
    ).scalar() or 0
    
    # 현재 사용자 좋아요 여부
    is_liked = False
    if current_user:
        is_liked = db.query(BoardLike).filter(
            BoardLike.board_no == board_no,
            BoardLike.member_no == current_user['member_no']
        ).first() is not None
    
    # 댓글 개수
    comment_count = db.query(func.count(Comment.comment_no)).filter(
        Comment.board_no == board_no,
        Comment.comment_del_fl == 'N'
    ).scalar() or 0
    
    # 작성자 여부
    is_author = current_user and current_user['member_no'] == board.member_no
    
    # JSON반환
    return JSONResponse(content= {
        "current_user": current_user,
        "board": board_to_dict(board), 
        "images": image_list, # image_list = [f"/uploads{os.path.join(img.img_path, img.img_rename)}" for img in board.images]
        "like_count": like_count,
        "is_liked": is_liked,
        "comment_count": comment_count,
        "is_author": is_author
    })    
    
