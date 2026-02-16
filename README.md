# Devlog2JoBoJu

## 동기

KDT training 과정에서 자바 기반 웹앱 개발과 파이선 기반 데이터 분석 및 ML/DL 파트를 하나의 웹앱 개발로 통합하기에는 무리가 되는 부분들이 있어서, 이후 future direction의 일환으로 Java Spring-Boot 기반 Devlog 프로젝트 웹앱에서 내가 담당했던 부분들을 중심으로 일부를 Python FastAPI 기반 웹앱으로 Porting하는 작업을 수행해 보았다. 여기 파이선 웹앱으로 포팅된 기존 부분들에 파이썬 기반 데이터분석, ML/DL등의 내용들을 채워 계속 확장/톻합해 나가 볼 생각이다.


### SpringBoot 기반 웹 애플리케이션을 FastAPI 기반으로 포팅

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


###  아키텍처 변경

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


## 개발 워크플로우

### 코드 수정 시 재시작 필요 여부

| 변경 사항 | 재시작 필요? | 명령어 |
|-----------|-------------|--------|
| Python 코드 (.py) |  불필요 | 자동 리로드 (uvicorn --reload) |
| Static 파일 (HTML/CSS/JS) |  불필요 | 브라우저 새로고침 (Ctrl+Shift+R) |
| .env 파일 |  restart만 | `docker-compose restart fastapi-backend` |
| requirements.txt |  필요 | `docker-compose build --no-cache fastapi-backend && docker-compose up -d` |
| Dockerfile |  필요 | `docker-compose down && docker-compose build --no-cache && docker-compose up -d` |
| docker-compose.yml |  필요 | `docker-compose down && docker-compose up -d` |

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
docker logs oracle21c
#docker logs fastapi-backend
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
- `/init_scripts/init_PDB_XEPDB1.sql` - 회원 테이블, 게시판 테이블, 챗봇 테이블 (CB_SESSION, CB_TOKEN_USAGE)

**환경 설정:**
- `.env` - 환경 변수 (이미지 경로 설정 포함)
- `.env.example` - 환경 변수 템플릿 (OPENAI_API_KEY 포함)
- `docker-compose.yml` - Docker 설정
- `requirements.txt` - Python 의존성 (openai==1.12.0)
- `Dockerfile` - FastAPI 백엔드 이미지

---

<img width="845" height="730" alt="image" src="https://github.com/user-attachments/assets/5c8f0a68-262f-43eb-8d47-01a34cdef040" />

<img width="833" height="845" alt="image" src="https://github.com/user-attachments/assets/00d2c88d-4060-4438-8e39-a128b01701ca" />

<img width="834" height="912" alt="image" src="https://github.com/user-attachments/assets/e0bfdd10-226f-4a6e-9b5b-403c262cb573" />

<img width="836" height="913" alt="image" src="https://github.com/user-attachments/assets/4e082136-675e-484a-b06b-7b8e3546105a" />

<img width="831" height="909" alt="image" src="https://github.com/user-attachments/assets/eb7ef369-2ccb-4119-8bfc-c41545cfdbde" />

<img width="1090" height="918" alt="image" src="https://github.com/user-attachments/assets/4498b8b3-3d39-4301-a046-eb30b31a8bf7" />







