"""
Board Write Router - 게시글 작성/수정/삭제
"""
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from auth import get_current_user_optional
from board_service import BoardService
from exceptions import FileUploadException, NotFoundException, ForbiddenException

import logging
logger = logging.getLogger(__name__)

# Jinja2 템플릿
from core.templates import templates

# loginMember Session에 저장
from core.dependencies import login_required, admin_required

bcu_router = APIRouter(prefix="/board2", tags=["게시판-작성/수정"])

# ============================================
# 게시글 작성 페이지
# ============================================

@bcu_router.get("/write", response_class=HTMLResponse, name="board_write_page")
async def board_write_page(
    request: Request,
    current_user = Depends(login_required) # Session
):
    """게시글 작성 페이지"""
    
    # 로그인 체크
    if not current_user:
        #print("############ 로그인해주세요.....#########")
        return RedirectResponse(url="/member/login", status_code=303)
    
    return templates.TemplateResponse("board/freeboardWrite.html", {
        "request": request,
        "current_user": current_user
    })


# ============================================
# 게시글 작성 처리
# ============================================

@bcu_router.post("/write", name="board_write_submit")
async def board_write_submit(
    request: Request,
    board_title: str = Form(..., description="게시글 제목"),
    board_content: str = Form(..., description="게시글 내용"),
    images: List[UploadFile] = File(None, description="이미지 파일 (최대 5개)"),
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """
    게시글 작성 처리
    
    - XSS 방지 처리
    - 이미지 업로드 (최대 5개)
    - DB 저장
    """
    
    # 로그인 체크
    if not current_user:
        return RedirectResponse(url="/member/login", status_code=303)
    
    try:
        # BoardService 사용
        board_service = BoardService(db)
        
        # 이미지 필터링 (빈 파일 제외)
        valid_images = []
        if images:
            for img in images:
                if img.filename:  # 파일명이 있는 경우만
                    valid_images.append(img)
        
        # 게시글 생성
        new_board = board_service.create_board( # board_service.py
            board_title=board_title,
            board_content=board_content,
            # member_no=current_user['memberNo'],
            member_no=current_user['member_no'],
            board_code=3,  # 자유게시판
            images=valid_images if valid_images else None
        )
        
        # 상세 페이지로 리다이렉트
        return RedirectResponse(
            url=f"/board/{new_board.board_no}",
            status_code=303
        )
        
    except FileUploadException as e:
        # 파일 업로드 에러 → 에러 메시지와 함께 작성 페이지로
        return templates.TemplateResponse("board/freeboardWrite.html", {
            "request": request,
            "current_user": current_user,
            "error_message": str(e),
            "board_title": board_title,
            "board_content": board_content
        })
    
    except Exception as e:
        # 일반 에러
        return templates.TemplateResponse("board/freeboardWrite.html", {
            "request": request,
            "current_user": current_user,
            "error_message": "게시글 작성 중 오류가 발생했습니다.",
            "board_title": board_title,
            "board_content": board_content
        })


# ============================================
# 게시글 수정 페이지
# ============================================

@bcu_router.get("/update/{board_no}", response_class=HTMLResponse, name="board_update_page")
async def board_update_page(
    request: Request,
    board_no: int,
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """게시글 수정 페이지"""
    
    # 로그인 체크 (더블체크)
    if not current_user:
        return RedirectResponse(url="/member/login", status_code=303)
    
    from models import Board, BoardImg
    from sqlalchemy.orm import joinedload
    
    # 게시글 조회
    board = db.query(Board).options(
        joinedload(Board.author),
        joinedload(Board.images)
    ).filter(
        Board.board_no == board_no,
        Board.board_del_fl == 'N'
    ).first()
    
    if not board:
        # 게시글 없음 → 목록으로
        return RedirectResponse(url="/board/list", status_code=303)
    
    # 작성자 확인
    if board.member_no != current_user['member_no']:
        # 권한 없음 → 상세 페이지로
        return RedirectResponse(url=f"/board/{board_no}", status_code=303)
    
    # 이미지 목록
    images = sorted(board.images, key=lambda x: x.img_order)
    image_list = [
        {
            'img_no': img.img_no,
            'img_path': f"/uploads{img.img_path}",
            'img_orig': img.img_orig,
            'img_rename': img.img_rename,
            'img_order': img.img_order
        }
        for img in images
    ]
    
    # error 메시지
    # error_msg = "placeholder"
    error_msg = ""
    
    return templates.TemplateResponse("board/freeboardUpdate.html", {
        "request": request,
        "current_user": current_user,
        "board": board,
        "images": image_list
        ,"error_message": error_msg
    })


# ============================================
# 게시글 수정 처리
# ============================================
@bcu_router.post("/update/{board_no}", name="board_update_submit")
async def board_update_submit(
    request: Request,
    board_no: int,
    board_title: str = Form(...),
    board_content: str = Form(...),
    delete_images: Optional[str] = Form(None, description="삭제할 이미지 순서 (쉼표 구분)"),
    images: List[UploadFile] = File(None),
    current_user = Depends(login_required), # Session
    db: Session = Depends(get_db)
):
    """게시글 수정 처리"""
    
    # 로그인 체크
    if not current_user:
        return RedirectResponse(url="/member/login", status_code=303)
    
    try:
        
        # BoardService 사용
        board_service = BoardService(db)
        
        # 삭제할 이미지 순서 파싱
        delete_image_orders = []
        if delete_images:
            try:
                delete_image_orders = [int(order) for order in delete_images.split(',') if order.strip()]
            except ValueError:
                logger.warning(f"잘못된 delete_images 형식: {delete_images}")        
                
        logger.info(f"삭제할 이미지 순서: {delete_image_orders}")
        
        # 유효한 이미지만 필터링
        valid_images = []
        if images:
            for img in images:
                if img.filename:
                    valid_images.append(img)
                    
                    
                    
        
        # 게시글 수정 (img_order 업데이트 필요)
        updated_board = board_service.update_board(
            board_no=board_no,
            board_title=board_title,
            board_content=board_content,
            member_no=current_user['member_no'],
            delete_image_orders=delete_image_orders if delete_image_orders else None,
            new_images=valid_images if valid_images else None
        )
        
        # 상세 페이지로 리다이렉트
        return RedirectResponse(
            url=f"/board/{board_no}",
            status_code=303
        )
        
    except (NotFoundException, ForbiddenException) as e:
        # 게시글 없음 또는 권한 없음
        return RedirectResponse(url="/board/list", status_code=303)
    
    except FileUploadException as e:
        # 파일 업로드 에러
        return RedirectResponse(
            # url=f"/board/update/{board_no}?error={str(e)}", # ==> 현재 이 요청주소 처리 페이지가 없다 (404 에러발생) 
            url=f"/board/update/{board_no}", 
            status_code=303
        )


# ============================================
# 게시글 삭제
# ============================================
@bcu_router.post("/delete/{board_no}",  name="board_delete")
async def board_delete(
    board_no: int,
    current_user = Depends(login_required),
    db: Session = Depends(get_db)
):
    from models import Board

    if not current_user:
        return {"success": False, "message": "로그인이 필요합니다."}

    # 삭제 대상 조회
    board = db.query(Board).filter(
        Board.board_no == board_no,
        Board.board_del_fl == 'N'
    ).first()

    if not board:
        return {"success": False, "message": "게시글이 존재하지 않습니다."}

    if board.member_no != current_user["member_no"]:
        return {"success": False, "message": "삭제 권한이 없습니다."}

    # 소프트 삭제
    board.board_del_fl = 'Y'
    db.commit()

    return {
        "success": True,
        "deleted_count": 1
    }
