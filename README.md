# Devlog2JoBoJu

## 동기

KDT training 과정에서 자바 기반 웹앱 개발과 파이선 기반 데이터 분석 및 ML/DL 파트를 하나의 웹앱 개발로 통합하기에 무리가 되는 부분들이 있어서, 이후 future direction의 일환으로 Java Spring-Boot 기반 Devlog 프로젝트 웹앱에서 내가 담당했던 부분들을 중심으로 일부를 Python FastAPI 기반 웹앱으로 Porting하는 JoBoJu 프로젝트 수행해 보았다. 여기 파이선 웹앱으로 포팅된 기존 부분들에 파이썬 기반 데이터분석, ML/DL등의 내용들을 채워 계속 확장해 나가 볼 생각이다.


### SpringBoot 기반 웹 애플리케이션을 FastAPI 기반으로 완전 포팅

#### 원본 스택 (SpringBoot)
- **언어/프레임워크:** Java 17 + SpringBoot 3.5.7
- **ORM:** JPA/Hibernate (회원, 카카오 로그인) + MyBatis (게시판)
- **인증/보안:** Spring Security
- **템플릿 엔진:** Thymeleaf
- **데이터베이스:** Oracle Database 21c XE
- **검색엔진:** Elasticsearch (Docker)
- **개발환경:** STS4 IDE + Gradle

#### 목표 스택 (FastAPI)
- **언어/프레임워크:** Python 3.10 + FastAPI
- **ORM:** SQLAlchemy
- **인증/보안:** JWT (python-jose) + bcrypt
- **프론트엔드:** Native JavaScript (SPA 방식) -> 중간에 jinja2 SSR로 변경
- **데이터베이스:** Oracle Database 21c XE (PDB: XEPDB1)
- **검색엔진:** Elasticsearch + Kibana + Logstash
- **배포:** Docker Compose 기반 풀스택


---

## 현재  완료된 기능

#### 1. 회원가입/로그인
**주요 기능:**
- 이메일 인증 기반 회원가입
  - 6자리 랜덤 인증번호 생성
  - 5분 만료 시간 체크
  - SMTP(Gmail) 이메일 발송
- JWT 토큰 기반 인증/인가 (유효기간 1일)
- 이메일/닉네임 중복 체크 (실시간 AJAX)
- 비밀번호 bcrypt 해싱
- 쿠키 기반 "아이디 저장" 기능
- 레벨 시스템 (1~10레벨, 경험치 기반)

**파일 구조:**
- Backend: `member_router.py`, `email_router.py`, `auth.py`, `models.py`, `schemas.py`
- Frontend: `login.html/css/js`, `signup.html/css/js`
- DB: MEMBER, LEVELS, AUTH 테이블

#### 2. 카카오 소셜 로그인 
**주요 기능:**
- OAuth 2.0 인증 플로우
- 카카오 사용자 정보 연동 (kakaoId 기반)
- SOCIAL_LOGIN 테이블 (복합 유니크: PROVIDER + PROVIDER_ID)
- 신규 사용자: 필수 정보 입력 (`signupKakao.html`)
- 기존 사용자: 자동 로그인
- 이메일 기반 일반/소셜 계정 통합 가능

**파일 구조:**
- Backend: `kakao_router.py`, `kakao_service.py`, `kakao_schemas.py`
- Frontend: `signupKakao.html/js` (CSS는 signup.css 공유)
- DB: SOCIAL_LOGIN 테이블

**설정 필요:**
- `.env`에 `KAKAO_REST_API_KEY`, `KAKAO_CLIENT_SECRET`, `KAKAO_REDIRECT_URI` 설정
- 카카오 개발자 콘솔에서 Redirect URI 등록 필요

#### 3. 인프라 구성
**Docker Compose 멀티 컨테이너:**
- **FastAPI backend** (jbj-fastapi)
  - Uvicorn auto-reload (개발 시 코드 수정 즉시 반영)
  - Volume mount: `.:/app`, `./static:/app/static`
  - Port: 8880
  
- **Oracle 21c XE** (oracle21c)
  - PDB: XEPDB1 사용 (CDB가 아닌 PDB 사용 이유: 격리, 멀티테넌트 최적화)
  - User: jbj_user / Password: jbj_password1234
  - Port: 1521
  
- **Elasticsearch** (jbj-elasticsearch)
  - Version: 8.11.0
  - Port: 9200 
  
- **Kibana** (jbj-kibana)
  - Port: 5601
  
- **Logstash** (jbj-logstash)
  - Port: 5044 (현재 미사용)

**환경 변수 관리:**
- `.env` 파일로 민감 정보 관리
- `docker-compose.yml`에서 `env_file: .env` 참조

#### 4. 프론트엔드 아키텍처
**SPA 방식 (Static HTML + Native JS):**
- JWT 토큰 localStorage 저장
- `common.js`: API 호출 유틸리티, 인증 체크
- 공통 컴포넌트: header, footer, navigation
- 페이지별 독립 JS 모듈

**공통 컴포넌트:**
- `index.html` (메인 페이지)
- `common.css` (공통 스타일)
- `common.js` (API 호출, 인증 체크, 날짜 포맷 등)

---

#### 5. 자유게시판 CRUD 

**DB + 백엔드 API:**

**데이터베이스:**
- BOARDTYPE, BOARD, BOARD_IMG, BOARD_LIKE, COMMENT 테이블
- SEQ_BOARD_NO, SEQ_IMAGE_NO, SEQ_COMMENT_NO 시퀀스
- 인덱스: 게시판코드, 작성자, 작성일, 댓글

**백엔드:**
- SQLAlchemy 모델 (models_freeboard.py)
  - Oracle CLOB 타입 처리
  - 자기참조 관계 (대댓글)
  - CASCADE 삭제 설정
- Pydantic 스키마 (board_schemas.py)
  - Request/Response 검증
  - 재귀 댓글 구조
- FastAPI 라우터 (board_router.py - Jinja2 버전)
  - GET /board/list (목록 조회, HTMLResponse)
    - 페이징 (page, limit)
    - 검색 (keyword, search_type: title|content|author|all)
    - 정렬 (sort_by: recent|views|likes)
  - GET /board/{board_no} (상세 조회, HTMLResponse)
    - 조회수 자동 증가
    - 좋아요 개수 + 사용자 좋아요 여부
    - 댓글 개수

**파일 구조:**
- DB: init_freeboard.sql
- Backend: models_freeboard.py, board_schemas.py, routers/board_router.py

**Jinja2 템플릿 마이그레이션:**

**아키텍처 변경:**
- **기존:** SPA (Client-side rendering, API 호출)
- **변경:** SSR (Server-side rendering, Jinja2)
- **이유:** 
  - common.js 미구현 문제 해결
  - SEO 최적화
  - 초기 로딩 속도 개선
  - JavaScript 복잡도 감소

**템플릿 시스템:**
- base.html - 기본 레이아웃 (헤더/푸터 include)
- components/header.html - 공통 헤더
- components/footer.html - 공통 푸터
- board/freeboardList.html - 목록 (서버 렌더링)
- board/freeboardDetail.html - 상세 (서버 렌더링)

**목록 화면 (Jinja2):**
- 게시글 카드 레이아웃 (썸네일, 제목, 작성자, 통계)
- 검색 기능 (폼 submit)
- 정렬 기능 (URL 파라미터)
- 페이징 (하이퍼링크 방식)
- 반응형 디자인

**상세 화면 (Jinja2):**
- 게시글 내용 표시 (제목, 본문, 작성자 정보)
- 이미지 갤러리 (순서대로 표시)
- 좋아요 버튼 UI (JavaScript로 토글)
- 작성자 전용 버튼 (수정/삭제)
- 댓글 섹션 UI 준비

**이미지 경로 설정:**
- 실제 저장: `/mnt/user-data/uploads/images/board/freeboard/`
- 웹 접근: `/uploads/images/board/freeboard`
- 환경 변수: `UPLOAD_DIR`, `UPLOAD_WEB_PATH`

**파일 구조:**
- Backend: main.py (Jinja2 설정), auth.py (Optional 인증)
- Templates: templates/base.html, templates/board/*.html
- Components: templates/components/*.html
- Static: static/css/*.css, static/js/*.js (인터랙션만)
- Config: .env (이미지 경로 설정 추가)


**게시글 작성/수정/삭제 + 이미지 업로드:**

**유틸리티 & 예외 처리:**
- utils.py - Java Util 클래스 포팅
  - XSS 방지, 파일명 변경 (UUID), 시간 포맷팅
  - 파일 검증, 경로 조작 방지
- exceptions.py - Java Exception 클래스 포팅
  - 파일/인증/데이터 예외 클래스
  - 전역 예외 핸들러 (에러 코드 체계)

**게시판 서비스:**
- board_service.py - BoardService 클래스
  - create_board() - 작성 + 이미지 업로드 (최대 5개)
  - update_board() - 수정 + 이미지 관리
  - 확장자 검증 (jpg, jpeg, png, gif, webp)
  - 파일 크기 제한 (10MB)
  - 저장 경로: /mnt/user-data/uploads/images/board/freeboard/

**작성/수정 API:**
- POST /board/write - 게시글 작성
- GET /board/update/{id} - 수정 페이지
- POST /board/update/{id} - 수정 처리
- POST /board/delete/{id} - 소프트 삭제

**템플릿:**
- templates/board/freeboardWrite.html - 작성 페이지
- templates/board/freeboardUpdate.html - 수정 페이지
- static/css/freeboardWrite.css - 작성/수정 스타일
- 이미지 미리보기, 삭제 표시, 폼 검증

**좋아요 토글 + 댓글 CRUD:**

**좋아요 API (AJAX):**
- POST `/api/board/{board_no}/like` - 좋아요 토글
  - 복합 PK (board_no + member_no) 활용
  - 토글 로직: 없으면 추가 / 있으면 제거
  - 응답: `{ is_liked, like_count }` → 클라이언트 즉시 반영

**댓글 API (AJAX):**
- GET `/api/board/{board_no}/comments` - 댓글 목록
  - 재귀 트리 구조 (루트 댓글 + replies 중첩)
  - 비밀댓글: 작성자/게시글작성자만 내용 표시
  - 삭제된 댓글: "삭제된 댓글입니다." 표시 (대댓글 보존)
- POST `/api/board/{board_no}/comments` - 댓글 작성
  - XSS 방지 (Util.xss_handling)
  - 대댓글 지원 (parents_comment_no)
  - 비밀댓글 지원 (secret_yn)
  - 글자 제한 2000자
- PUT `/api/board/comments/{comment_no}` - 댓글 수정
  - 작성자만 수정 가능 (권한 검증)
  - modify_yn = 'Y' 자동 표시
- DELETE `/api/board/comments/{comment_no}` - 댓글 삭제
  - 대댓글 있으면 소프트 삭제 (COMMENT_DEL_FL = 'Y')
  - 대댓글 없으면 실제 삭제

**프론트엔드 (freeboardDetail.html):**
- 좋아요 AJAX 토글 (실시간 카운트 + 하트 아이콘 전환)
- 댓글 목록 AJAX 로드 (재귀 트리 렌더링)
- 댓글 작성 폼 (루트 + 답글 폼 분리)
- 인라인 수정 폼
- 답글 폼 토글 (클릭 시 삽입/제거)
- 클라이언트 XSS 방지 (escapeHtml)
- 글자수 표시 (0 / 2000)
- 비밀댓글 체크 + 배지 표시

**스타일 (freeboardDetail.css):**
- 댓글 아이템, 대댓글 들여쓰기, 답글 폼, 인라인 수정, 배지

**main.py 업데이트:**
- comment_like_router 등록
- board_write_router 등록
- register_exception_handlers() 등록


---

## 🔑 중요한 설계/포팅 결정

### 1. 아키텍처 변경

| 항목 | SpringBoot | FastAPI (초기) | FastAPI (Jinja2) | 이유 |
|------|-----------|---------------|------------------|------|
| 패턴 | MVC (SSR) | REST API + SPA | SSR (Jinja2) | SEO, 초기 로딩 개선 |
| 템플릿 | Thymeleaf | Static HTML + JS | Jinja2 | 서버 렌더링, 템플릿 상속 |
| 렌더링 | Server-side | Client-side | Server-side | 안정성, 유지보수성 |
| 상태 관리 | 세션 기반 | JWT (Stateless) | JWT (Stateless) | RESTful 원칙 |
| ORM | JPA/Hibernate + MyBatis | SQLAlchemy | SQLAlchemy | Python 표준 ORM |
| 검증 | Bean Validation | Pydantic | Pydantic | 타입 힌트 기반 |

**주요 변경 사항:**
- SPA → SSR: common.js 미구현 문제 해결
- JavaScript 역할 축소: 전체 렌더링 → 인터랙션만 (좋아요, 댓글)
- 템플릿 상속: base.html → 페이지별 extends
- 이미지 경로 분리: 실제 저장 경로 vs 웹 접근 경로

### 2. 데이터베이스 설계

#### PDB(XEPDB1) vs CDB(XE) 선택
**PDB 사용 이유:**
- 격리: 애플리케이션별 독립적인 데이터베이스 환경
- 멀티테넌트 최적화: Oracle 12c 이후 권장 아키텍처
- 개발/운영 분리: PDB별로 환경 분리 용이
- 보안: CDB는 관리용, PDB는 애플리케이션용

**현재 테이블 구조:**

**회원 관련:**
```
MEMBER (회원)
├── MEMBER_NO (PK)
├── MEMBER_EMAIL (UK)
├── MEMBER_LEVEL (FK → LEVELS.LEVEL_NO)
├── MEMBER_PW (bcrypt 해시)
├── MEMBER_NICKNAME
└── ...

LEVELS (레벨)
├── LEVEL_NO (PK)
├── REQUIRED_TOTAL_EXP
└── TITLE

AUTH (이메일 인증)
├── AUTH_NO (PK)
├── CODE (6자리)
├── EMAIL
└── CREATE_AT (5분 만료)

SOCIAL_LOGIN (소셜 로그인)
├── SOCIAL_NO (PK)
├── PROVIDER (kakao, google, naver)
├── PROVIDER_ID
├── MEMBER_NO (FK → MEMBER.MEMBER_NO)
└── UK(PROVIDER, PROVIDER_ID)
```

**자유게시판 관련:**
```
BOARDTYPE (게시판 타입)
├── BOARD_CODE (PK)
├── BOARD_NAME
└── PARENTS_BOARD_CODE (FK → BOARDTYPE.BOARD_CODE, 계층 구조)
  - 1: 공지사항
  - 2: 질문게시판
  - 3: 자유게시판
  - 4: FAQ

BOARD (게시글)
├── BOARD_NO (PK, SEQ_BOARD_NO)
├── BOARD_TITLE (VARCHAR2 300)
├── BOARD_CONTENT (CLOB)
├── B_CREATE_DATE (DATE)
├── B_UPDATE_DATE (DATE)
├── BOARD_COUNT (조회수)
├── BOARD_DEL_FL (Y/N, 소프트 삭제)
├── BOARD_CODE (FK → BOARDTYPE.BOARD_CODE)
├── MEMBER_NO (FK → MEMBER.MEMBER_NO)
└── NEWS_REPORTER (뉴스용 선택 필드)

BOARD_IMG (게시글 이미지)
├── IMG_NO (PK, SEQ_IMAGE_NO)
├── IMG_PATH (저장 경로)
├── IMG_ORIG (원본 파일명)
├── IMG_RENAME (변경된 파일명, UUID)
├── IMG_ORDER (0: 썸네일, 1~4: 서브)
└── BOARD_NO (FK → BOARD.BOARD_NO, ON DELETE CASCADE)

BOARD_LIKE (게시글 좋아요)
├── BOARD_NO (PK, FK → BOARD.BOARD_NO)
├── MEMBER_NO (PK, FK → MEMBER.MEMBER_NO)
└── 복합 PK (BOARD_NO, MEMBER_NO)

COMMENT (댓글)
├── COMMENT_NO (PK, SEQ_COMMENT_NO)
├── MEMBER_NO (FK → MEMBER.MEMBER_NO)
├── BOARD_NO (FK → BOARD.BOARD_NO)
├── PARENTS_COMMENT_NO (FK → COMMENT.COMMENT_NO, 대댓글)
├── C_CREATE_DATE (DATE)
├── COMMENT_CONTENT (VARCHAR2 2000)
├── COMMENT_DEL_FL (Y/N, 소프트 삭제)
├── SECRET_YN (Y/N, 비밀댓글)
└── MODIFY_YN (Y/N, 수정 여부)
```

**인덱스 (성능 최적화):**
```
IDX_BOARD_CODE → BOARD(BOARD_CODE)
IDX_BOARD_MEMBER → BOARD(MEMBER_NO)
IDX_BOARD_DATE → BOARD(B_CREATE_DATE DESC)
IDX_COMMENT_BOARD → COMMENT(BOARD_NO)
IDX_COMMENT_MEMBER → COMMENT(MEMBER_NO)
```

**시퀀스:**
```
SEQ_BOARD_NO → 게시글 번호
SEQ_IMAGE_NO → 이미지 번호
SEQ_COMMENT_NO → 댓글 번호
```

**AI 챗봇 관련:**
```
CB_SESSION (챗봇 세션)
├── CB_SESSION_ID (PK, SEQ_CB_SESSION_NO)
├── STARTED_AT (DATE, DEFAULT SYSDATE)
├── ENDED_AT (DATE, nullable)
├── CB_SESSION_TYPE (VARCHAR2 50, BASIC/KONG)
├── CB_BOARD_TYPE (VARCHAR2 100, INSERT/UPDATE)
├── MEMBER_NO (FK → MEMBER.MEMBER_NO)
└── BOARD_NO (FK → BOARD.BOARD_NO, nullable)

CB_TOKEN_USAGE (토큰 사용 내역)
├── TK_USAGE_ID (PK, SEQ_TOKEN_USAGE_NO)
├── PROMPT_TEXT (CLOB, 사용자 질문)
├── ANSWER_TEXT (CLOB, 챗봇 답변)
├── PROMPT_TOKENS (NUMBER, 질문 토큰 수)
├── ANSWER_TOKENS (NUMBER, 답변 토큰 수)
├── TOTAL_TOKENS (NUMBER, 총 토큰 수)
├── BEAN_SWE (NUMBER, 차감 커피콩)
├── MODEL_NAME (VARCHAR2 50, gpt-4o-mini)
├── MEMBER_NO (FK → MEMBER.MEMBER_NO)
└── CB_SESSION_ID (FK → CB_SESSION.CB_SESSION_ID)
```

**챗봇 시퀀스:**
```
SEQ_CB_SESSION_NO → 챗봇 세션 ID
SEQ_TOKEN_USAGE_NO → 토큰 사용 이력 ID
```


### 3. 인증 방식 변경

#### SpringBoot → FastAPI 변경 사항
- **SpringBoot:** Spring Security (세션 기반)
- **FastAPI:** python-jose (JWT 기반) -> member_router.py에서 req.session["user"] = SessionLoginMemberDTO()과 core/dependencies.py 사용한  Session 기반으로 변경

#### 로그인 플로우
1. 이메일/비밀번호 검증 (bcrypt)
2. JWT 토큰 생성 (유효기간 1일)
   - Payload: `memberNo`, `memberEmail`, `memberNickname`, `role`
3. 클라이언트: localStorage에 저장 
4. 모든 API 요청 시 `Authorization: Bearer <token>` 헤더 포함
5. 서버: JWT 검증 후 요청 처리
6. 이후 서버 Session 저장 방식으로 변경 후 3,4,5번은 더이상 유효하지 않음:
   서버 메모리(Session)저장하고, 서버에서 로그인 상태 체크/유지

### 4. 이메일 인증 플로우

**구현 방식:**
1. 사용자가 이메일 입력 후 "인증번호 받기" 클릭
2. 서버에서 6자리 랜덤 인증번호 생성
3. AUTH 테이블에 저장 (CREATE_AT 기준 5분 만료)
4. SMTP(Gmail)로 이메일 발송
5. 프론트에서 타이머 표시 (05:00 → 00:00)
6. 사용자가 인증번호 입력 후 "인증하기" 클릭
7. 서버에서 인증번호 + 만료 시간 검증
8. 성공 시 회원가입 진행

### 5. 카카오 로그인 통합 전략

**DB 구조:**
- 카카오 ID를 SOCIAL_LOGIN 테이블에 저장
- Member 테이블과 1:N 관계 (한 회원이 여러 소셜 계정 연동 가능)
- 복합 유니크 제약: (PROVIDER, PROVIDER_ID)

**로그인 플로우:**
1. 사용자가 "카카오 로그인" 버튼 클릭
2. FastAPI → 카카오 인증 서버로 리다이렉트
3. 카카오 로그인 성공 → 인가 코드 받음
4. FastAPI: 인가 코드로 액세스 토큰 요청
5. 액세스 토큰으로 사용자 정보(kakaoId) 조회
6. SOCIAL_LOGIN 테이블에서 kakaoId 검색
   - **기존 회원:** 자동 로그인 → 메인 페이지
   - **신규 회원:** 필수 정보 입력 페이지 → 회원가입 → 로그인

**이메일 매칭:**
- 카카오에서 제공하는 이메일과 일반 회원가입 이메일이 같으면 통합 가능
- 사용자가 원하면 소셜 로그인과 일반 로그인 모두 사용 가능

### 6. 파일 업로드 전략

**이미지 업로드 규칙:**
- 최대 5장
- 첫 번째 이미지가 썸네일 (대표 이미지)
- 허용 포맷: image/* (jpg, png, gif, webp 등)
- 저장 위치: `/mnt/user-data/uploads/images/board/freeboard/`

**DB 저장:**
- BOARD_IMG 테이블에 메타데이터 저장
  - IMG_PATH, IMG_ORIG, IMG_RENAME, IMG_ORDER

**SQLAlchemy 주의사항:**
- Oracle CLOB 타입 처리 (BOARD_CONTENT)
- SEQUENCE 자동 증가 (SEQ_BOARD_NO, SEQ_IMAGE_NO, SEQ_COMMENT_NO)

### 7. 자유게시판 주요 설계 결정

#### 페이징 전략
- **방식:** Offset-based pagination
- **기본값:** page=1, limit=10
- **최대값:** limit=50 (과도한 데이터 요청 방지)
- **장점:** 간단하고 Oracle에서 잘 지원
- **개선 가능:** Cursor-based pagination (대용량 데이터)

#### 검색 전략
- **현재:** SQL LIKE 연산자 사용
  - `BOARD_TITLE LIKE '%keyword%'`
  - `MEMBER_NICKNAME LIKE '%keyword%'` (JOIN)
- **개선 계획:** Elasticsearch 전문 검색 통합
  - 형태소 분석
  - 하이라이팅
  - 자동완성

#### 정렬 방식
- **최신순:** `ORDER BY B_CREATE_DATE DESC`
- **조회수순:** `ORDER BY BOARD_COUNT DESC`
- **좋아요순:** 서브쿼리로 COUNT 후 정렬

#### 좋아요 개수 조회
- **방식:** 매번 COUNT 쿼리 실행
- **이유:** 실시간 정확성 보장
- **개선 가능:** 
  - BOARD 테이블에 `like_count` 컬럼 추가
  - 트리거로 자동 업데이트
  - 캐싱 (Redis)

#### 댓글 구조
- **대댓글:** `PARENTS_COMMENT_NO` 자기참조
- **렌더링:** 재귀 구조 (Pydantic 모델)
- **삭제:** 소프트 삭제 (`COMMENT_DEL_FL = 'Y'`)
  - 내용은 "삭제된 댓글입니다"로 표시
  - 대댓글이 있으면 완전 삭제 불가

#### 이미지 순서 규칙
- **img_order = 0:** 썸네일 (대표 이미지)
  - 목록에서 표시
  - OpenGraph 메타 태그용
- **img_order = 1~4:** 서브 이미지
  - 본문에서 갤러리로 표시

#### 소프트 삭제 전략
- **게시글:** `BOARD_DEL_FL = 'Y'`
  - 목록/상세 조회 시 필터링
  - 관리자는 복구 가능
- **댓글:** `COMMENT_DEL_FL = 'Y'`
  - "삭제된 댓글입니다" 표시
  - 대댓글 구조 유지

#### N+1 문제 방지
- **Eager Loading:** `joinedload()` 사용
  - 목록: `joinedload(Board.author)`
  - 상세: `joinedload(Board.images)`
- **서브쿼리:** 좋아요/댓글 개수
  - 별도 쿼리로 집계

---

## 남아 있는 문제/리스크

### 1. Elasticsearch 미활용
- **현상:** 컨테이너는 실행 중이나 검색 기능 미구현
- **원인:** Logstash 파이프라인 미설정, FastAPI 연동 코드 부재
- **해결 계획:** 이후 적절한 단계에서 게시글 검색 통합 (elasticsearch-py 사용)

### 2. 에러 처리 미흡
- **문제:**
  - 전역 예외 핸들러 부재
  - 프론트엔드 에러 메시지 UX 개선 필요
  - Oracle 연결 실패 시 재시도 로직 없음
- **해결 계획:**
  - FastAPI의 `@app.exception_handler` 구현
  - 프론트: 에러 모달 또는 토스트 메시지
  - DB 연결: sqlalchemy.pool.Pool retry 설정

### 3. 보안 강화 필요
- **현재 상태:**
  - CORS: 모든 origin 허용 (개발용)
  - Rate Limiting 미구현
  - HTTPS 미설정
- **해결 계획:**
  - CORS: 프로덕션에서 특정 도메인만 허용
  - slowapi를 이용한 Rate Limiting
  - Nginx + Let's Encrypt로 HTTPS 설정

### 4. 테스트 부재
- **문제:** 단위/통합 테스트 없음
- **해결 계획:**
  - pytest + pytest-asyncio
  - httpx.AsyncClient로 API 테스트
  - DB 테스트: SQLAlchemy TestSession

### 5. 성능 최적화 미완료
- **문제:**
  - DB 인덱스 미설정
  - 쿼리 N+1 문제 가능성 (Lazy Loading)
  - 이미지 리사이징/압축 미구현
- **해결 계획:**
  - 인덱스: MEMBER_EMAIL, BOARD_CODE, MEMBER_NO 등
  - Eager Loading: `joinedload()` 사용
  - Pillow로 이미지 리사이징

### 6. Docker 환경 이슈
- **문제:**
  - Oracle 컨테이너 재시작 시 연결 대기 로직 필요
  - 환경 변수 우선순위 혼란 (.env vs docker-compose.yml)
- **해결:**
  - Health check 개선
  - `env_file: .env` 사용 (docker-compose.yml)

---

## 작업 우선순위

### 우선순위 1: 자유게시판 CRUD 포팅

**완료된 단계:**
1. DB 테이블 생성 + SQLAlchemy 모델
2. Pydantic 스키마
3. 게시판 목록 조회 API + Frontend
4. 게시글 상세 조회 API + Frontend
5. 게시글 작성 API + Frontend (이미지 업로드 포함)
6. 게시글 수정/삭제 API + Frontend
7. 댓글 CRUD API + Frontend
8. 좋아요 API + Frontend
9. 이미지 다중 업로드 (최대 5장, UUID 파일명, XSS 방지)

**현재 성과:**
- CRUD 패턴 정립 (목록 조회, 상세 조회)
- 페이징/정렬/검색 구현
- 반응형 UI 구현
- JWT 인증 통합
- 파일 업로드 시스템 완성

**최근 수정 (2026-02-05):**
- 게시글 수정 시 다중 이미지 업로드 문제 해결
  - FormData 명시적 생성 및 파일 개별 추가
  - 서버 측 이미지 개수 검증 로직 수정 (삭제 예정 이미지 차감)
  - 실시간 이미지 개수 표시 UI 추가


### 우선순위 2: AI 챗봇 통합 완료
**목표:** Spring AI 기반 챗봇을 OpenAI Python SDK로 포팅

**주요 기능:**
- **무료형 챗봇 (BASIC):**
  - 입력 제한: 20자 (테스트용) / 500자 (실제)
  - 응답 제한: 500자
  - 커피콩 과금 없음
  - 간단한 질의응답용

- **유료형 챗봇 (KONG):**
  - 입력 제한: 4000자
  - 응답 제한: 없음
  - 커피콩 과금: 5토큰당 1콩 (테스트용) / 500토큰당 1콩 (실제)
  - 상세한 답변 제공

**기술 스택:**
- OpenAI API: gpt-4o-mini 모델
- 토큰 계산: OpenAI `usage` 메타데이터 활용
- 과금 시스템: 실시간 커피콩 차감
- 세션 관리: 메모리 기반 누적 토큰 추적

**완료된 단계:**
1.  **1단계 (DB + 모델 + 스키마):**
   - CB_SESSION, CB_TOKEN_USAGE 테이블 생성
   - SQLAlchemy 모델 (models_chatbot.py)
   - Pydantic 스키마 (chatbot_schemas.py)

2.  **2단계 (프론트엔드):**
   - fbChatbotRevBasic.html (무료형 팝업)
   - fbChatbotRevKong.html (유료형 팝업)
   - fbChatbot.css (공통 스타일)
   - fbChatbot.js (챗봇 로직, Thymeleaf 제거)

3.  **3단계 (백엔드 API):**
   - chatbot_service.py (OpenAI 연동, 토큰 계산)
   - chatbot_router.py (세션 시작/종료, 메시지 API)
   - .env.example (환경 변수 템플릿)
   - requirements.txt (openai==1.12.0 추가)
   - Dockerfile (OpenAI SDK 설치)
   - docker-compose.yml (서비스 설정)
   - CHATBOT_TEST_GUIDE.md (테스트 가이드)

**주요 설계 결정:**
- **세션 관리:** 팝업 열 때 세션 시작, 닫을 때 종료 + 커피콩 차감
- **토큰 추적:** 메모리 캐시 (`ConcurrentHashMap` → Python `dict`)
- **과금 로직:** 세션별 누적 토큰 → 커피콩 계산 → DB 기록 (KONG만)
- **팝업 통신:** `window.opener.globalData`로 부모-자식 간 데이터 전달
- **안전한 종료:** `beforeunload` 이벤트 + `fetch` with `keepalive: true`
- **Thymeleaf 제거:** 모든 데이터를 API 호출로 가져오기
- **OpenAI 연동:** `openai.chat.completions.create()` 비동기 호출

### 우선순위 3: Elasticsearch 검색 통합
- 게시글 전문 검색 기능 추가

### 우선순위 4: 모니터링/로깅
- Logstash 파이프라인 설정
- Kibana 대시보드 구성

---

## 개발 워크플로우

### 코드 수정 시 재시작 필요 여부

| 변경 사항 | 재시작 필요? | 명령어 |
|-----------|-------------|--------|
| Python 코드 (.py) | ❌ 불필요 | 자동 리로드 (uvicorn --reload) |
| Static 파일 (HTML/CSS/JS) | ❌ 불필요 | 브라우저 새로고침 (Ctrl+Shift+R) |
| .env 파일 | ⚠️ restart만 | `docker-compose restart fastapi-backend` |
| requirements.txt | ✅ 필요 | `docker-compose build --no-cache fastapi-backend && docker-compose up -d` |
| Dockerfile | ✅ 필요 | `docker-compose down && docker-compose build --no-cache && docker-compose up -d` |
| docker-compose.yml | ✅ 필요 | `docker-compose down && docker-compose up -d` |

### 개발 시작 절차
```bash

# 1. 컨테이너 시작 
docker compose up -d

# 1-1: 컨테이너 시작에 문제 있을시(기존 네트워크연결로 문제시): 네트워크 완전 삭제 → 새로 생성 → 컨테이너 재빌드까지 한 번에 해결
# (프로젝트 폴더명 기반으로 자동 생성된 네트워크까지 완벽 정리후 새로 생성)
docker compose down --volumes --remove-orphans && docker network prune -f && docker compose up -d --build --force-recreate

# 2-1. 네트워크 연결확인
docker exec -it jbj-fastapi ping -c 3 oracle21c

# 2-2. 로그 확인 (터미널 1)
#docker-compose logs -f fastapi-backend
docker logs fastapi-backend
docker logs jbj-fastapi

# 3. 코드 수정 (VS Code 또는 nano)
# → 저장 → 로그에서 "Reloading..." 확인

# 4. API 테스트 (터미널 2)
curl http://localhost:8880/health

# 5. 브라우저 테스트
# F12 → Network 탭 → 요청 확인

# 6. 작업 종료
docker compose down
```

---

### 주요 파일 위치

**Backend (자유게시판):**
- `models.py` - SQLAlchemy 모델
- `schemas.py` - Pydantic 스키마 (로그인, 회원가입, 카카오 소셜 로그인)
- `board_schemas.py` - Pydantic 스키마 (게시판, 댓글, 좋아요)
- `routers/board_router.py` - 목록/상세 라우터 (Jinja2)
- `routers/board_write_router.py` - 작성/수정/삭제 라우터
- `routers/comment_like_router.py` - 좋아요 토글 + 댓글 CRUD API
- `board_service.py` - 게시판 비즈니스 로직 (작성/수정/이미지)
- `utils.py` - 유틸리티 함수 (XSS, 파일명 변경 등)
- `exceptions.py` - 예외 클래스 (전역 핸들러)
- `auth.py` - JWT 인증 (Optional 사용자 지원)
- `main.py` - FastAPI 앱 (Jinja2 + 라우터 + 예외핸들러)

**Backend (챗봇):**
- `models_chatbot.py` - SQLAlchemy 모델 (CbSession, CbTokenUsage)
- `chatbot_schemas.py` - Pydantic 스키마 (챗봇 요청/응답)
- `routers/chatbot_router.py` - 세션 시작/종료, 메시지 API
- `chatbot_service.py` - OpenAI 연동, 토큰 계산

**Templates (Jinja2):**
- `templates/base.html` - 기본 레이아웃
- `templates/components/header.html` - 헤더
- `templates/components/footer.html` - 푸터
- `templates/board/freeboardList.html` - 목록 화면
- `templates/board/freeboardDetail.html` - 상세 (좋아요 AJAX + 댓글 트리)
- `templates/board/freeboardWrite.html` - 작성 폼
- `templates/board/freeboardUpdate.html` - 수정 폼

**Static - 챗봇 (HTML/CSS/JS):**
- `static/fbChatbotRevBasic.html` - 무료형 챗봇 팝업
- `static/fbChatbotRevKong.html` - 유료형 챗봇 팝업
- `static/css/board/freeboard/fbChatbot.css` - 챗봇 스타일
- `static/js/board/freeboard/fbChatbot.js` - 챗봇 로직

**Static (CSS/JS):**
- `static/css/common.css` - 공통 스타일
- `static/css/freeboardList.css` - 목록 스타일
- `static/css/freeboardDetail.css` - 상세 스타일 (댓글 트리 포함)
- `static/css/freeboardWrite.css` - 작성/수정 스타일
- `static/js/common.js` - 공통 JS (단순화)
- `static/images/` - 정적 이미지 (로고, 아이콘)
- `static/images/board/freeboard/` - 챗봇 이미지

**Uploads (사용자 파일):**
- `/mnt/user-data/uploads/profiles/` - 프로필 이미지
- `/mnt/user-data/uploads/boards/` - 게시글 이미지

**DB 초기화:**
- `/init_scripts/init_PDB_XEPDB1.sql` - 회원 테이블, 게시판 테이블
- `/init_scripts/init_chatbot.sql` - 챗봇 테이블 (CB_SESSION, CB_TOKEN_USAGE)

**환경 설정:**
- `.env` - 환경 변수 (이미지 경로 설정 포함)
- `.env.example` - 환경 변수 템플릿 (OPENAI_API_KEY 포함)
- `docker-compose.yml` - Docker 설정
- `requirements.txt` - Python 의존성 (openai==1.12.0)
- `Dockerfile` - FastAPI 백엔드 이미지

---
