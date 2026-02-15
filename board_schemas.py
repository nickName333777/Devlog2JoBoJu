"""
Pydantic Schemas for Board (자유게시판)
Request/Response 데이터 검증 및 직렬화
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
# from typing import Literal
from datetime import datetime


# ============================================
# BOARD 스키마
# ============================================

class BoardBase(BaseModel):
    """게시글 기본 스키마"""
    board_title: str = Field(..., max_length=300, description="게시글 제목")
    board_content: str = Field(..., description="게시글 내용")
    board_code: int = Field(default=3, description="게시판 코드 (3: 자유게시판)")


class BoardCreate(BoardBase):
    """게시글 작성 요청"""
    pass


class BoardUpdate(BaseModel):
    """게시글 수정 요청"""
    board_title: Optional[str] = Field(None, max_length=300)
    board_content: Optional[str] = None


class BoardImageResponse(BaseModel):
    """게시글 이미지 응답"""
    img_no: int
    img_path: str
    img_orig: Optional[str]
    img_rename: Optional[str]
    img_order: int
    
    class Config:
        from_attributes = True


class BoardAuthorResponse(BaseModel):
    """게시글 작성자 정보"""
    member_no: int
    member_nickname: str
    profile_img: Optional[str]
    member_level_no: int
    
    class Config:
        from_attributes = True


class BoardListItem(BaseModel):
    """게시글 목록 아이템"""
    board_no: int
    board_title: str
    board_count: int
    b_create_date: datetime
    author: BoardAuthorResponse
    thumbnail: Optional[str] = None  # 첫 번째 이미지
    like_count: int = 0
    comment_count: int = 0
    
    class Config:
        from_attributes = True


class BoardDetailResponse(BaseModel):
    """게시글 상세 응답"""
    board_no: int
    board_title: str
    board_content: str
    board_count: int
    b_create_date: datetime
    b_update_date: Optional[datetime]
    author: BoardAuthorResponse
    images: List[BoardImageResponse] = []
    like_count: int = 0
    is_liked: bool = False  # 현재 사용자가 좋아요 눌렀는지
    comment_count: int = 0
    
    class Config:
        from_attributes = True


class BoardListResponse(BaseModel):
    """게시글 목록 페이징 응답"""
    boards: List[BoardListItem]
    total: int
    page: int
    limit: int
    total_pages: int


# ============================================
# COMMENTS 스키마
# ============================================

class CommentBase(BaseModel):
    """댓글 기본 스키마"""
    comment_content: str = Field(..., max_length=2000, description="댓글 내용")
    #secret_yn: str = Field(default='N', regex='^[YN]$', description="비밀댓글 여부") # pydantic v1
    secret_yn: str = Field(default='N', pattern='^[YN]$', description="비밀댓글 여부") # pydantic v2


class CommentCreate(CommentBase):
    """댓글 작성 요청"""
    board_no: int
    parents_comment_no: Optional[int] = None  # 대댓글인 경우


class CommentUpdate(BaseModel):
    """댓글 수정 요청"""
    comment_content: str = Field(..., max_length=2000)


class CommentAuthorResponse(BaseModel):
    """댓글 작성자 정보"""
    member_no: int
    member_nickname: str
    profile_img: Optional[str]
    
    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """댓글 응답"""
    comment_no: int
    comment_content: str
    c_create_date: datetime
    modify_yn: str
    secret_yn: str
    comment_del_fl: str
    author: CommentAuthorResponse
    parents_comment_no: Optional[int]
    replies: List['CommentResponse'] = []  # 대댓글 목록
    
    class Config:
        from_attributes = True


# Forward reference 해결
CommentResponse.model_rebuild()


# ============================================
# LIKE 스키마
# ============================================

class BoardLikeResponse(BaseModel):
    """좋아요 응답"""
    is_liked: bool
    like_count: int


# ============================================
# SEARCH/FILTER 스키마
# ============================================

class BoardSearchParams(BaseModel):
    """게시글 검색 파라미터"""
    keyword: Optional[str] = None
    #search_type: str = Field(default='title', regex='^(title|content|author|all)$') # pydantic v1
    search_type: str = Field(default='title', pattern='^(title|content|author|all)$') # pydantic v2
    #sort_by: str = Field(default='recent', regex='^(recent|views|likes)$')
    sort_by: str = Field(default='recent', pattern='^(recent|views|likes)$')
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)


# ============================================
# 공통 응답 스키마
# ============================================

class MessageResponse(BaseModel):
    """일반 메시지 응답"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """에러 응답"""
    message: str
    success: bool = False
    error_code: Optional[str] = None
