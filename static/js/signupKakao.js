console.log('signupKakao.js loaded...');

// API_BASE_URL은 common.js에서 이미 선언됨

// kakaoId 확인 for 카카오 소셜로그인
const kakaoId = sessionStorage.getItem('kakaoId');
if (!kakaoId) {
    alert('카카오 로그인 정보가 없습니다. 다시 로그인해주세요.');
    window.location.href = '/member/login'; // GET 요청 jinja2 동적 렌더링
}

console.log('KakaoID:', kakaoId);

// 유효성 검사 객체 (signup.js와 동일하게 사용)
const checkObj = {
    memberEmail: false,
    memberPw: false,
    memberPwConfirm: false,
    memberName: false,
    memberNickname: false,
    memberTel: false,
    memberCareer: false,
    authKey: false
};

// 이메일 유효성 검사 (signup.js와 동일)
const memberEmail = document.getElementById("memberEmail");
const emailMessage = document.getElementById("emailMessage");

memberEmail.addEventListener("input", async function() {
    if (memberEmail.value === "") {
        emailMessage.innerText = "메일을 받을 수 있는 이메일을 입력해주세요.";
        emailMessage.classList.remove("confirm", "error");
        checkObj.memberEmail = false;
        return;
    }
    
    const regExp = /^[\w\_.]{4,}@[a-z]+(\.[a-z]+){1,2}$/;
    
    if (regExp.test(memberEmail.value)) {
        try {
            const response = await fetch(`${API_BASE_URL}/member/dupcheck/email?email=${memberEmail.value}`);
            const data = await response.json();
            
            if (data.exists) {
                emailMessage.innerText = "이미 사용중인 이메일 입니다.";
                emailMessage.classList.add("error");
                emailMessage.classList.remove("confirm");
                checkObj.memberEmail = false;
            } else {
                emailMessage.innerText = "사용 가능한 이메일입니다.";
                emailMessage.classList.add("confirm");
                emailMessage.classList.remove("error");
                checkObj.memberEmail = true;
            }
        } catch (error) {
            console.error("이메일 중복 체크 오류:", error);
        }
    } else {
        emailMessage.innerText = "이메일 형식이 유효하지 않습니다.";
        emailMessage.classList.add("error");
        emailMessage.classList.remove("confirm");
        checkObj.memberEmail = false;
    }
});

// 인증번호 발송 (signup.js와 동일)
let authTimer;
let authMin = 4;
let authSec = 59;
let tempEmail = "";

document.getElementById("sendAuthKeyBtn").addEventListener("click", async function() {
    if (!checkObj.memberEmail) {
        alert("유효한 이메일을 작성해주세요.");
        memberEmail.focus();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/sendEmail/signup?email=${memberEmail.value}`);
        const data = await response.json();
        
        if (data.result > 0) {
            tempEmail = memberEmail.value;
            alert("인증번호가 발송되었습니다.");
            
            authMin = 4;
            authSec = 59;
            authKeyMessage.innerText = "05:00";
            authKeyMessage.classList.remove("confirm");
            
            clearInterval(authTimer);
            
            authTimer = setInterval(() => {
                authKeyMessage.innerText = "0" + authMin + ":" + (authSec < 10 ? "0" + authSec : authSec);
                
                if (authMin === 0 && authSec === 0) {
                    checkObj.authKey = false;
                    clearInterval(authTimer);
                    return;
                }
                
                if (authSec === 0) {
                    authSec = 60;
                    authMin--;
                }
                
                authSec--;
            }, 1000);
        }
    } catch (error) {
        console.error("인증번호 발송 오류:", error);
        alert("인증번호 발송에 실패했습니다.");
    }
});

// 인증 확인 (signup.js와 동일)
const authKey = document.getElementById("authKey");
const authKeyMessage = document.getElementById("authKeyMessage");

document.getElementById("checkAuthKeyBtn").addEventListener("click", async function() {
    if (authMin === 0 && authSec === 0) {
        alert("인증 시간이 만료되었습니다. 다시 시도해주세요.");
        return;
    }
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/sendEmail/checkAuthKey?inputKey=${authKey.value}&email=${tempEmail}`
        );
        const data = await response.json();
        
        if (data.result > 0) {
            clearInterval(authTimer);
            authKeyMessage.innerText = "인증되었습니다.";
            authKeyMessage.classList.add("confirm");
            checkObj.authKey = true;
        } else {
            alert("인증번호가 일치하지 않습니다.");
            checkObj.authKey = false;
        }
    } catch (error) {
        console.error("인증 확인 오류:", error);
    }
});


// 비밀번호 유효성 검사
const memberPw = document.getElementById("memberPw");
const memberPwConfirm = document.getElementById("memberPwConfirm");
const pwMessage = document.getElementById("pwMessage");

memberPw.addEventListener("input", function() {
    if (memberPw.value.trim().length === 0) {
        pwMessage.innerText = "영어, 숫자, 특수문자(!, @, #, -, _) 6~20글자 사이로 입력해 주세요.";
        pwMessage.classList.remove("confirm", "error");
        checkObj.memberPw = false;
        return;
    }
    
    const regExp = /^[\w!@#\-_]{6,20}$/;
    
    if (regExp.test(memberPw.value)) {
        checkObj.memberPw = true;
        
        if (memberPwConfirm.value === "") {
            pwMessage.innerText = "사용가능한 비밀번호 입니다.";
            pwMessage.classList.add("confirm");
            pwMessage.classList.remove("error");
        } else {
            if (memberPw.value === memberPwConfirm.value) {
                pwMessage.innerText = "비밀번호가 일치합니다.";
                pwMessage.classList.add("confirm");
                pwMessage.classList.remove("error");
                checkObj.memberPwConfirm = true;
            } else {
                pwMessage.innerText = "비밀번호가 일치하지 않습니다.";
                pwMessage.classList.add("error");
                pwMessage.classList.remove("confirm");
                checkObj.memberPwConfirm = false;
            }
        }
    } else {
        pwMessage.innerText = "사용 불가능한 비밀번호 입니다.";
        pwMessage.classList.add("error");
        pwMessage.classList.remove("confirm");
        checkObj.memberPw = false;
    }
});

memberPwConfirm.addEventListener("input", () => {
    if (memberPw.value === "") {
        alert("비밀번호를 입력해주세요.");
        memberPwConfirm.value = "";
        memberPw.focus();
        return;
    }
    
    if (checkObj.memberPw) {
        if (memberPw.value === memberPwConfirm.value) {
            pwMessage.innerText = "비밀번호가 일치합니다.";
            pwMessage.classList.add("confirm");
            pwMessage.classList.remove("error");
            checkObj.memberPwConfirm = true;
        } else {
            pwMessage.innerText = "비밀번호가 일치하지 않습니다.";
            pwMessage.classList.add("error");
            pwMessage.classList.remove("confirm");
            checkObj.memberPwConfirm = false;
        }
    } else {
        checkObj.memberPwConfirm = false;
    }
});

// 이름, 닉네임, 전화번호, 경력사항 유효성 검사 
// 이름 유효성 검사
const memberName = document.getElementById("memberName"); 
const nameMessage = document.getElementById("nameMessage");

memberName.addEventListener("input", () =>{
    // 입력된 이름이 없을 경우
    if (memberName == ""){
        nameMessage.innerText = "유효한 한글 이름 입력해 주세요"
        nameMessage.classList.remove("confirm", "error");
        checkObj.memberName = false;
        return;
    }

    // 입력된 이름이 있을 경우
    // 이름 작성시, 유효성 검사: 한글 2~15글자
    const regEx = /^[가-힣]{2,15}$/; //"한글2~15글자 사이"

    if (regEx.test(memberName.value)) {
        // 유효한 경우
        nameMessage.innerText = "유효한 한글 이름입니다."
        nameMessage.classList.add("confirm");
        nameMessage.classList.remove("error");
        checkObj.memberName = true;
        
    } else {
        // 유효하지 않은 경우 
        nameMessage.innerText = "유효하지 않은 한글이름입니다.  한글로만 2~15글자를 넣어주세요."
        nameMessage.classList.add("error");
        nameMessage.classList.remove("confirm");
        checkObj.memberName = false;        
    }

})

// 닉네임 유효성 검사
const memberNickname = document.getElementById("memberNickname"); 
const nicknameMessage = document.getElementById("nicknameMessage");

//memberNickname.addEventListener("input", ()=> {
memberNickname.addEventListener("input", async (e) => {

    // 입력된 닉네임이 없을 경우
    if (memberNickname == ""){
        nicknameMessage.innerText = "한글,영어,숫자로만 2~10글자로 입력해 주세요"
        nicknameMessage.classList.remove("confirm", "error");
        checkObj.memberNickname = false;
        return;
    }

    // 입력된 닉네임이 있을 경우
    // 닉네임 작성시, 유효성 검사: 한글,영어,숫자로만 2~10글자
    const regEx = /^[가-힣a-zA-Z0-9]{2,10}$/; //"영어/숫자/한글2~10글자 사이"

    if (regEx.test(memberNickname.value)) {
        // 유효한 경우

        //******************************************* */
        // fetch() API를 이용한 ajax
        // //console.log("test : " + memberNickname.value)
        // console.log("test : ", memberNickname.value)

        // 요청주소 : /dupCheck/nickname
        // 중복인 경우 : "이미 사용 중인 닉네임입니다." 빨간 글씨
        // 중복이 아닌 경우 : "사용 가능한 닉네임입니다." 초록글씨

        try {
            const response = await fetch(`${API_BASE_URL}/member/dupcheck/nickname?nickname=${memberNickname.value}`);
            const data = await response.json();
            console.log("Nickname 중복체크 결과 = ", data)
            if (data.exists) {
                nicknameMessage.innerText = "이미 사용 중인 닉네임입니다."
                nicknameMessage.classList.add("error");
                nicknameMessage.classList.remove("confirm");
                checkObj.memberNickname = false; 
            } else {
                nicknameMessage.innerText = "사용 가능한 닉네임입니다."
                nicknameMessage.classList.add("confirm");
                nicknameMessage.classList.remove("error");
                checkObj.memberNickname = true;
            }

        } catch (error) {
            console.error("닉네임 중복 체크 오류:", error);
        }

    } else {
        // 유효하지 않은 경우 
        nicknameMessage.innerText = "유효하지 않은 닉네임입니다.  한글,영어,숫자로만 2~10글자를 넣어주세요."
        nicknameMessage.classList.add("error");
        nicknameMessage.classList.remove("confirm");
        checkObj.memberNickname = false;        
    }

})



// 전화번호 유효성 검사
const memberTel = document.getElementById("memberTel");
const telMessage = document.getElementById("telMessage");

memberTel.addEventListener("input", ()=>{

    // 전화번호 미 입력시
    if(memberTel.value == ""){
        telMessage.innerText = "전화번호를 입력해 주세요.";
        telMessage.classList.remove("confirm", "error");
        checkObj.memberTel = false;
        return;
    }

    // 전화번호 입력시, 유효성 검사: 전화번호를 입력해주세요.(- 제외)
    const regEx = /^0(1[01]|2|[3-6][1-5]|70)\d{7,8}$/; //" 하이픈제외"

    if (regEx.test(memberTel.value)) {
        telMessage.innerText = "유효한 전화번호입니다.";
        telMessage.classList.add("confirm");
        telMessage.classList.remove("error");
        checkObj.memberTel = true;
    } else {
        telMessage.innerText = "존재하지 않은 전화 번호입니다.";
        telMessage.classList.add("error");
        telMessage.classList.remove("confirm");
        checkObj.memberTel = false;        
    }

})

// 경력사항 유효성 검사
const memberCareer = document.getElementById("memberCareer");
const careerMessage = document.getElementById("careerMessage");


memberCareer.addEventListener("input", () =>{
    // 입력된 경력 사항이 없을 경우
    if (memberCareer == ""){
        careerMessage.innerText = "경력사항을 입력해 주세요(예시:벡엔드3년차)"
        careerMessage.classList.remove("confirm", "error");
        checkObj.memberCareer = false;
        return;
    }

    // 입력된 경력사항이 있을 경우
    // 경력사항 작성시, 유효성 검사: 한글 + 숫자 둘 다 반드시 포함 + 공백 허용 + 길이 2~40
    const regEx = /^(?=.*[가-힣])(?=.*[0-9])[가-힣0-9 ]{2,40}$/; //"경력(한글)과 년차(숫자)포함 2~40글자 사이"

    if (regEx.test(memberCareer.value)) {
        // 유효한 경우
        careerMessage.innerText = "유효한 경력사항입니다."
        careerMessage.classList.add("confirm");
        careerMessage.classList.remove("error");
        checkObj.memberCareer = true;
        
    } else {
        // 유효하지 않은 경우 
        careerMessage.innerText = "유효하지 않은 경력사항입니다.  경력(한글)과 년차(숫자)포함 2~40글자를 넣어주세요."
        careerMessage.classList.add("error");
        careerMessage.classList.remove("confirm");
        checkObj.memberCareer = false;        
    }

})




// 폼 제출
document.getElementById("signupKakaoFrm").addEventListener("submit", async (e) => {
    e.preventDefault();
    
    // 모든 필드 검증
    for (let key in checkObj) {
        if (!checkObj[key]) {
            alert(`${key}가 유효하지 않습니다.`);
            document.getElementById(key)?.focus();
            return;
        }
    }
    
    const formData = {
        member_email: memberEmail.value,
        member_pw: memberPw.value,
        member_name: document.getElementById("memberName").value,
        member_nickname: document.getElementById("memberNickname").value,
        member_tel: document.getElementById("memberTel").value,
        member_career: document.getElementById("memberCareer").value,
        member_subscribe: document.getElementById("memberSubscribe").checked ? 'Y' : 'N'
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/app/login/kakao/signup?kakao_id=${kakaoId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 토큰 저장 for 카카오 소셜로그인
            localStorage.setItem('access_token', data.access_token);
            
		    // loginMember info를 localStorage에 저장
            console.log("member_dto :", data.member_dto)
            localStorage.setItem('loginMember', JSON.stringify(data.member_dto));     

            // kakaoId 세션 삭제 for 카카오 소셜로그인
            sessionStorage.removeItem('kakaoId');
            
            alert(data.message);
            window.location.href = '/index.html';
        } else {
            throw new Error(data.detail || '필수 회원정보 입력에 실패했습니다. 잠시후 다시 시도해 주세요');
        }
    } catch (error) {
        console.error("필수 회원정보 입력 오류:", error);
        alert(error.message);
    }
});
