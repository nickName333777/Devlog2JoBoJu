"""
SQLAlchemy Models for FastAPI Backend
Oracle DB 테이블에 매핑되는 모델들
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy import UniqueConstraint # kakao social login
from sqlalchemy import Text, CLOB # freeboard
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import Sequence # 생성한 SEQ_TABLE__NO  자동삽입용

from sqlalchemy.sql import func
#from database import Base # from sqlalchemy.ext.declarative import declarative_base 에 Base 있음

Base = declarative_base()

# ================================================================
# 회원/인증
# ================================================================

class Level(Base):
    """레벨 테이블"""
    __tablename__ = "LEVELS"
    
    level_no = Column("LEVEL_NO", Integer, primary_key=True)
    required_total_exp = Column("REQUIRED_TOTAL_EXP", Integer, nullable=False)
    title = Column("TITLE", String(100), nullable=False)
    
    # 관계 설정
    members = relationship("Member", back_populates="member_level")


class Member(Base):
    """회원 테이블"""
    __tablename__ = "MEMBER"
    
    # PK
    #member_no = Column("MEMBER_NO", Integer, primary_key=True, autoincrement=True)
    member_no = Column("MEMBER_NO", Integer, Sequence("SEQ_MEMBER_NO"), primary_key=True, autoincrement=True)  # SEQ_MEMBER_NO 자동증가
    # 로그인 정보
    member_email = Column("MEMBER_EMAIL", String(30), nullable=False, unique=True)
    member_pw = Column("MEMBER_PW", String(200))
    # 기본 정보
    member_name = Column("MEMBER_NAME", String(30), nullable=False)
    member_nickname = Column("MEMBER_NICKNAME", String(30), nullable=False)
    member_tel = Column("MEMBER_TEL", String(13), nullable=False)
    member_career = Column("MEMBER_CAREER", String(50), nullable=False)
    # 상태값
    member_subscribe = Column("MEMBER_SUBSCRIBE", String(1), default='N', nullable=False)
    member_admin = Column("MEMBER_ADMIN", String(1), default='N', nullable=False)
    member_del_fl = Column("MEMBER_DEL_FL", String(1), default='N', nullable=False)
    profile_img = Column("PROFILE_IMG", String(300))
    # 프로필
    my_info_intro = Column("MY_INFO_INTRO", String(2000))
    my_info_git = Column("MY_INFO_GIT", String(200))
    my_info_homepage = Column("MY_INFO_HOMEPAGE", String(200))
    # 활동 정보
    subscription_price = Column("SUBSCRIPTION_PRICE", Integer, default=0, nullable=False)
    beans_amount = Column("BEANS_AMOUNT", Integer, default=0, nullable=False)
    current_exp = Column("CURRENT_EXP", Integer, default=0, nullable=False)
    # 날짜
    m_create_date = Column("M_CREATE_DATE", DateTime, default=datetime.now)
    # FK
    member_level_no = Column("MEMBER_LEVEL", Integer, ForeignKey("LEVELS.LEVEL_NO"), nullable=False)
    
    # 관계 설정
    member_level = relationship("Level", back_populates="members")
    social_logins = relationship("SocialLogin", back_populates="member")
    boards = relationship("Board", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    board_likes = relationship("BoardLike", back_populates="member")
	# 관계 설정: 챗봇 CbSession, CbTokenUsage 클래스
    chatbot_sessions = relationship("CbSession", back_populates="member")
    token_usages = relationship("CbTokenUsage", back_populates="member")
    
    
    # 제약조건
    __table_args__ = (
        CheckConstraint("MEMBER_SUBSCRIBE IN ('Y', 'N')", name="ck_member_subscribe"),
        CheckConstraint("MEMBER_ADMIN IN ('Y', 'N')", name="ck_member_admin"),
        CheckConstraint("MEMBER_DEL_FL IN ('Y', 'N')", name="ck_member_del_fl"),
    )


class Auth(Base):
    """이메일 인증 테이블"""
    __tablename__ = "AUTH"
    
    #auth_no = Column("AUTH_NO", Integer, primary_key=True, autoincrement=True)
    auth_no = Column("AUTH_NO", Integer, Sequence("SEQ_AUTH_NO"), primary_key=True, autoincrement=True)
    code = Column("CODE", String(100), nullable=False)
    email = Column("EMAIL", String(100), nullable=False, unique=True)
    create_at = Column("CREATE_AT", DateTime, default=datetime.now, nullable=False)
    
    
class SocialLogin(Base):
    """소셜 로그인 테이블"""
    __tablename__ = "SOCIAL_LOGIN"
    
    #social_no = Column("SOCIAL_NO", Integer, primary_key=True, autoincrement=True)
    social_no = Column("SOCIAL_NO", Integer,  Sequence("SEQ_SOCIAL_LOGIN_NO"), primary_key=True, autoincrement=True)
    provider = Column("PROVIDER", String(30), nullable=False)
    provider_id = Column("PROVIDER_ID", String(100), nullable=False)
    member_no = Column("MEMBER_NO", Integer, ForeignKey("MEMBER.MEMBER_NO"), nullable=False)
    
    # 관계 설정
    member = relationship("Member", back_populates="social_logins")
    
    # 제약조건: PROVIDER + PROVIDER_ID 복합 유니크
    __table_args__ = (
        UniqueConstraint('PROVIDER', 'PROVIDER_ID', name='UK_SOCIAL_LOGIN'),
        CheckConstraint("PROVIDER IN ('kakao', 'google', 'naver')"),
    )    


# ================================================================
# 자유게시판 모델들
# ================================================================

class BoardType(Base):
    """게시판 타입 테이블"""
    __tablename__ = 'BOARDTYPE'
    
    board_code = Column('BOARD_CODE', Integer, primary_key=True)
    board_name = Column('BOARD_NAME', String(20), nullable=False)
    parents_board_code = Column('PARENTS_BOARD_CODE', Integer, ForeignKey('BOARDTYPE.BOARD_CODE'))
    
    # 관계
    boards = relationship("Board", back_populates="board_type")


class Board(Base):
    """게시글 테이블"""
    __tablename__ = 'BOARD'
    
    # PK
    #board_no = Column('BOARD_NO', Integer, primary_key=True)
    board_no = Column('BOARD_NO', Integer, Sequence("SEQ_BOARD_NO"), primary_key=True)
        
    # 게시글 정보
    board_title = Column('BOARD_TITLE', String(300), nullable=False)
    board_content = Column('BOARD_CONTENT', CLOB, nullable=False)
    
    # 날짜
    b_create_date = Column('B_CREATE_DATE', DateTime, nullable=False, default=datetime.now)
    b_update_date = Column('B_UPDATE_DATE', DateTime)
    
    # 통계
    board_count = Column('BOARD_COUNT', Integer, nullable=False, default=0)
    
    # 상태
    board_del_fl = Column('BOARD_DEL_FL', String(1), nullable=False, default='N')
    
    # FK
    board_code = Column('BOARD_CODE', Integer, ForeignKey('BOARDTYPE.BOARD_CODE'), nullable=False)
    member_no = Column('MEMBER_NO', Integer, ForeignKey('MEMBER.MEMBER_NO'), nullable=False)
    
    # 뉴스 게시판용 (선택)
    news_reporter = Column('NEWS_REPORTER', String(100))
    
    # 관계
    board_type = relationship("BoardType", back_populates="boards")
    author = relationship("Member", back_populates="boards")
    images = relationship("BoardImg", back_populates="board", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="board", cascade="all, delete-orphan")
    likes = relationship("BoardLike", back_populates="board", cascade="all, delete-orphan")
	# 관계 설정: 챗봇 CbSession 클래스
    chatbot_sessions = relationship("CbSession", back_populates="board")        
    
    # 제약 조건
    __table_args__ = (
        CheckConstraint("BOARD_DEL_FL IN ('Y', 'N')"),
    )


class BoardImg(Base):
    """게시글 이미지 테이블"""
    __tablename__ = 'BOARD_IMG'
    
    #img_no = Column('IMG_NO', Integer, primary_key=True)
    img_no = Column('IMG_NO', Integer, Sequence("SEQ_IMAGE_NO"), primary_key=True)    
    img_path = Column('IMG_PATH', String(500), nullable=False)
    img_orig = Column('IMG_ORIG', String(200))
    img_rename = Column('IMG_RENAME', String(200))
    img_order = Column('IMG_ORDER', Integer, nullable=False)
    
    # FK
    board_no = Column('BOARD_NO', Integer, ForeignKey('BOARD.BOARD_NO'), nullable=False)
    
    # 관계
    board = relationship("Board", back_populates="images")


class BoardLike(Base):
    """게시글 좋아요 테이블"""
    __tablename__ = 'BOARD_LIKE'
    
    # 복합 PK
    board_no = Column('BOARD_NO', Integer, ForeignKey('BOARD.BOARD_NO'), primary_key=True)
    member_no = Column('MEMBER_NO', Integer, ForeignKey('MEMBER.MEMBER_NO'), primary_key=True)
    
    # 관계
    board = relationship("Board", back_populates="likes")
    member = relationship("Member", back_populates="board_likes")


class Comment(Base):
    """댓글 테이블"""
    __tablename__ = 'COMMENTS'
    
    # PK
    #comment_no = Column('COMMENT_NO', Integer, primary_key=True)
    comment_no = Column('COMMENT_NO', Integer, Sequence("SEQ_COMMENT_NO"), primary_key=True)
        
    # FK
    member_no = Column('MEMBER_NO', Integer, ForeignKey('MEMBER.MEMBER_NO'), nullable=False)
    board_no = Column('BOARD_NO', Integer, ForeignKey('BOARD.BOARD_NO'), nullable=False)
    parents_comment_no = Column('PARENTS_COMMENT_NO', Integer, ForeignKey('COMMENTS.COMMENT_NO'))
    
    # 댓글 정보
    c_create_date = Column('C_CREATE_DATE', DateTime, nullable=False, default=datetime.now)
    comment_content = Column('COMMENT_CONTENT', String(2000), nullable=False)
    
    # 상태
    comment_del_fl = Column('COMMENT_DEL_FL', String(1), nullable=False, default='N')
    secret_yn = Column('SECRET_YN', String(1), nullable=False, default='N')
    modify_yn = Column('MODIFY_YN', String(1), nullable=False, default='N')
    
    # 관계
    board = relationship("Board", back_populates="comments")
    author = relationship("Member", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[comment_no])
    
    # 제약 조건
    __table_args__ = (
        CheckConstraint("COMMENT_DEL_FL IN ('Y', 'N')"),
        CheckConstraint("SECRET_YN IN ('Y', 'N')"),
        CheckConstraint("MODIFY_YN IN ('Y', 'N')"),
    )
    

# ================================================================
# 챗봇 모델들
# ================================================================


class CbSession(Base):
    """
    챗봇 세션 테이블
    - 팝업 열 때 세션 시작 (STARTED_AT)
    - 팝업 닫을 때 세션 종료 (ENDED_AT)
    """
    __tablename__ = "CB_SESSION"
    
    # PK     
    cb_session_id = Column('CB_SESSION_ID',
        Integer,
        #Sequence('SEQ_CB_SESSION_NO', start=1, increment=1), #####
        Sequence('SEQ_CB_SESSION_NO'), #####
        primary_key=True,
        comment='챗봇세션식별자'
    )
    
    # 시간 정보
    started_at = Column('STARTED_AT',
        DateTime,
        default=func.sysdate(),
        nullable=True,
        comment='챗봇팝업시작시간'
    )
    ended_at = Column('ENDED_AT',
        DateTime,
        nullable=True,
        comment='챗봇팝업마침시간'
    )
    
    # 세션 유형
    cb_session_type = Column('CB_SESSION_TYPE',
        String(50),
        nullable=False,
        comment='챗봇세션유형(BASIC 기본형, KONG 커피콩충전형)'
    )
    
    # 게시글 유형
    cb_board_type = Column('CB_BOARD_TYPE',
        String(100),
        nullable=False,
        comment='게시글유형(INSERT 또는 UPDATE)'
    )
    
    # FK (회원)
    member_no = Column('MEMBER_NO',
        Integer,
        ForeignKey('MEMBER.MEMBER_NO'),
        nullable=False,
        comment='회원번호'
    )
    
    # FK (게시글) - nullable (글쓰기 시 NULL)
    board_no = Column('BOARD_NO',
        Integer,
        ForeignKey('BOARD.BOARD_NO'),
        nullable=True,
        comment='게시글번호(글쓰기:NULL, 글수정:BOARD_NO)'
    )
    
    # 관계 정의
    member = relationship("Member", back_populates="chatbot_sessions")
    board = relationship("Board", back_populates="chatbot_sessions")
    token_usages = relationship(
        "CbTokenUsage",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<CbSession(id={self.cb_session_id}, type={self.cb_session_type}, member={self.member_no})>"


class CbTokenUsage(Base):
    """
    토큰 사용 내역 테이블
    - 질문/답변 토큰 수 기록
    - 커피콩 과금 금액 계산 (5토큰 = 1콩, 테스트용)
    """
    __tablename__ = "CB_TOKEN_USAGE"
    
    # PK
    tk_usage_id = Column('TK_USAGE_ID',
        Integer,
        #Sequence('SEQ_TOKEN_USAGE_NO', start=1, increment=1), #####
        Sequence('SEQ_TOKEN_USAGE_NO'), #####
        primary_key=True,
        comment='토큰사용이력식별자'
    )
    
    # 질문/답변 내용 (CLOB)
    prompt_text = Column('PROMPT_TEXT',
        Text,  # Oracle CLOB 타입
        nullable=True,
        comment='사용자질문내용'
    )
    answer_text = Column('ANSWER_TEXT',
        Text,  # Oracle CLOB 타입
        nullable=True,
        comment='챗봇대답내용'
    )
    
    # 토큰 수
    prompt_tokens = Column('PROMPT_TOKENS',
        Integer,
        nullable=False,
        comment='사용자질문토큰수'
    )
    answer_tokens = Column('ANSWER_TOKENS',
        Integer,
        nullable=False,
        comment='챗봇대답토큰수'
    )
    total_tokens = Column('TOTAL_TOKENS',
        Integer,
        nullable=False,
        comment='전체토큰수(/세션)'
    )
    
    # 과금 정보
    bean_swe = Column('BEAN_SWE',
        Integer,
        nullable=True,
        comment='과금커피콩포인트SWEngineering'
    )
    
    # 모델명
    model_name = Column('MODEL_NAME',
        String(50),
        nullable=True,
        comment='챗봇이름(GPT-4o-mini)'
    )
    
    # FK (회원)
    member_no = Column('MEMBER_NO',
        Integer,
        ForeignKey('MEMBER.MEMBER_NO'),
        nullable=False,
        comment='회원번호'
    )
    
    # FK (세션)
    cb_session_id = Column('CB_SESSION_ID',
        Integer,
        ForeignKey('CB_SESSION.CB_SESSION_ID'),
        nullable=False,
        comment='챗봇세션식별자'
    )
    
    # 관계 정의
    member = relationship("Member", back_populates="token_usages")
    session = relationship("CbSession", back_populates="token_usages")
    
    def __repr__(self):
        return f"<CbTokenUsage(id={self.tk_usage_id}, session={self.cb_session_id}, tokens={self.total_tokens})>"

