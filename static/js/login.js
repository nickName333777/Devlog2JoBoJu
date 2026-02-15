console.log("login.js loaded...");

// API_BASE_URL은 common.js에서 이미 선언됨
//const API_BASE_URL = "http://localhost:8880";

// 페이지 로드 시 저장된 이메일 불러오기
document.addEventListener('DOMContentLoaded', () => {
    const saveId = getCookie('saveId');
    if (saveId) {
        document.getElementById('memberEmail').value = saveId;
        document.getElementById('saveId').checked = true;
    }
});

// 로그인 폼 제출
document.getElementById('loginFrm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const memberEmail = document.getElementById('memberEmail').value.trim();
    const memberPw = document.getElementById('memberPw').value;
    const saveId = document.getElementById('saveId').checked;
    
    // 유효성 검사
    if (!memberEmail) {
        alert("이메일을 입력해 주세요");
        document.getElementById('memberEmail').focus();
        return;
    }
    
    if (!memberPw) {
        alert("비밀번호를 입력해 주세요");
        document.getElementById('memberPw').focus();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/member/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',  // 쿠키 포함 (save_Id쿠키, loginMember저장 Session_Id 쿠키)
            body: JSON.stringify({
                member_email: memberEmail,
                member_pw: memberPw,
                save_id: saveId
            })
        });
        
        
        const data = await response.json();

        
        if (!response.ok) {
            throw new Error(data.detail || '로그인 실패');
        }
        
        console.log('로그인 성공, raw:', response);        
        console.log('로그인 성공:', data);
        
        // 토큰을 localStorage에 저장
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('loginMember', JSON.stringify(data));
        
        alert(`${data.member_nickname}님 환영합니다!`);
        
        // 메인 페이지로 이동
        window.location.href = '/index.html';
        
    } catch (error) {
        console.error('로그인 오류:', error);
        alert(error.message);
        document.getElementById('memberPw').value = '';
        document.getElementById('memberPw').focus();
    }
});


// 카카오 소셜로그인
const kakaoLoginBtn = document.getElementById("kakaoLoginBtn");

kakaoLoginBtn.addEventListener("click", function () {
            // JoBoJu 서비스 서버로 이동
            window.location.href = "/app/login/kakao";
});


// 쿠키 가져오기 함수
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
