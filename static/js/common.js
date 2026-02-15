// 공통 JavaScript 유틸리티
// const API_BASE_URL = "http://localhost:8880"; // login.js, signup.js, main.js에서 중복설정 충돌 발생
// 전역 설정 객체
window.APP_CONFIG = window.APP_CONFIG || {
    API_BASE_URL: "http://localhost:8880",
    DEBUG: true
};
// 편의를 위한 상수
const API_BASE_URL = window.APP_CONFIG.API_BASE_URL;

console.log("common.js loaded, API_BASE_URL:", API_BASE_URL);

// API용 엔드포인트를 따로 만들기: URL 분리 (페이지 렌더링: /board/list, AJAX 데이터용: /api/board/ajax/list)
//                                 => Spring에서 Controller (View) for 페이지 렌더링, RestController (JSON) for AJAX 데이터용
// 전역 노출, 세션 기반 로그인 유지
window.fetchAPI = async function (url, options = {}) {
    const defaultOptions = {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        },
        credentials: "include" // 세션 로그인 유지 (중요)
    };

    const response = await fetch(
        API_BASE_URL + url,
        { ...defaultOptions, ...options }
    );

    return response;
};


// JS-CSR로 로그인 상태관리시 사용가능한 전역변수(index.html에서 세팅된 전역변수로, common.js가 index.html 로그인상태관리할때만 사용가능)
// loginMemberNo 
// memberNickname
// profileImg
// beansAmount

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', () => {
    syncAuthState(); // 
    checkLoginStatus(); // 로그인 상태 확인 및 UI 업데이트 by access_token
    //checkLoginStatusBySession(); // loginMemberNo is not defined
    // setTimeout(() => { // index.html에 /api/auth/me ajax가 딜레이때문에 거기서 생성되는 전역변수 사용하려면 약 delay 0.5초가량 지연 실행 필요
    //     console.log("0.5초 후 커피콩 체크및 세선 처리");
    //     checkLoginStatusBySession();
    // }, 500);
    setupLogoutHandler();
});

// for JWT(static, index.html) + Session(jinja2, 그외html들) 혼용시 서버세션 유효한지 check(/api/session/check) on 2026/02/08 
async function syncAuthState() {
    const token = localStorage.getItem('access_token');

    // JWT자체가 없으면 체크할 필요없음
    if (!token) return;

    try {
        const res = await fetch('/api/session/check', {
            credentials: 'include' // <===세션 쿠키 전달 필수
        });

        const data = await res.json();

        if (!data.loggedIn) {
            // 서버 세션 죽음 → JWT도 정리
            localStorage.removeItem('access_token');
            localStorage.removeItem('loginMember');

            alert('로그인이 만료되었습니다.');
            location.href = '/member/login';
        }
    } catch (e) {
        console.error('세션 동기화 실패', e);
    }
}

// 로그인 상태 확인 및 UI 업데이트 by access_token
function checkLoginStatus() { 
    // 
    const token = localStorage.getItem('access_token'); 
    const loginMember = JSON.parse(localStorage.getItem('loginMember') || 'null');
    
    // 로그인 상태에 따른 프론트 화면 동적구성(CSR)
    const loginMenu = document.getElementById('loginMenu'); // 로그인 전
    const userInfo = document.getElementById('userInfo');   // 로그인 후
    const notificationContainer = document.getElementById('notificationContainer');
    const userNickname = document.getElementById('userNickname');
    const userProfileImgHeader = document.getElementById('userProfileImgHeader');
    
    console.log("checking loginMember = ", loginMember);

    if (token && loginMember) {
        // 로그인 상태
        if (loginMenu) loginMenu.style.display = 'none';
        if (userInfo) {
            userInfo.style.display = 'block';
            if (userProfileImgHeader){
                //userProfileImgHeader.src = loginMember.profile_img;
                userProfileImgHeader.src = `/uploads${loginMember.profile_img}`;
            }
            if (userNickname) {
                userNickname.textContent = loginMember.member_nickname;
            }
        }
        if (notificationContainer) {
            notificationContainer.style.display = 'block';
        }
    } else {
        // 로그아웃 상태
        if (loginMenu) loginMenu.style.display = 'flex';
        if (userInfo) userInfo.style.display = 'none';
        if (notificationContainer) {
            notificationContainer.style.display = 'none';
        }
    }
}


// 로그인 상태 확인 및 UI 업데이트 by 서버 세션 메모리 ==> 별로 사용성이 않좋아 실사용은 안함
function checkLoginStatusBySession() { 
    // 
    //const token = localStorage.getItem('access_token'); 
    //const loginMember = JSON.parse(localStorage.getItem('loginMember') || 'null');
    //
    const loginMemberNoSession = loginMemberNo; 
    const memberNicknameSession = memberNickname;
    const profileImgSession = profileImg;
    //const beansAmountSession = beansAmount;

    // 로그인 상태에 따른 프론트 화면 동적구성(CSR)
    const loginMenu = document.getElementById('loginMenu'); // 로그인 전
    const userInfo = document.getElementById('userInfo');   // 로그인 후
    const notificationContainer = document.getElementById('notificationContainer');
    const userNickname = document.getElementById('userNickname');
    const userProfileImgHeader = document.getElementById('userProfileImgHeader');
    
    console.log("checking loginMemberNoSession = ", loginMemberNoSession);
    console.log("checking memberNicknameSession = ", memberNicknameSession);
    console.log("checking profileImgSession = ", profileImgSession);

    if (memberNicknameSession && loginMemberNoSession) {
        // 로그인 상태
        if (loginMenu) loginMenu.style.display = 'none';
        if (userInfo) {
            userInfo.style.display = 'block';
            if (userProfileImgHeader){
                //userProfileImgHeader.src = loginMember.profile_img;
                userProfileImgHeader.src = profileImgSession;
            }
            if (userNickname) {
                userNickname.textContent = memberNicknameSession;
            }
        }
        if (notificationContainer) {
            notificationContainer.style.display = 'block';
        }
    } else {
        // 로그아웃 상태
        if (loginMenu) loginMenu.style.display = 'flex';
        if (userInfo) userInfo.style.display = 'none';
        if (notificationContainer) {
            notificationContainer.style.display = 'none';
        }
    }
}


// 로그아웃 핸들러 설정
function setupLogoutHandler() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            try {
                const response = await fetch(`${API_BASE_URL}/member/logout`, { // 서버 세션 정리
                    method: 'GET',
                    credentials: 'include'
                });
                
                if (response.ok) {
                    // 프론트 로컬 스토리지 정리
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('loginMember');
                    
                    alert('로그아웃 되었습니다.');
                    window.location.href = '/static/index.html';
                }
            } catch (error) {
                console.error('로그아웃 오류:', error);
                // 에러가 발생해도 프론트 로컬스토리지 데이터는 정리
                localStorage.removeItem('access_token');
                localStorage.removeItem('loginMember');
                window.location.href = '/static/index.html';
            }
        });
    }
}

// API 요청 헬퍼 함수 (JWT 토큰 자동 포함)
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('access_token');
    
    if (token) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };
    }
    
    options.credentials = 'include';
    
    const response = await fetch(url, options);
    
    // 401 에러 시 로그인 페이지로 리다이렉트
    if (response.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('loginMember');
        alert('로그인이 필요합니다.');
        window.location.href = '/static/login.html';
        return null;
    }
    
    return response;
}

// 날짜 포맷팅 함수
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

// 쿠키 관련 함수
function getCookie(name) {
    const cookies = document.cookie.split('; ');
    for (let cookie of cookies) {
        const [key, value] = cookie.split('=');
        if (key === name) {
            return decodeURIComponent(value);
        }
    }
    return null;
}

function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires.toUTCString()}; path=/`;
}

function deleteCookie(name) {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
}

// 현재 사용자 정보 가져오기
function getCurrentUser() {
    return JSON.parse(localStorage.getItem('loginMember') || 'null');
}

// 로그인 여부 확인
function isLoggedIn() {
    return !!localStorage.getItem('access_token'); // !!은 boolean으로 강제변환(access_token있으면 True, 없으면 False)
}

// 페이지 접근 권한 체크 (로그인 필수 페이지)
function requireLogin() {
    if (!isLoggedIn()) {
        alert('로그인이 필요한 페이지입니다.');
        window.location.href = '/static/login.html';
        return false;
    }
    return true;
}
