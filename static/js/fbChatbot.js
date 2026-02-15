/* fbChatbot.js - JoBoJu 챗봇 로직 */
console.log("fbChatbot.js loaded");

// DOM 요소
const chatBox = document.getElementById("chatBox");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");

// 전역 변수
let currentSessionId = null;  // 서버에서 받은 실제 세션 ID
let accumulated_usedBeans = 0;
let beansAmount2update = 0;

let totalServerTokens = 0;
let totalClientTokens = 0;
let lastQuestion = "";
let lastAiAnswer = "";

// ============================================
// 페이지 초기화
// ============================================

/**
 * 페이지 로드 시 실행
 */
window.addEventListener('DOMContentLoaded', function() {
    console.log("BeansAmount:", window.beansAmount);
    
    // 커피콩 체크 및 세션 시작
    //checkBeansAndStartSession();
    setTimeout(() => {
        console.log("0.5초 후 커피콩 체크및 세선 처리");
        checkBeansAndStartSession(); // ajax실행 지연 감안
    }, 500);
    
    // 입력 글자 수 제한 설정
    setupTextareaLimit();
});

/**
 * 창 닫을 때 세션 종료
 */
window.addEventListener('beforeunload', function() {
    if (currentSessionId) {
        endChatbotSession();
    }
});

// ============================================
// 세션 관리
// ============================================

/**
 * 커피콩 체크 후 세션 시작
 *  // 커피콩 챗봇인 경우 잔액 체크 => '/api/auth/me'에 delay있어서 처음에는 무조건 로그인정보 available하지 않아 loginMember 정보 ==> null
 *  //                                 처음 session 시작시 콩잔액 체크랑, 로그인 정보 체크를 위해 약 ~ 0.5 sec 뒤에 checkBeansAndStartSession() 실행시켜야함 
 * 
 */
function checkBeansAndStartSession() {
    const chatbotTypeSelect = document.getElementById("chatbotType");
    const chatbotType = chatbotTypeSelect ? chatbotTypeSelect.value : "basic";
    
    // 로그인 체크 (커피콩 챗봇의 경우)
    if (chatbotType === "kong" && !window.loginMemberNo) {
        alert("커피콩 충전형 챗봇은 로그인이 필요합니다.");
        window.close();
        return;
    }
    
    // 커피콩 챗봇인 경우 잔액 체크: ('/api/auth/me'에 delay =>  setTimeout()으로 지연준다)                            
    if (chatbotType === "kong") {

        // beansAmount ==> Uncaught ReferenceError: can't access lexical declaration 'beansAmount' before initialization ('/api/auth/me'에 delay있다)
        const beansAmount = window.beansAmount || 0; // 이거는 not-working 초기에 0 why? fbChatbotRevKong.html에서 설정 delay?
        //const beansAmount = beansAmount || 0; // 이거도 not-working, fbChatbotRevKong.html에서 설정 전역변수값 설정 delay?
        
        if (beansAmount <= 0) {
            alert(`커피콩 잔액이 ${beansAmount}입니다.\n커피콩충전형 챗봇은 커피콩 충전 후 이용해 주세요.`);
            
            // // 부모 창이 있으면 부모 창을 리다이렉트, 없으면 현재 창 => // "/coffeebeans" 없으므로 redirection은 일단 inactive            
            // if (window.opener) {
            //     window.opener.location.href = "/coffeebeans";
            //     window.close();
            // } else {
            //     window.location.href = "/coffeebeans";
            // }
            return;
        }
    }
    
    // 커피콩이 충분하면 세션 시작
    startChatbotSession();
}

/**
 * 챗봇 세션 시작
 */
function startChatbotSession() {
    console.log("챗봇 세션 시작을 위한 세션 정보 수집...");
    
    const chatbotTypeSelect = document.getElementById("chatbotType");
    const chatbotType = chatbotTypeSelect ? chatbotTypeSelect.value : "basic";
    
    // 부모 창에서 boardNo 가져오기
    if (window.opener && window.opener.globalData) {
        window.boardNo = window.opener.globalData.boardNo || window.opener.globalData.boardNoGlobal;
        window.loginMemberNo = window.opener.globalData.loginMemberNo || window.opener.globalData.loginMemberNoGlobal;
    }
    
    const cbBoardType = window.boardNo ? "UPDATE" : "INSERT";
    
    console.log("수집된 챗봇 세션 정보:", {
        chatbotType,
        cbBoardType,
        boardNo: window.boardNo,
        loginMemberNo: window.loginMemberNo
    });
    
    const requestData = {
        // cbSessionType: chatbotType.toUpperCase(),  // BASIC, KONG
        // cbBoardType: cbBoardType,                   // INSERT, UPDATE
        // boardNo: window.boardNo || null
        // for Request body of CbSessionCreate in fetch('/api/chatbot/session/start')
        cb_session_type: chatbotType.toUpperCase(),  // BASIC, KONG
        cb_board_type: cbBoardType,                   // INSERT, UPDATE
        board_no: window.boardNo || null
    };
    
    fetch('/api/chatbot/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    })
    .then(res => res.json())
    .then(data => {
    	//console.log("##### fbChatbot.js, fetch('/api/chatbot/session/start'), 반환데이터 data: ", data)
    	//console.log("##### fbChatbot.js, fetch('/api/chatbot/session/start'), 반환데이터 data.success: ", data.success)
        if (data.success) {
            currentSessionId = data.sessionId;
            console.log("챗봇 세션 시작, 현 세션번호 =", currentSessionId);
            
            // 세션 시작 후 커피콩 정보 업데이트
            if (window.loginMemberNo && chatbotType === "kong") {
                console.log("updating BeansDisplay... ");
                updateBeansDisplay();
            }
        } else {
            console.error("세션 시작 실패:", data.error || data.message);
            alert("챗봇 세션 시작에 실패했습니다.");
        }
    })
    .catch(err => {
        console.error("세션 시작 오류:", err);
        alert("챗봇을 시작할 수 없습니다.");
    });
}

/**
 * 챗봇 세션 종료
 */
function endChatbotSession() {
    if (!currentSessionId) return;
    
    const chatbotTypeSelect = document.getElementById("chatbotType");
    const chatbotType = chatbotTypeSelect ? chatbotTypeSelect.value : "basic";
    
    console.log("챗봇 세션 종료 시작 - 누적 사용 커피콩:", accumulated_usedBeans);
    
    // 1. KONG 타입만 커피콩 과금 처리
    if (chatbotType === "kong" && window.loginMemberNo) {
        const initialBeans = window.beansAmount || 0;
        const finalBeansAmount = Math.max(0, initialBeans - accumulated_usedBeans);

        console.log("=== 챗봇 세션 종료 정보 ===");
        console.log("초기 커피콩:", initialBeans);
        console.log("누적 사용 커피콩:", accumulated_usedBeans);
        console.log("최종 잔여 커피콩:", finalBeansAmount);
        console.log("========================");

        // 아무 질문도 안 했으면 업데이트 안 함
        if (accumulated_usedBeans > 0) {
            // MEMBER 테이블 커피콩 업데이트
            fetch('/api/chatbot/freeboard/updateBeansAmount', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    loginMemberNo: window.loginMemberNo,
                    updatedBeansAmount: finalBeansAmount
                }),
                keepalive: true
            })
            .then(response => {
                if (response.ok) {
                    console.log("MEMBER 테이블 업데이트 성공");
                } else {
                    console.error("MEMBER 테이블 업데이트 실패:", response.status);
                }
            })
            .catch(err => {
                console.error("MEMBER 테이블 업데이트 오류:", err);
            });

            console.log("MEMBER 테이블 업데이트 요청 전송:", {
                loginMemberNo: window.loginMemberNo,
                updatedBeansAmount: finalBeansAmount
            });
        } else {
            console.log("커피콩 사용 없음 - DB MEMBER 테이블 업데이트 생략");
        }
    }
    
    // 2. 세션 종료 (항상 실행)
    fetch(`/api/chatbot/session/end/${currentSessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}), // 전달 body데이터는 없음
        keepalive: true
    })
    .then(response => {
        if (response.ok) {
            console.log("챗봇 세션 종료 성공:", currentSessionId);
        }
    })
    .catch(err => {
        console.error("세션 종료 오류:", err);
    });
}

// ============================================
// UI 설정
// ============================================

/**
 * 입력 글자 수 제한 설정 (BASIC 타입만)
 */
function setupTextareaLimit() {
    const chatbotTypeSelect = document.getElementById("chatbotType");
    const chatbotType = chatbotTypeSelect ? chatbotTypeSelect.value : "basic";
    const textarea = document.getElementById("chatInput");
    
    if (!textarea) return;
    
    if (chatbotType === "basic") {
        // BASIC 타입: 20자 제한 (테스트용)
        textarea.maxLength = 20;
        
        // 글자 수 표시 추가
        const charCounter = document.createElement('div');
        charCounter.id = 'charCounter';
        charCounter.style.cssText = 'text-align: right; font-size: 12px; color: #777; padding: 5px 10px;';
        charCounter.textContent = '0 / 20자';
        
        const inputArea = document.querySelector('.input-area');
        if (inputArea && !document.getElementById('charCounter')) {
            inputArea.insertBefore(charCounter, textarea);
        }
        
        // 입력 시 글자 수 업데이트
        textarea.addEventListener('input', function() {
            let value = this.value;

            if (value.length > 20) {
                this.value = value.slice(0, 20) + '...';
            }

            const length = this.value.length;
            charCounter.textContent = `${length} / 20자`;
            
            if (length >= 20) {
                charCounter.style.color = 'red';
            } else if (length >= 15) {
                charCounter.style.color = 'orange';
            } else {
                charCounter.style.color = '#777';
            }
        });
    } else {
        // KONG 타입: 4000자 제한
        textarea.maxLength = 4000;
        
        // 기존 글자 수 표시 제거
        const existingCounter = document.getElementById('charCounter');
        if (existingCounter) {
            existingCounter.remove();
        }
    }
}

/**
 * 토큰 사용량 표시 업데이트
 */
function updateTokenDisplay(promptTokens, completionTokens, totalTokens, accumulatedUsedBeans) {
    // 전역변수 업데이트
    accumulated_usedBeans = accumulatedUsedBeans || 0;
    
    // 잔여 커피콩 계산
    const initialBeans = window.beansAmount || 0;
    beansAmount2update = Math.max(0, initialBeans - accumulated_usedBeans);

    console.log("=== 토큰 업데이트 상세 ===");
    console.log("현재 턴 토큰:", { promptTokens, completionTokens, totalTokens });
    console.log("누적 정보:", { accumulatedUsedBeans, initialBeans, beansAmount2update });
    console.log("=======================");

    // 화면 표시 업데이트
    const beansAmountElement = document.getElementById("beansAmount");
    if (beansAmountElement) {
        beansAmountElement.textContent = `콩잔액: ${beansAmount2update.toLocaleString()} 포인트`;
    }

    const tokenUsageDisplay = document.getElementById("tokenUsageDisplay");
    if (tokenUsageDisplay) {
        tokenUsageDisplay.textContent = `사용 토큰: ${totalTokens} (질문: ${promptTokens}, 답변: ${completionTokens}), 사용 콩: ${accumulatedUsedBeans}`;
    }
    
    totalServerTokens += totalTokens;
    
    // KONG 타입만 커피콩 체크
    const chatbotTypeSelect = document.getElementById("chatbotType");
    const chatbotType = chatbotTypeSelect ? chatbotTypeSelect.value : "basic";
    
    if (chatbotType === "kong" && beansAmount2update <= 0) {
        alert("커피콩이 모두 소진되었습니다. 충전 후 이용해 주세요.");
        endChatbotSession();
        
        // // "/coffeebeans" 요청주소 현재 처리안하므로 redirection은 inactive        
        // if (window.opener) {
        //     window.opener.location.href = "/coffeebeans";
        //     window.close();
        // } else {
        //     window.location.href = "/coffeebeans";
        // }
    }
}

/**
 * 커피콩 잔액 표시 업데이트
 */
function updateBeansDisplay() {
    fetch('/api/chatbot/freeboard/usage')
        .then(res => res.json())
        .then(data => {
            const beansAmountElement = document.getElementById('beansAmount');
            if (beansAmountElement && data.remainingBeans !== undefined) {
                beansAmountElement.textContent = `콩잔액: ${data.remainingBeans.toLocaleString()} 포인트`;
                window.beansAmount = data.remainingBeans;
                
                const chatbotTypeSelect = document.getElementById("chatbotType");
                const chatbotType = chatbotTypeSelect ? chatbotTypeSelect.value : "basic";
                
                if (chatbotType === "kong" && data.remainingBeans <= 0) {
                    alert("커피콩이 모두 소진되었습니다. 충전 후 이용해 주세요.");
                    
                    // // "/coffeebeans" 요청주소 현재 처리안하므로 redirection은 inactive
                    // if (window.opener) {
                    //     window.opener.location.href = "/coffeebeans";
                    //     window.close();
                    // } else {
                    //     window.location.href = "/coffeebeans";
                    // }
                }
            }
        })
        .catch(err => {
            console.warn('커피콩 정보 업데이트 실패:', err);
        });
}

// ============================================
// 메시지 UI
// ============================================

/**
 * 사용자 메시지 추가
 */
function addUserMessage(text) {
    const row = document.createElement("div");
    row.className = "chat-row right";

    const nickname = window.memberNickname || "유저";
    // const userProfileImg = window.profileImg || "/static/images/user.png";
    const userProfileImg = profileImg || "/static/images/user.png";
    console.log("### window.profileImg = ", window.profileImg);
    console.log("### profileImg = ", profileImg);
    console.log("### userProfileImg = ", userProfileImg);

    row.innerHTML = `
        <div>
            <div class="bubble user" onclick="showCopyMenu(event, this)">
                ${escapeHtml(text)}
            </div>
            <div class="time">${now()}</div>
            <div class="name">${escapeHtml(nickname)}</div>
        </div>
        <img src="${userProfileImg}" class="bot-img" alt="유저">
    `;

    chatBox.appendChild(row);
    scrollToBottom();
}

/**
 * 봇 메시지 추가
 */
function addBotMessage(text) {
    const row = document.createElement("div");
    row.className = "chat-row left";

    const botImg = window.cbtProfileImg || "/static/images/board/freeboard/chatbot1.png";

    row.innerHTML = `
        <img src="${botImg}" class="bot-img" alt="챗봇">
        <div>
            <div class="bubble bot" onclick="showCopyMenu(event, this)">
                ${escapeHtml(text).replace(/\n/g, "<br>")}
            </div>
            <div class="time">${now()}</div>
            <div class="name">JoBoJu 챗봇</div>
        </div>
    `;

    chatBox.appendChild(row);
    scrollToBottom();
}

// ============================================
// 메시지 전송
// ============================================

/**
 * OpenAI API 연동: 실제 질문 보내고 응답 받기
 */
function sendMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    // 세션 체크
    if (!currentSessionId) {
        alert("챗봇 세션이 시작되지 않았습니다. 페이지를 새로고침해주세요.");
        return;
    }

    // 커피콩 체크 (KONG 타입만)
    const chatbotTypeSelect = document.getElementById("chatbotType");
    const chatbotType = chatbotTypeSelect ? chatbotTypeSelect.value : "basic";
    
    if (chatbotType === "kong") {
        const currentBeans = beansAmount2update > 0 ? beansAmount2update : window.beansAmount;
        if (currentBeans <= 0) {
            alert("커피콩이 부족합니다. 충전 후 이용해 주세요.");
            // // "/coffeebeans" 요청주소 현재 처리안하므로 redirection은 inactive
            // if (window.opener) {
            //     window.opener.location.href = "/coffeebeans";
            //     window.close();
            // }
            return;
        }
    }

    chatInput.value = "";

    // 1) 유저 질문 화면에 보여주기
    addUserMessage(msg);

    // 2) 서버로 질문 전송
    fetch(`/api/chatbot/freeboard/${currentSessionId}`, {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: msg
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`서버 응답 오류: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        console.log("챗봇 응답:", data);

        if (data.error) {
            addBotMessage(`오류: ${data.error}`);
            return;
        }

        // 3) 챗봇 대답 화면에 보여주기
        addBotMessage(data.reply || data.content || "응답 없음");

        // 토큰 사용량 업데이트 (KONG 타입만)
        if (data.usage && chatbotType === "kong") {
            const {
                prompt_tokens,
                completion_tokens,
                total_tokens,
                accumulated_tokens,
                accumulated_usedBeans: serverUsedBeans
            } = data.usage;
            
            console.log("##### 서버에서 받은 누적 커피콩:", serverUsedBeans);

            updateTokenDisplay(
                prompt_tokens,
                completion_tokens,
                total_tokens,
                serverUsedBeans || 0
            );
        }
    })
    .catch(err => {
        addBotMessage("서버와 통신 중 오류가 발생했습니다.");
        console.error("에러:", err);
    });
}

// ============================================
// 유틸리티 함수
// ============================================

/**
 * 맨 아래로 스크롤
 */
function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * 타임스탬프
 */
function now() {
    return new Date().toLocaleString();
}

/**
 * HTML 이스케이프 (XSS 방지)
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 토큰 계산 (대략적)
 */
function tokenCalc(text) {
    return Math.ceil(text.length / 4);
}

// ============================================
// 복사 메뉴
// ============================================

/**
 * 말풍선 복사 메뉴 표시
 */
function showCopyMenu(event, bubbleElement) {
    event.stopPropagation();
    
    // 기존 메뉴 제거
    const existingMenu = document.querySelector('.copy-menu');
    if (existingMenu) {
        existingMenu.remove();
    }
    
    // 복사 메뉴 생성
    const menu = document.createElement('div');
    menu.className = 'copy-menu';
    menu.innerHTML = '<button onclick="copyBubbleText(event)">📋 복사</button>';
    
    // 메뉴 위치 설정
    menu.style.position = 'absolute';
    menu.style.left = event.pageX + 'px';
    menu.style.top = event.pageY + 'px';
    menu.style.zIndex = '1000';
    
    // 복사할 텍스트 저장
    const textContent = bubbleElement.innerText
        .replace(bubbleElement.querySelector('.time')?.innerText || '', '')
        .replace(bubbleElement.querySelector('.name')?.innerText || '', '')
        .trim();
    menu.dataset.copyText = textContent;
    
    document.body.appendChild(menu);
    
    // 다른 곳 클릭하면 메뉴 닫기
    setTimeout(() => {
        document.addEventListener('click', closeCopyMenu);
    }, 100);
}

/**
 * 말풍선 텍스트 복사
 */
function copyBubbleText(event) {
    event.stopPropagation();
    
    const menu = event.target.closest('.copy-menu');
    const textToCopy = menu.dataset.copyText;
    
    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            alert('복사되었습니다!');
            menu.remove();
        })
        .catch(err => {
            console.error('복사 실패:', err);
            // 폴백: textarea 사용
            const textarea = document.createElement('textarea');
            textarea.value = textToCopy;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            alert('복사되었습니다!');
            menu.remove();
        });
}

/**
 * 복사 메뉴 닫기
 */
function closeCopyMenu() {
    const menu = document.querySelector('.copy-menu');
    if (menu) {
        menu.remove();
    }
    document.removeEventListener('click', closeCopyMenu);
}


// ============================================
// 이벤트 리스너
// ============================================

// 전송 버튼 클릭
if (sendBtn) {
    sendBtn.addEventListener("click", sendMessage);
}

// Enter 키로 전송 (Shift+Enter는 줄바꿈)
if (chatInput) {
    chatInput.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// 페이지 로드 시 스크롤 맨 아래로
window.onload = function() {
    scrollToBottom();
};
