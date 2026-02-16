------------------------------------------------------------
-- PDB (Pluggable DB, 서비스name: XEPDB1) 용 유저 생성 by 관리자
-- [여기부터 4줄 관리자 계정접속해서 PDB(XEPDB1)에 'jbj_user'계정 생성]
------------------------------------------------------------
--
--
---- 1. 관리자 계정(sys as sysdba)으로 접속
---- 관리자 계정임을 확인
--SELECT USER FROM dual;
---- 'SYS' 나와야함
--
---- 2. CDB$ROOT로 이동 후 새 PDB (XEPDB1) 생성
---- 2-0) CDB 루트에서 실행
--ALTER SESSION SET CONTAINER = CDB$ROOT;
--SHOW CON_NAME; 
---- CDB$ROOT 나옴
--
---- CDB 레벨 확인
--SELECT 'CDB (XE)' as location, username, account_status, common 
--FROM cdb_users;
----WHERE username = 'JBJ_USER'; # 'JBJ_USER'가 CDB, PDB에 각각 하나씩 있을 수 있으나, 이름만 같을뿐 별개의 nampespace
--
---- 2-1) 모든 PDB 목록 확인
--SHOW PDBS;
--SELECT name, open_mode FROM v$pdbs;
--
---- 2-2) XEPDB1 생성 (admin 사용자 포함)
--CREATE PLUGGABLE DATABASE XEPDB1 
--ADMIN USER xepdb1_admin IDENTIFIED BY xepdb1_pass123
--ROLES=(CONNECT, RESOURCE, DBA)
--FILE_NAME_CONVERT=(
--  '/opt/oracle/oradata/XE/pdbseed/',
--  '/opt/oracle/oradata/XE/XEPDB1/'
--);
--
---- 2-3) PDB 열기
--ALTER PLUGGABLE DATABASE XEPDB1 OPEN;
--
---- 3. 새 PDB로 접속 테스트
--ALTER SESSION SET CONTAINER = XEPDB1;
--SHOW CON_NAME;  
---- "XEPDB1" 나옴
--
---- 모든 사용자 계정 조회
--SELECT username FROM dba_users;
---- 기존 사용자 삭제 (테이블 등 객체도 함께 삭제)
--DROP USER jbj_user CASCADE;
---- 기존 사용자 삭제 확인
--SELECT username FROM dba_users WHERE username = 'JBJ_USER';
---- 아무 결과도 안 나오면 성공
--
---- 새 사용자 생성
--CREATE USER jbj_user IDENTIFIED BY jbj_pass123;
----GRANT CONNECT, RESOURCE, CREATE TABLE TO jbj_user;
---- 권한 부여
--GRANT CONNECT, RESOURCE, CREATE VIEW TO jbj_user;
---- CONNECT : DB 연결 권한 ROLE (SET CONTAINER, CREATE SESSION; 2개 권한)
---- RESOURCE : DB 기본 객체 생성 권한 ROLE (CREATE INDEXTYPE, 
--                   --  CREATE OPERATOR, CREATE TYPE, CREATE TRIGGER,
--                   --  CREATE PROCEDURE, CREATE SEQUENCE, CREATE CLUSTER
--                   -- CREATE TABLE; 8개 권한)
---- 객체 생성 공간 할당성QUOTA UNLIMITED ON SYSTEM;
----ALTER USER jbj_user DEFAULT TABLESPACE SYSTEM
----QUOTA UNLIMITED ON SYSTEM;
--ALTER USER jbj_user DEFAULT TABLESPACE USERS
--                    TEMPORARY TABLESPACE TEMP
--                    QUOTA UNLIMITED ON USERS;
--
--COMMIT;
--
---- 확인
--SELECT username, account_status, common
--FROM dba_users 
--WHERE username = 'JBJ_USER';
--
---- 현재 PDB 확인
--SHOW CON_NAME;
---- XEPDB1 나옴
--
---- XEPDB1 레벨 확인
--SELECT 'PDB (XEPDB1)' as location, username, account_status, common 
--FROM dba_users;
----WHERE username = 'JBJ_USER';
--
---- 모든 PDB 목록 확인 (CDB 보다는 적은 목록확인 가능)
--SHOW PDBS;
--SELECT name, open_mode FROM v$pdbs;
--
--

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-- JBJ Database 초기화 스크립트

DROP TABLE "AUTH";
DROP TABLE "CB_TOKEN_USAGE";
DROP TABLE "SOCIAL_LOGIN";
DROP TABLE "NOTIFICATION";
DROP TABLE "BOARD_IMG";
DROP TABLE "CB_SESSION";
DROP TABLE "BOARD_LIKE";
DROP TABLE "COMMENTS";
DROP TABLE "BOARD";
DROP TABLE "BOARDTYPE";
DROP TABLE "MEMBER";
DROP TABLE "LEVELS";

 SELECT * FROM USER_CONSTRAINTS WHERE TABLE_NAME = "tabnam";


-- LEVELS 테이블 생성
DROP TABLE "LEVELS";
CREATE TABLE LEVELS (
    LEVEL_NO NUMBER NOT NULL,
    REQUIRED_TOTAL_EXP NUMBER NOT NULL,
    TITLE VARCHAR2(100) NOT NULL,
    CONSTRAINT PK_LEVELS PRIMARY KEY (LEVEL_NO)
);

COMMENT ON COLUMN LEVELS.LEVEL_NO IS 'LV1 ~ LV30';
COMMENT ON COLUMN LEVELS.REQUIRED_TOTAL_EXP IS '레벨별 필요 누적 경험치';
COMMENT ON COLUMN LEVELS.TITLE IS '레벨별 타이틀';

--SELECT * FROM "LEVELS";
--SELECT SEQ_LEVEL_NO.NEXTVAL from dual; -- 시퀀스없으면 에러: ORA-02289: sequence does not exist
--DELETE FROM "LEVELS"; 
--DROP SEQUENCE SEQ_LEVEL_NO; 
-- 시퀀스 생성
--CREATE SEQUENCE SEQ_LEVEL_NO START WITH 1 NOCACHE;

-- MEMBER 테이블 생성
CREATE TABLE MEMBER (
    MEMBER_NO NUMBER NOT NULL,
    MEMBER_EMAIL VARCHAR2(30) NOT NULL,
    MEMBER_PW VARCHAR2(200),
    MEMBER_NAME VARCHAR2(30) NOT NULL,
    MEMBER_NICKNAME VARCHAR2(30) NOT NULL,
    MEMBER_TEL VARCHAR2(13) NOT NULL,
    MEMBER_CAREER VARCHAR2(50) NOT NULL,
    MEMBER_SUBSCRIBE CHAR(1) DEFAULT 'N' NOT NULL,
    MEMBER_ADMIN CHAR(1) DEFAULT 'N' NOT NULL,
    PROFILE_IMG VARCHAR2(300),
    MEMBER_DEL_FL CHAR(1) DEFAULT 'N' NOT NULL,
    M_CREATE_DATE DATE DEFAULT SYSDATE,
    SUBSCRIPTION_PRICE NUMBER DEFAULT 0 NOT NULL,
    MY_INFO_INTRO VARCHAR2(2000),
    MY_INFO_GIT VARCHAR2(200),
    MY_INFO_HOMEPAGE VARCHAR2(200),
    BEANS_AMOUNT NUMBER DEFAULT 0 NOT NULL,
    CURRENT_EXP NUMBER DEFAULT 0 NOT NULL,
    MEMBER_LEVEL NUMBER NOT NULL,
    CONSTRAINT PK_MEMBER PRIMARY KEY (MEMBER_NO),
    CONSTRAINT FK_LEVELS_TO_MEMBER FOREIGN KEY (MEMBER_LEVEL) REFERENCES LEVELS(LEVEL_NO),
    CONSTRAINT UK_MEMBER_EMAIL UNIQUE (MEMBER_EMAIL)
);
COMMENT ON COLUMN "MEMBER"."MEMBER_NO" IS '회원번호(SEQ_MEMBER_NO)';
COMMENT ON COLUMN "MEMBER"."MEMBER_EMAIL" IS '회원이메일(아이디)';
COMMENT ON COLUMN "MEMBER"."MEMBER_PW" IS '회원비밀번호';
COMMENT ON COLUMN "MEMBER"."MEMBER_NAME" IS '회원이름';
COMMENT ON COLUMN "MEMBER"."MEMBER_NICKNAME" IS '회원닉네임';
COMMENT ON COLUMN "MEMBER"."MEMBER_TEL" IS '회원전화번호';
COMMENT ON COLUMN "MEMBER"."MEMBER_CAREER" IS '회원경력사항';
COMMENT ON COLUMN "MEMBER"."MEMBER_SUBSCRIBE" IS '회원전용메일수신동의';
COMMENT ON COLUMN "MEMBER"."MEMBER_ADMIN" IS '관리자계정여부(Y:관리자, N:일반회원)';
COMMENT ON COLUMN "MEMBER"."PROFILE_IMG" IS '프로필 이미지';
COMMENT ON COLUMN "MEMBER"."MEMBER_DEL_FL" IS '회원탈퇴여부';
COMMENT ON COLUMN "MEMBER"."M_CREATE_DATE" IS '회원가입일';
COMMENT ON COLUMN "MEMBER"."SUBSCRIPTION_PRICE" IS '나를구독하면 지불해야할금액: 초기값0원';
COMMENT ON COLUMN "MEMBER"."MY_INFO_INTRO" IS '내 소개글';
COMMENT ON COLUMN "MEMBER"."MY_INFO_GIT" IS '깃허브 주소';
COMMENT ON COLUMN "MEMBER"."MY_INFO_HOMEPAGE" IS '노션, 포트폴리오 등 주소';
COMMENT ON COLUMN "MEMBER"."BEANS_AMOUNT" IS '커피콩지갑';
COMMENT ON COLUMN "MEMBER"."CURRENT_EXP" IS '회원 현재 경험치';
COMMENT ON COLUMN "MEMBER"."MEMBER_LEVEL" IS 'LV1 ~ LV30';


-- 시퀀스 생성
DROP SEQUENCE SEQ_MEMBER_NO; 
CREATE SEQUENCE SEQ_MEMBER_NO
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- AUTH 테이블 생성
CREATE TABLE AUTH (
    AUTH_NO NUMBER NOT NULL,
    CODE VARCHAR2(100) NOT NULL,
    EMAIL VARCHAR2(100) NOT NULL,
    CREATE_AT DATE DEFAULT SYSDATE NOT NULL,
    CONSTRAINT PK_AUTH PRIMARY KEY (AUTH_NO)
);
COMMENT ON COLUMN "AUTH"."AUTH_NO" IS '시퀀스번호';
COMMENT ON COLUMN "AUTH"."CODE" IS '인증키 코드';
COMMENT ON COLUMN "AUTH"."EMAIL" IS '이메일';
COMMENT ON COLUMN "AUTH"."CREATE_AT" IS '생성시간';

DROP SEQUENCE SEQ_AUTH_NO; 
CREATE SEQUENCE SEQ_AUTH_NO
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;


-- SOCIAL_LOGIN 테이블 생성
CREATE TABLE SOCIAL_LOGIN (
    SOCIAL_NO NUMBER NOT NULL,
    PROVIDER VARCHAR2(30) NOT NULL,
    PROVIDER_ID VARCHAR2(100) NOT NULL,
    MEMBER_NO NUMBER NOT NULL,
    CONSTRAINT PK_SOCIAL_LOGIN PRIMARY KEY (SOCIAL_NO),
    CONSTRAINT FK_MEMBER_TO_SOCIAL_LOGIN FOREIGN KEY (MEMBER_NO) REFERENCES MEMBER(MEMBER_NO),
    CONSTRAINT UK_SOCIAL_LOGIN UNIQUE (PROVIDER, PROVIDER_ID)
);

COMMENT ON COLUMN SOCIAL_LOGIN.SOCIAL_NO IS '시퀀스번호';
COMMENT ON COLUMN SOCIAL_LOGIN.PROVIDER IS 'KAKAO';
COMMENT ON COLUMN SOCIAL_LOGIN.PROVIDER_ID IS '식별 아이디';
COMMENT ON COLUMN SOCIAL_LOGIN.MEMBER_NO IS '회원번호(SEQ_MEMBER_NO)';

DROP SEQUENCE SEQ_SOCIAL_LOGIN_NO; 
CREATE SEQUENCE SEQ_SOCIAL_LOGIN_NO
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 확인
SELECT table_name FROM user_tables WHERE table_name = 'SOCIAL_LOGIN';
SELECT sequence_name FROM user_sequences WHERE sequence_name = 'SEQ_SOCIAL_LOGIN_NO';



-- ============================================
-- 자유게시판 테이블 생성 스크립트
-- 작성일: 2026-01-28
-- ============================================

-- 기존 테이블 삭제
DROP TABLE "COMMENT" CASCADE CONSTRAINTS;
DROP TABLE "BOARD_LIKE" CASCADE CONSTRAINTS;
DROP TABLE "BOARD_IMG" CASCADE CONSTRAINTS;
DROP TABLE "BOARD" CASCADE CONSTRAINTS;
DROP TABLE "BOARDTYPE" CASCADE CONSTRAINTS;

-- 시퀀스 삭제
DROP SEQUENCE SEQ_COMMENT_NO;
DROP SEQUENCE SEQ_BOARD_NO;
DROP SEQUENCE SEQ_IMAGE_NO;

-- ============================================
-- 1. BOARDTYPE
-- ============================================
CREATE TABLE "BOARDTYPE" (
    BOARD_CODE NUMBER NOT NULL,
    BOARD_NAME VARCHAR2(20) NOT NULL,
    PARENTS_BOARD_CODE NUMBER NULL,
    CONSTRAINT PK_BOARDTYPE PRIMARY KEY (BOARD_CODE),
    CONSTRAINT FK_BOARDTYPE_TO_BOARDTYPE FOREIGN KEY (PARENTS_BOARD_CODE) 
        REFERENCES BOARDTYPE(BOARD_CODE)
);

INSERT INTO BOARDTYPE VALUES (1, 'ITT', NULL);
INSERT INTO BOARDTYPE VALUES (2, 'IndustryNews', NULL);
INSERT INTO BOARDTYPE VALUES (3, '자유게시판', NULL);
INSERT INTO BOARDTYPE VALUES (4, 'FAQ', NULL);
COMMIT;

-- ============================================
-- 2. BOARD
-- ============================================
CREATE TABLE "BOARD" (
    BOARD_NO NUMBER NOT NULL,
    BOARD_TITLE VARCHAR2(300) NOT NULL,
    BOARD_CONTENT CLOB NOT NULL,
    B_CREATE_DATE DATE DEFAULT SYSDATE NOT NULL,
    B_UPDATE_DATE DATE NULL,
    BOARD_COUNT NUMBER DEFAULT 0 NOT NULL,
    BOARD_DEL_FL CHAR(1) DEFAULT 'N' NOT NULL,
    BOARD_CODE NUMBER NOT NULL,
    MEMBER_NO NUMBER NOT NULL,
    NEWS_REPORTER VARCHAR2(100) NULL,
    CONSTRAINT PK_BOARD PRIMARY KEY (BOARD_NO),
    CONSTRAINT FK_BOARDTYPE_TO_BOARD FOREIGN KEY (BOARD_CODE) REFERENCES BOARDTYPE(BOARD_CODE),
    CONSTRAINT FK_MEMBER_TO_BOARD FOREIGN KEY (MEMBER_NO) REFERENCES MEMBER(MEMBER_NO),
    CONSTRAINT CHK_BOARD_DEL_FL CHECK (BOARD_DEL_FL IN ('Y', 'N'))
);

CREATE SEQUENCE SEQ_BOARD_NO START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;
CREATE INDEX IDX_BOARD_CODE ON BOARD(BOARD_CODE); -- B-Tree 인덱스 생성: 게시판별 글을 빠르게 조회하기 위해 미리 만들어 둔 검색용 목차
CREATE INDEX IDX_BOARD_MEMBER ON BOARD(MEMBER_NO);
CREATE INDEX IDX_BOARD_DATE ON BOARD(B_CREATE_DATE DESC);

-- ============================================
-- 3. BOARD_IMG
-- ============================================
CREATE TABLE "BOARD_IMG" (
    IMG_NO NUMBER NOT NULL,
    IMG_PATH VARCHAR2(500) NOT NULL,
    IMG_ORIG VARCHAR2(200) NULL,
    IMG_RENAME VARCHAR2(200) NULL,
    IMG_ORDER NUMBER NOT NULL,
    BOARD_NO NUMBER NOT NULL,
    CONSTRAINT PK_BOARD_IMG PRIMARY KEY (IMG_NO),
    CONSTRAINT FK_BOARD_TO_BOARD_IMG FOREIGN KEY (BOARD_NO) REFERENCES BOARD(BOARD_NO) ON DELETE CASCADE
);

CREATE SEQUENCE SEQ_IMAGE_NO START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;

-- ============================================
-- 4. BOARD_LIKE
-- ============================================
CREATE TABLE "BOARD_LIKE" (
    BOARD_NO NUMBER NOT NULL,
    MEMBER_NO NUMBER NOT NULL,
    CONSTRAINT PK_BOARD_LIKE PRIMARY KEY (BOARD_NO, MEMBER_NO),
    CONSTRAINT FK_BOARD_TO_BOARD_LIKE FOREIGN KEY (BOARD_NO) REFERENCES BOARD(BOARD_NO) ON DELETE CASCADE,
    CONSTRAINT FK_MEMBER_TO_BOARD_LIKE FOREIGN KEY (MEMBER_NO) REFERENCES MEMBER(MEMBER_NO) ON DELETE CASCADE
);

-- ============================================
-- 5. COMMENTS
-- ============================================
CREATE TABLE COMMENTS (
    COMMENT_NO NUMBER NOT NULL,
    MEMBER_NO NUMBER NOT NULL,
    BOARD_NO NUMBER NOT NULL,
    PARENTS_COMMENT_NO NUMBER NULL,
    C_CREATE_DATE DATE DEFAULT SYSDATE NOT NULL,
    COMMENT_CONTENT VARCHAR2(2000) NOT NULL,
    COMMENT_DEL_FL CHAR(1) DEFAULT 'N' NOT NULL,
    SECRET_YN CHAR(1) DEFAULT 'N' NOT NULL,
    MODIFY_YN CHAR(1) DEFAULT 'N' NOT NULL,
    CONSTRAINT PK_COMMENT PRIMARY KEY (COMMENT_NO),
    CONSTRAINT FK_MEMBER_TO_COMMENT FOREIGN KEY (MEMBER_NO) REFERENCES MEMBER(MEMBER_NO),
    CONSTRAINT FK_BOARD_TO_COMMENT FOREIGN KEY (BOARD_NO) REFERENCES BOARD(BOARD_NO) ON DELETE CASCADE,
    CONSTRAINT FK_COMMENT_TO_COMMENT FOREIGN KEY (PARENTS_COMMENT_NO) REFERENCES COMMENTS(COMMENT_NO),
    CONSTRAINT CHK_COMMENT_DEL_FL CHECK (COMMENT_DEL_FL IN ('Y', 'N')),
    CONSTRAINT CHK_SECRET_YN CHECK (SECRET_YN IN ('Y', 'N')),
    CONSTRAINT CHK_MODIFY_YN CHECK (MODIFY_YN IN ('Y', 'N'))
);

CREATE SEQUENCE SEQ_COMMENT_NO START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;
CREATE INDEX IDX_COMMENT_BOARD ON COMMENTS(BOARD_NO);

COMMIT;


-- ============================================
-- AI 챗봇 테이블 생성 스크립트
-- Description: CB_SESSION, CB_TOKEN_USAGE 테이블 생성
-- ============================================

-- 기존 테이블 삭제 (재생성용)
DROP TABLE CB_TOKEN_USAGE CASCADE CONSTRAINTS;
DROP TABLE CB_SESSION CASCADE CONSTRAINTS;

-- ============================================
-- CB_SESSION 테이블 생성 (챗봇 세션)
-- ============================================
CREATE TABLE CB_SESSION (
   CB_SESSION_ID    NUMBER          NOT NULL,
   STARTED_AT       DATE            DEFAULT SYSDATE NULL,
   ENDED_AT         DATE            NULL,
   CB_SESSION_TYPE  VARCHAR2(50)    NOT NULL,
   CB_BOARD_TYPE    VARCHAR2(100)   NOT NULL,
   MEMBER_NO        NUMBER          NOT NULL,
   BOARD_NO         NUMBER          NULL
);

-- 컬럼 코멘트
COMMENT ON COLUMN CB_SESSION.CB_SESSION_ID IS '챗봇세션식별자(SEQ_CB_SESSION_NO)';
COMMENT ON COLUMN CB_SESSION.STARTED_AT IS '챗봇팝업시작시간';
COMMENT ON COLUMN CB_SESSION.ENDED_AT IS '챗봇팝업마침시간';
COMMENT ON COLUMN CB_SESSION.CB_SESSION_TYPE IS '챗봇세션유형(BASIC 기본형, KONG 커피콩충전형)';
COMMENT ON COLUMN CB_SESSION.CB_BOARD_TYPE IS '게시글유형(INSERT 또는 UPDATE)';
COMMENT ON COLUMN CB_SESSION.MEMBER_NO IS '회원번호(SEQ_MEMBER_NO)';
COMMENT ON COLUMN CB_SESSION.BOARD_NO IS '게시글번호(글쓰기:NULL, 글수정:BOARD_NO)';

-- PK 제약조건
ALTER TABLE CB_SESSION ADD CONSTRAINT PK_CB_SESSION 
    PRIMARY KEY (CB_SESSION_ID);

-- FK 제약조건
ALTER TABLE CB_SESSION ADD CONSTRAINT FK_MEMBER_TO_CB_SESSION_1 
    FOREIGN KEY (MEMBER_NO) REFERENCES MEMBER (MEMBER_NO);

ALTER TABLE CB_SESSION ADD CONSTRAINT FK_BOARD_TO_CB_SESSION_1 
    FOREIGN KEY (BOARD_NO) REFERENCES BOARD (BOARD_NO);

-- ============================================
-- CB_TOKEN_USAGE 테이블 생성 (토큰 사용 내역)
-- ============================================
CREATE TABLE CB_TOKEN_USAGE (
   TK_USAGE_ID      NUMBER      NOT NULL,
   PROMPT_TEXT      CLOB        NULL,
   ANSWER_TEXT      CLOB        NULL,
   PROMPT_TOKENS    NUMBER      NOT NULL,
   ANSWER_TOKENS    NUMBER      NOT NULL,
   TOTAL_TOKENS     NUMBER      NOT NULL,
   BEAN_SWE         NUMBER      NULL,
   MODEL_NAME       VARCHAR2(50) NULL,
   MEMBER_NO        NUMBER      NOT NULL,
   CB_SESSION_ID    NUMBER      NOT NULL
);

-- 컬럼 코멘트
COMMENT ON COLUMN CB_TOKEN_USAGE.TK_USAGE_ID IS '토큰사용이력식별자(SEQ_TOKEN_USAGE_NO)';
COMMENT ON COLUMN CB_TOKEN_USAGE.PROMPT_TEXT IS '사용자질문내용';
COMMENT ON COLUMN CB_TOKEN_USAGE.ANSWER_TEXT IS '챗봇대답내용';
COMMENT ON COLUMN CB_TOKEN_USAGE.PROMPT_TOKENS IS '사용자질문토큰수';
COMMENT ON COLUMN CB_TOKEN_USAGE.ANSWER_TOKENS IS '챗봇대답토큰수';
COMMENT ON COLUMN CB_TOKEN_USAGE.TOTAL_TOKENS IS '전체토큰수(/세션)';
COMMENT ON COLUMN CB_TOKEN_USAGE.BEAN_SWE IS '과금커피콩포인트SWEngineering';
COMMENT ON COLUMN CB_TOKEN_USAGE.MODEL_NAME IS '챗봇이름(GPT-4o-mini)';
COMMENT ON COLUMN CB_TOKEN_USAGE.MEMBER_NO IS '회원번호(SEQ_MEMBER_NO)';
COMMENT ON COLUMN CB_TOKEN_USAGE.CB_SESSION_ID IS '챗봇세션식별자(SEQ_CB_SESSION_NO)';

-- PK 제약조건
ALTER TABLE CB_TOKEN_USAGE ADD CONSTRAINT PK_CB_TOKEN_USAGE 
    PRIMARY KEY (TK_USAGE_ID);

-- FK 제약조건
ALTER TABLE CB_TOKEN_USAGE ADD CONSTRAINT FK_MEMBER_TO_CB_TOKEN_USAGE_1 
    FOREIGN KEY (MEMBER_NO) REFERENCES MEMBER (MEMBER_NO);

ALTER TABLE CB_TOKEN_USAGE ADD CONSTRAINT FK_CB_SESSION_TO_CB_TOKEN_USAGE_1 
    FOREIGN KEY (CB_SESSION_ID) REFERENCES CB_SESSION (CB_SESSION_ID);

-- ============================================
-- 시퀀스 생성
-- ============================================
-- 시퀀스 삭제 (재생성용)
DROP SEQUENCE SEQ_TOKEN_USAGE_NO;
DROP SEQUENCE SEQ_CB_SESSION_NO;

CREATE SEQUENCE SEQ_CB_SESSION_NO
START WITH 1
INCREMENT BY 1
NOCACHE;

CREATE SEQUENCE SEQ_TOKEN_USAGE_NO
START WITH 1
INCREMENT BY 1
NOCACHE;

-- ============================================
-- 인덱스 생성 (성능 최적화)
-- ============================================
-- 세션별 토큰 사용 내역 조회용
CREATE INDEX IDX_TOKEN_USAGE_SESSION ON CB_TOKEN_USAGE(CB_SESSION_ID);

-- 회원별 토큰 사용 내역 조회용
CREATE INDEX IDX_TOKEN_USAGE_MEMBER ON CB_TOKEN_USAGE(MEMBER_NO);

-- 회원별 세션 조회용
CREATE INDEX IDX_CB_SESSION_MEMBER ON CB_SESSION(MEMBER_NO);

-- 게시글별 세션 조회용 (nullable이지만 인덱스 생성 가능)
CREATE INDEX IDX_CB_SESSION_BOARD ON CB_SESSION(BOARD_NO);

-- 세션 타입별 조회용
CREATE INDEX IDX_CB_SESSION_TYPE ON CB_SESSION(CB_SESSION_TYPE);

COMMIT;

-- ============================================
-- 확인 쿼리
-- ============================================
SELECT 'CB_SESSION 테이블 생성 완료' AS status FROM dual;
SELECT 'CB_TOKEN_USAGE 테이블 생성 완료' AS status FROM dual;
SELECT 'SEQ_CB_SESSION_NO, SEQ_TOKEN_USAGE_NO 시퀀스 생성 완료' AS status FROM dual;




-------------------------------------------------------------------------------
------------ 더미데이터 삽입 ---------------------------------------------------
-------------------------------------------------------------------------------
-- 기본 레벨 데이터 삽입
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (1,   0,     '초보자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (2,   100,   '견습 개발자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (3,   300,   '연습생');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (4,   600,   '신입 개발자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (5,   1000,  '튜토리얼 완료');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (6,   1500,  '초급 개발자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (7,   2100,  '기능 사용자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (8,   2800,  '로직 사용자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (9,   3600,  '문제 해결가');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (10,  4500,  '주니어 개발자');

INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (11,  5500,  '숙련자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (12,  6600,  '기능 숙련자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (13,  7800,  '코드 숙련자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (14,  9100,  '실전 숙련자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (15, 10500,  '실무 숙련자');

INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (16, 12000,  '중급 개발자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (17, 13600,  '설계 참여자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (18, 15300,  '안정성 담당');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (19, 17100,  '품질 담당');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (20, 19000,  '베테랑 개발자');

INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (21, 21000,  '고급 개발자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (22, 23100,  '시스템 전문가');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (23, 25300,  '문제 해결 전문가');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (24, 27600,  '핵심 멤버');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (25, 30000,  '시니어 개발자');

INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (26, 32500,  '마스터');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (27, 35100,  '그랜드 마스터');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (28, 37800,  '전설의 개발자');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (29, 40600,  '서버 네임드');
INSERT INTO LEVELS (LEVEL_NO, REQUIRED_TOTAL_EXP, TITLE) VALUES (30, 43500,  '레전드');

COMMIT;

-- =========================================================================
-- 회원 더미데이터 
INSERT INTO MEMBER VALUES (
  0,'admin@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '관리자','Administrator','0101000001','전설',
  'N','Y','/images/board/freeboard/chatbot5.png','N',SYSDATE,
  0,NULL,NULL,NULL,
  10000000,100000,30
);
INSERT INTO MEMBER VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user01@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '김도현','NullMaster','0101000001','웹백엔드 개발자 1년차',
  'N','N','/images/board/freeboard/images_cat02.jpg','N',SYSDATE,
  0,NULL,NULL,NULL,
  1000,0,1
);

INSERT INTO MEMBER  VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user02@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '이서연','버그헌터','0101000002','프론트엔드 개발자 6개월',
  'N','N','/images/board/freeboard/cat1.jpg','N',SYSDATE,
  0,NULL,NULL,NULL,
  0,0,1
);

INSERT INTO MEMBER  VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user03@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '박지훈','코딩하는곰','0101000003','풀스택 개발자 2년차',
  'N','N','/images/board/freeboard/dog3.jpg','N',SYSDATE,
  0,NULL,NULL,NULL,
  30,0,1
);

INSERT INTO MEMBER  VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user04@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '최민재','SQL마법사','0101000004','DBA/데이터엔지니어 3년차',
  'N','N','/images/board/freeboard/flower1.jpg','N',SYSDATE,
  0,NULL,NULL,NULL,
  100,0,1
);

INSERT INTO MEMBER  VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user05@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '정윤호','디버깅중독','0101000005','백엔드 개발자 1년차(Spring)',
  'N','N','/images/board/freeboard/tiger01.jpg','N',SYSDATE,
  0,NULL,NULL,NULL,
  100,0,1
);

INSERT INTO MEMBER  VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user06@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '한지수','콘솔로그장인','0101000006','프론트엔드 개발자 2년차(React)',
  'N','N','/images/board/freeboard/fbComment_img1.png','N',SYSDATE,
  0,NULL,NULL,NULL,
  100,0,1
);

INSERT INTO MEMBER  VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user07@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '오현우','에러수집가','0101000007','QA 엔지니어 1년차(테스트 자동화)',
  'N','N','/images/board/freeboard/fbComment_img2.png','N',SYSDATE,
  0,NULL,NULL,NULL,
  100,0,1);

INSERT INTO MEMBER  VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user08@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '유채원','주석요정','0101000008','웹퍼블리셔 8개월(접근성/반응형)',
  'N','N',NULL,'N',SYSDATE,
  0,NULL,NULL,NULL,
  100,0,1
);

INSERT INTO MEMBER  VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user09@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '강민수','메모리도둑','0101000009','시스템 엔지니어 4년차(Linux/네트워크)',
  'N','N',NULL,'N',SYSDATE,
  0,NULL,NULL,NULL,
  100,0,1
);

INSERT INTO MEMBER  VALUES (
  SEQ_MEMBER_NO.NEXTVAL,'user10@joboju.com','$2a$10$XVUq9irjRcTuzgfvXeq9HuFdZf4RAJvcGQVj1Qzc20BD/ShnF0o7u',
  '신예린','리팩터여신','0101000010','풀스택 개발자 3년차(Java+JS)',
  'N','N',NULL,'N',SYSDATE,
  0,NULL,NULL,NULL,
  100,0,1
);


COMMIT;

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-- q'[...]' 는 Oracle이 절대 바인드로 오해하지 않는 문자열 표기법 (ORA-17041방지)
SET DEFINE OFF;
SET SERVEROUTPUT ON;

DECLARE
BEGIN
   FOR i IN 1..10 LOOP

      INSERT INTO BOARD (
         BOARD_NO,
         BOARD_TITLE,
         BOARD_CONTENT,
         B_CREATE_DATE,
         B_UPDATE_DATE,
         BOARD_COUNT,
         BOARD_DEL_FL,
         BOARD_CODE,
         MEMBER_NO,
         NEWS_REPORTER
      )
      VALUES (
         SEQ_BOARD_NO.NEXTVAL,

         /* 제목 */
         CASE i
            WHEN 1 THEN q'[요즘 개발 동기부여 어떻게 하고 계세요?]'
            WHEN 2 THEN q'[내가 만든 기능이 드디어 실서비스에 반영됐다!]'
            WHEN 3 THEN q'[개발하다가 만난 가장 황당한 버그]'
            WHEN 4 THEN q'[요새 핫한 신기술, 뭐 써보셨나요?]'
            WHEN 5 THEN q'[퇴근 후 코딩 다들 어떻게 집중하시나요?]'
            WHEN 6 THEN q'[개발자 블로그 개편 중인데 피드백 환영!]'
            WHEN 7 THEN q'[사이드 프로젝트 팀원을 모으는 게 어렵네요]'
            WHEN 8 THEN q'[요즘 개발하면서 배운 가장 큰 교훈]'
            WHEN 9 THEN q'[개발자 노트북 추천 부탁드립니다]'
            WHEN 10 THEN q'[새로운 언어 공부 어떻게 시작하세요?]'
         END,

         /* 내용 */
         CASE i
            WHEN 1 THEN q'[최근 들어 사이드 프로젝트가 예전만큼 속도가 나지 않아서 여러 가지 동기부여 방법을 시도하고 있어요. 운동을 하면서 리프레시도 해보고, 개발 공부 라이브 스트리밍을 켜놓고 따라 해보기도 했는데 꾸준한 루틴을 만드는 게 제일 어렵더라고요. 특히 퇴근 후 약간의 피로감이 몰려올 때는 ‘오늘은 그냥 쉬자’라는 유혹이 엄청 쎄요. 그래도 작은 목표라도 하나씩 달성하면 다시 동력이 생기더라고요. 여러분은 어떤 방식으로 꾸준함을 유지하고, 다시 동기부여를 얻고 계신가요? 서로의 방법을 공유하면 도움이 될 것 같아요!]'
            WHEN 2 THEN q'[몇 주 동안 밤늦게까지 붙잡고 있던 기능이 오늘 드디어 실서비스에 반영됐습니다. 배포 버튼을 누르는 순간 손이 떨릴 정도로 긴장됐고, 모니터링 페이지를 켜놓고 로그가 정상적으로 돌아가는지 계속 들여다보고 있어요. 사용자 반응이 어떤지 너무 궁금해서 주기적으로 댓글도 확인하게 되네요. 아직 버그가 없다고 확신할 수는 없지만, 그래도 내가 만든 것이 실제로 세상에 나왔다는 사실만으로도 정말 뿌듯합니다. 여러분은 첫 배포 때 어떤 느낌이었나요? 혹은 지금도 배포할 때마다 떨리나요?]'
            WHEN 3 THEN q'[오늘 코드 한 줄이 왜 돌아가지 않는지 3시간 동안 머리를 싸매고 고민했는데, 알고 보니 정말 아무것도 아닌 세미콜론 하나가 문제였어요. 그동안 복잡한 로직이나 구조적인 문제라고 생각해서 별 짓을 다 했는데, 마지막에 단순한 문법 오류였다는 걸 깨달았을 때 허탈함과 웃음이 동시에 나오더라고요. 이런 사소한 버그 때문에 시간을 날릴 때가 한두 번이 아니라서 점점 디버깅 패턴도 바뀌는 것 같아요. 여러분도 이런 황당한 경험 있으신가요? 서로 공유하면 위로가 될 것 같아요.]'
            WHEN 4 THEN q'[최근에는 AI와 관련된 새로운 라이브러리들을 이것저것 만져보고 있는데, 아직은 활용 범위가 애매해도 실험하는 과정 자체가 꽤 재미있더라고요. 특히 작은 기능 하나도 모델을 활용해서 자동화해보거나 실시간 분석 기능을 붙여보는 과정에서 다양한 아이디어가 떠오릅니다. 물론 실제 업무에 도입하기엔 여러 제약과 검토해야 할 부분이 많지만, 미래에는 분명히 중요한 기술이 될 거라고 느끼고 있어요. 여러분은 최근에 어떤 신기술이나 툴을 써보셨나요? 추천할 만한 것이 있으면 공유해 주세요!]'
            WHEN 5 THEN q'[퇴근하고 집에 오면 머리가 멍해져서 아무것도 하기 싫은데, 막상 코딩을 시작하면 또 몰입하게 되더라고요. 그래서 집중력을 끌어올리기 위한 여러 루틴을 시험해보고 있어요. 커피를 한 잔 마시거나, 좋아하는 음악을 틀어놓거나, 혹은 잠깐 산책을 하고 나서 시작하면 그나마 도움이 되더라고요. 그래도 '꾸준함'이라는 벽을 넘는 건 쉽지 않습니다. 여러분은 퇴근 후 자기계발이나 개발 공부를 할 때 어떤 방식으로 집중 모드를 만들고 유지하시나요? 팁을 공유해주시면 감사하겠습니다!.]'
            WHEN 6 THEN q'[최근 블로그를 전체적으로 개편하고 있는데, 디자인 감각이 뛰어난 편이 아니라 UI를 바꿀 때마다 스스로 '이게 맞나?'라는 의문이 들곤 합니다. 새로운 테마를 적용하고 색상 조합도 바꿔봤지만 마음에 들었다가도 금방 어색해 보이더라고요. 특히 모바일 환경에서 보이는 디테일들이 신경 쓰여서 이것저것 테스트하느라 시간이 꽤 걸리고 있습니다. 혹시 방문해서 어색한 부분이나 개선했으면 하는 점이 있으면 편하게 알려주세요. 실제 사용자 의견이 제일 큰 도움이 되는 것 같아요.]'
            WHEN 7 THEN q'[처음에는 열정 넘치는 개발자들과 함께 재미있게 진행해보려고 했는데, 막상 팀을 꾸려보니 일정 조율이나 업무 스타일 차이로 인해 쉽게 진행되지 않더라고요. 서로 좋은 의도였지만 프로젝트에 대한 기대나 목표가 조금씩 달라 조율하는 데 어려움을 겪기도 했어요. 그래도 잘 맞는 팀원을 만날 수 있다면 훨씬 재밌고 빠르게 성장할 수 있다는 생각이 들어 계속 도전하고 있습니다. 혹시 여러분은 팀원을 모집할 때 어떤 기준이나 방법을 활용하시나요? 경험담도 환영이에요!]'
            WHEN 8 THEN q'[최근 프로젝트를 진행하면서 기술적인 문제보다 소통의 중요성을 더 크게 느끼고 있어요. 서로 같은 내용을 이해했다고 생각했지만, 막상 결과물을 보면 완전히 다르게 구현되어 있거나, 일정에 대한 기대치가 서로 달라 오해가 생기기도 했거든요. 그래서 문서화나 회의 후 기록을 남기는 습관을 다시 강화하고 있습니다. 제대로 소통되지 않으면 기술력만으로는 해결할 수 없는 문제가 많더라고요. 여러분은 최근에 어떤 교훈을 얻으셨나요? 함께 공유하면 좋을 것 같아요!]'
            WHEN 9 THEN q'[노트북을 바꾸려고 알아보고 있는데, 요즘은 선택지가 너무 많아서 오히려 결정하기가 더 어려운 것 같아요. 맥북 M 시리즈는 성능과 배터리가 워낙 좋다고 들었고, 반대로 고성능 윈도우 랩탑은 개발환경을 다양하게 구성하기 좋아 보여서 계속 망설여지고 있어요. 또한 이동이 많은 편이라 무게도 신경 쓰이고, 동시에 빌드 시간이 빠른 것도 중요하다 보니 우선순위를 어디에 둘지 혼란스럽습니다. 실제로 사용해본 경험이 있다면 추천 부탁드려요. 참고하면 큰 도움이 될 것 같아요!]'
            WHEN 10 THEN q'[새로운 언어를 공부하고 있는데 문법만 훑어본 상태에서는 실제 프로젝트에 적용하려니 막막함이 크게 느껴지더라고요. 공식 문서를 정독하는 게 좋은지, 튜토리얼 영상을 따라가며 코드를 직접 실행해보는 게 나은지 고민 중입니다. 일단 간단한 토이 프로젝트를 만들어 보려고 하는데, 역시 익숙하지 않은 언어로 구조를 잡는 건 쉽지 않네요. 여러분은 새로운 언어를 배울 때 어떤 접근 방식을 사용하시나요? 효과적인 루틴이 있다면 꼭 공유해주세요!]'
         END
         || CHR(10) || q'[사진 첨부했습니다.]',

         SYSDATE - TRUNC(DBMS_RANDOM.VALUE(10, 20)),
         SYSDATE - TRUNC(DBMS_RANDOM.VALUE(0, 10)),
         TRUNC(DBMS_RANDOM.VALUE(10, 200)),
         'N',
         3,
         TRUNC(DBMS_RANDOM.VALUE(1, 6)),
         NULL
      );

      INSERT INTO BOARD_IMG (
         IMG_NO,
         IMG_PATH,
         IMG_ORIG,
         IMG_RENAME,
         IMG_ORDER,
         BOARD_NO
      )
      VALUES (
         SEQ_IMAGE_NO.NEXTVAL,
         '/images/board/freeboard/',
         'fbList_img' || i || '.png',
         'fbList_img' || i || '.png',
         0,
         SEQ_BOARD_NO.CURRVAL
      );

   END LOOP;

   COMMIT;
END;
/


COMMIT;

-- 댓글/대댓글 더미 데이터 스크립트 (5개): 
--

SET DEFINE OFF;

DECLARE
    v_board_no NUMBER := 7; -- 댓글을 달 게시글 번호
    v_parent_comment_no NUMBER;
BEGIN
    /* ===============================
       부모 댓글 1 by memberNo=6, 묘소연
    =============================== */
    INSERT INTO COMMENTS (
        COMMENT_NO,
        MEMBER_NO,
        BOARD_NO,
        PARENTS_COMMENT_NO,
        C_CREATE_DATE,
        COMMENT_CONTENT,
        COMMENT_DEL_FL,
        SECRET_YN,
        MODIFY_YN
    ) VALUES (
        SEQ_COMMENT_NO.NEXTVAL,
        6,
        v_board_no,
        NULL,
        SYSDATE - 3,
        q'[글 잘 봤습니다. ^^]',
        'N',
        'N',
        'N'
    );

    v_parent_comment_no := SEQ_COMMENT_NO.CURRVAL;

    /* ===============================
       부모 댓글 2 by memberNo=7, 줌-옹
    =============================== */
    INSERT INTO COMMENTS (
        COMMENT_NO,
        MEMBER_NO,
        BOARD_NO,
        PARENTS_COMMENT_NO,
        C_CREATE_DATE,
        COMMENT_CONTENT,
        COMMENT_DEL_FL,
        SECRET_YN,
        MODIFY_YN
    ) VALUES (
        SEQ_COMMENT_NO.NEXTVAL,
        7,
        v_board_no,
        NULL,
        SYSDATE - 1,
        q'[글 잘 봤습니다. ^^]',
        'N',
        'N',
        'N'
    );

    COMMIT;
END;
/



-------------------------------------------------------
-- 1. 자유게시판 게시글 & 이미지 좀더 추가 ~up to 100개: 
-- q'[...]' 는 Oracle이 절대 바인드로 오해하지 않는 문자열 표기법 (ORA-17041방지)
SET DEFINE OFF;
SET SERVEROUTPUT ON;

DECLARE
BEGIN
   -- 10개 세트를 10번 반복 → 총 100개 추
   FOR repeat_cnt IN 1..9 LOOP	
	   FOR inner_cnt IN 1..10 LOOP

		  INSERT INTO BOARD (
		     BOARD_NO,
		     BOARD_TITLE,
		     BOARD_CONTENT,
		     B_CREATE_DATE,
		     B_UPDATE_DATE,
		     BOARD_COUNT,
		     BOARD_DEL_FL,
		     BOARD_CODE,
		     MEMBER_NO,
		     NEWS_REPORTER
		  )
		  VALUES (
		     SEQ_BOARD_NO.NEXTVAL,

		     /* 제목 (반복 회차 붙이기) */
		     CASE inner_cnt
		        WHEN 1 THEN q'[요즘 개발 동기부여 어떻게 하고 계세요?]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		        WHEN 2 THEN q'[내가 만든 기능이 드디어 실서비스에 반영됐다!]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		        WHEN 3 THEN q'[개발하다가 만난 가장 황당한 버그]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		        WHEN 4 THEN q'[요새 핫한 신기술, 뭐 써보셨나요?]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		        WHEN 5 THEN q'[퇴근 후 코딩 다들 어떻게 집중하시나요?]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		        WHEN 6 THEN q'[개발자 블로그 개편 중인데 피드백 환영!]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		        WHEN 7 THEN q'[사이드 프로젝트 팀원을 모으는 게 어렵네요]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		        WHEN 8 THEN q'[요즘 개발하면서 배운 가장 큰 교훈]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		        WHEN 9 THEN q'[개발자 노트북 추천 부탁드립니다]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		        WHEN 10 THEN q'[새로운 언어 공부 어떻게 시작하세요?]'
		        			|| ' (' || repeat_cnt || ', ' || inner_cnt || ')'
		     END,
		     

		     /* 내용 */
		     CASE inner_cnt
		        WHEN 1 THEN q'[최근 들어 사이드 프로젝트가 예전만큼 속도가 나지 않아서 여러 가지 동기부여 방법을 시도하고 있어요. 운동을 하면서 리프레시도 해보고, 개발 공부 라이브 스트리밍을 켜놓고 따라 해보기도 했는데 꾸준한 루틴을 만드는 게 제일 어렵더라고요. 특히 퇴근 후 약간의 피로감이 몰려올 때는 ‘오늘은 그냥 쉬자’라는 유혹이 엄청 쎄요. 그래도 작은 목표라도 하나씩 달성하면 다시 동력이 생기더라고요. 여러분은 어떤 방식으로 꾸준함을 유지하고, 다시 동기부여를 얻고 계신가요? 서로의 방법을 공유하면 도움이 될 것 같아요!]'
		        WHEN 2 THEN q'[몇 주 동안 밤늦게까지 붙잡고 있던 기능이 오늘 드디어 실서비스에 반영됐습니다. 배포 버튼을 누르는 순간 손이 떨릴 정도로 긴장됐고, 모니터링 페이지를 켜놓고 로그가 정상적으로 돌아가는지 계속 들여다보고 있어요. 사용자 반응이 어떤지 너무 궁금해서 주기적으로 댓글도 확인하게 되네요. 아직 버그가 없다고 확신할 수는 없지만, 그래도 내가 만든 것이 실제로 세상에 나왔다는 사실만으로도 정말 뿌듯합니다. 여러분은 첫 배포 때 어떤 느낌이었나요? 혹은 지금도 배포할 때마다 떨리나요?]'
		        WHEN 3 THEN q'[오늘 코드 한 줄이 왜 돌아가지 않는지 3시간 동안 머리를 싸매고 고민했는데, 알고 보니 정말 아무것도 아닌 세미콜론 하나가 문제였어요. 그동안 복잡한 로직이나 구조적인 문제라고 생각해서 별 짓을 다 했는데, 마지막에 단순한 문법 오류였다는 걸 깨달았을 때 허탈함과 웃음이 동시에 나오더라고요. 이런 사소한 버그 때문에 시간을 날릴 때가 한두 번이 아니라서 점점 디버깅 패턴도 바뀌는 것 같아요. 여러분도 이런 황당한 경험 있으신가요? 서로 공유하면 위로가 될 것 같아요.]'
		        WHEN 4 THEN q'[최근에는 AI와 관련된 새로운 라이브러리들을 이것저것 만져보고 있는데, 아직은 활용 범위가 애매해도 실험하는 과정 자체가 꽤 재미있더라고요. 특히 작은 기능 하나도 모델을 활용해서 자동화해보거나 실시간 분석 기능을 붙여보는 과정에서 다양한 아이디어가 떠오릅니다. 물론 실제 업무에 도입하기엔 여러 제약과 검토해야 할 부분이 많지만, 미래에는 분명히 중요한 기술이 될 거라고 느끼고 있어요. 여러분은 최근에 어떤 신기술이나 툴을 써보셨나요? 추천할 만한 것이 있으면 공유해 주세요!]'
		        WHEN 5 THEN q'[퇴근하고 집에 오면 머리가 멍해져서 아무것도 하기 싫은데, 막상 코딩을 시작하면 또 몰입하게 되더라고요. 그래서 집중력을 끌어올리기 위한 여러 루틴을 시험해보고 있어요. 커피를 한 잔 마시거나, 좋아하는 음악을 틀어놓거나, 혹은 잠깐 산책을 하고 나서 시작하면 그나마 도움이 되더라고요. 그래도 '꾸준함'이라는 벽을 넘는 건 쉽지 않습니다. 여러분은 퇴근 후 자기계발이나 개발 공부를 할 때 어떤 방식으로 집중 모드를 만들고 유지하시나요? 팁을 공유해주시면 감사하겠습니다!.]'
		        WHEN 6 THEN q'[최근 블로그를 전체적으로 개편하고 있는데, 디자인 감각이 뛰어난 편이 아니라 UI를 바꿀 때마다 스스로 '이게 맞나?'라는 의문이 들곤 합니다. 새로운 테마를 적용하고 색상 조합도 바꿔봤지만 마음에 들었다가도 금방 어색해 보이더라고요. 특히 모바일 환경에서 보이는 디테일들이 신경 쓰여서 이것저것 테스트하느라 시간이 꽤 걸리고 있습니다. 혹시 방문해서 어색한 부분이나 개선했으면 하는 점이 있으면 편하게 알려주세요. 실제 사용자 의견이 제일 큰 도움이 되는 것 같아요.]'
		        WHEN 7 THEN q'[처음에는 열정 넘치는 개발자들과 함께 재미있게 진행해보려고 했는데, 막상 팀을 꾸려보니 일정 조율이나 업무 스타일 차이로 인해 쉽게 진행되지 않더라고요. 서로 좋은 의도였지만 프로젝트에 대한 기대나 목표가 조금씩 달라 조율하는 데 어려움을 겪기도 했어요. 그래도 잘 맞는 팀원을 만날 수 있다면 훨씬 재밌고 빠르게 성장할 수 있다는 생각이 들어 계속 도전하고 있습니다. 혹시 여러분은 팀원을 모집할 때 어떤 기준이나 방법을 활용하시나요? 경험담도 환영이에요!]'
		        WHEN 8 THEN q'[최근 프로젝트를 진행하면서 기술적인 문제보다 소통의 중요성을 더 크게 느끼고 있어요. 서로 같은 내용을 이해했다고 생각했지만, 막상 결과물을 보면 완전히 다르게 구현되어 있거나, 일정에 대한 기대치가 서로 달라 오해가 생기기도 했거든요. 그래서 문서화나 회의 후 기록을 남기는 습관을 다시 강화하고 있습니다. 제대로 소통되지 않으면 기술력만으로는 해결할 수 없는 문제가 많더라고요. 여러분은 최근에 어떤 교훈을 얻으셨나요? 함께 공유하면 좋을 것 같아요!]'
		        WHEN 9 THEN q'[노트북을 바꾸려고 알아보고 있는데, 요즘은 선택지가 너무 많아서 오히려 결정하기가 더 어려운 것 같아요. 맥북 M 시리즈는 성능과 배터리가 워낙 좋다고 들었고, 반대로 고성능 윈도우 랩탑은 개발환경을 다양하게 구성하기 좋아 보여서 계속 망설여지고 있어요. 또한 이동이 많은 편이라 무게도 신경 쓰이고, 동시에 빌드 시간이 빠른 것도 중요하다 보니 우선순위를 어디에 둘지 혼란스럽습니다. 실제로 사용해본 경험이 있다면 추천 부탁드려요. 참고하면 큰 도움이 될 것 같아요!]'
		        WHEN 10 THEN q'[새로운 언어를 공부하고 있는데 문법만 훑어본 상태에서는 실제 프로젝트에 적용하려니 막막함이 크게 느껴지더라고요. 공식 문서를 정독하는 게 좋은지, 튜토리얼 영상을 따라가며 코드를 직접 실행해보는 게 나은지 고민 중입니다. 일단 간단한 토이 프로젝트를 만들어 보려고 하는데, 역시 익숙하지 않은 언어로 구조를 잡는 건 쉽지 않네요. 여러분은 새로운 언어를 배울 때 어떤 접근 방식을 사용하시나요? 효과적인 루틴이 있다면 꼭 공유해주세요!]'
		     END
		     || CHR(10) 
			 || '사진 (' || repeat_cnt || ', ' || inner_cnt || ') 첨부했습니다.',
		     

		     SYSDATE - TRUNC(DBMS_RANDOM.VALUE(10, 20)),
		     SYSDATE - TRUNC(DBMS_RANDOM.VALUE(0, 10)),
		     TRUNC(DBMS_RANDOM.VALUE(10, 200)),
		     'N',
		     3,
		     TRUNC(DBMS_RANDOM.VALUE(1, 6)),
		     NULL
		  );

		  INSERT INTO BOARD_IMG (
		     IMG_NO,
		     IMG_PATH,
		     IMG_ORIG,
		     IMG_RENAME,
		     IMG_ORDER,
		     BOARD_NO
		  )
		  VALUES (
		     SEQ_IMAGE_NO.NEXTVAL,
		     '/images/board/freeboard/',
		     'fbList_img' || inner_cnt || '.png',
		     'fbList_img' || inner_cnt || '.png',
		     0,
		     SEQ_BOARD_NO.CURRVAL
		  );

	   END LOOP;
	   
	END LOOP;
	
	COMMIT;
END;
/

