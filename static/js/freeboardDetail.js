/**
 * 자유게시판 상세 JavaScript
 */
console.log('freeboardDetail.js loaded...');

// 전역 변수
let boardNo = null;
let currentUser = null;
let boardData = null;

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', async () => {
    // 인증 체크 ==> 비회원도 목록, 상세조회 가능하게 인증 불활성화
    // if (!isLoggedIn()) {    // isLoggedIn() in common.js
    //     alert('로그인이 필요합니다.');
    //     window.location.href = '/member/login'; // jinja2 SSR 동적 렌더링, GET
    //     return;
    // }

    // 현재 사용자 정보 가져오기
    currentUser = getCurrentUserInfo();
    console.log("currentUser = ", currentUser); 

    // URL에서 게시글 번호 추출
    console.log("window.location 객체 = ", window.location);  // http://localhost:8880/board/43
    //console.log("window.location.pathname 문자열 = ", window.location.pathname);  //  http://localhost:8880/board/43
    //console.log("window.location.search = ", window.location.search);  // empty 

    // const pathParts = window.location.pathname.split("/");
    // const boardNo = pathParts[pathParts.length - 1];
    const boardNo = window.location.pathname
    .split("/")
    .filter(Boolean)
    .pop();
    // const boardNo = window.location.href.split("/");


    if (!boardNo) {
        alert('잘못된 접근입니다.');
        window.location.href = '/board/list'; // jinja2 SSR rendering
        return;
    }

    // 헤더/푸터 로드
    //await loadCommonComponents(); // jinja2 에서는 불필요

    // 게시글 로드
    // await loadBoardDetail(boardNo); // 사실 게시글 상세는 조회는 url 페이지 jinja2 SSR 렌더링이면 되고, AJAX 비동기 CSR 랜더링은 그냥 연습으로

    // 댓글 로드 
    // await loadComments();
});

/**
 * 게시글 상세 로드
 */
async function loadBoardDetail(boardNo) {
    const article = document.getElementsByClassName('board-article')[0];

    // 로딩 표시
    article.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <p>게시글을 불러오는 중...</p>
        </div>
    `;

    try {
        const response = await fetchAPI(`/api/board/ajax/detail/${boardNo}`);

        if (!response.ok) {
            throw new Error('게시글을 찾을 수 없습니다.');
        }

        boardData = await response.json();
        console.log("fetched board-detail boardData = ", boardData);
        //console.log("fetched board-detail boardData.board = ", boardData.board);
        //console.log("fetched board-detail boardData.board.author = ", boardData.board.author);
        renderBoardDetail(boardData);

    } catch (error) {
        console.error('게시글 로드 오류:', error);
        article.innerHTML = `
            <div class="loading">
                <p>게시글을 불러오는데 실패했습니다.</p>
                <p>${error.message}</p>
                <button class="btn-list" onclick="goToList()">목록으로</button>
            </div>
        `;
    }
}

/**
 * 게시글 상세 렌더링
 */
function renderBoardDetail(boardData) {
    const article = document.getElementById('boardArticle');
    console.log("fetched board-detail boardData.board = ", boardData.board);
    const board = boardData.board;

    // 작성자인지 확인
    const isAuthor = currentUser && currentUser.memberNo === board.author.member_no;

    console.log("isAuthor =", isAuthor);

    article.innerHTML = `
        <div class="article-header">
            <h1 class="article-title">${escapeHtml(board.board_title)}</h1>
            
            <div class="article-meta">
                <div class="author-info">
                    ${board.author.profile_img 
                        ? `<img src="/uploads${board.author.profile_img}" alt="프로필" class="author-profile">`
                        : `<img src="{{ url_for(request, 'static', path='/images/user.png') }}" alt="프로필디폴트" class="author-profile">`
                    }
                    <div class="author-details">
                        <span class="author-name">${escapeHtml(board.author.member_nickname)}</span>
                        <!-- <span class="author-level">Level ${board.author.member_level_no}</span> -->
                    </div>
                </div>

                <div class="article-stats">
                    <div class="stat-item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <span>${formatDate(board.b_create_date)}</span>
                    </div>
                    ${board.b_update_date ? `
                        <div class="stat-item">
                            <span>(수정됨)</span>
                        </div>
                    ` : ''}
                    <div class="stat-item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                        </svg>
                        <span>${board.board_count}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="article-content">
            ${escapeHtml(board.board_content)}
        </div>
        <!-- boardData.images는 image_list = [f"/uploads{os.path.join(img.img_path, img.img_rename)}" for img in board.images] -->
        ${boardData.images && boardData.images.length > 0 ? `
            <div class="article-images">
                
                <!-- 첫 번째 이미지: thumbnail로 100% 크기 -->
                <div class="image-main">
                    <img src="${boardData.images[0]}" alt="이미지">
                </div>            
            
                <!-- 나머지 이미지: thumbnail 25% 크기  -->
                ${boardData.images.length > 1 ? `
                    <div class="image-thumbs">
                        ${boardData.images.slice(1).map(img => `
                            <div class="thumb-item">
                                <img src="${img}" alt="이미지">
                            </div>
                        `).join('')}
                    </div>
                ` : ''}

            </div>
        ` : ''}

        <div class="article-actions">
            <!-- 좋아요 버튼 -->
            <button class="btn-like ${boardData.is_liked ? 'liked' : ''}" onclick="toggleLike(${board.board_no})" id="likeBtn">
                <svg viewBox="0 0 24 24" fill="${boardData.is_liked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                    <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                </svg>
                <span class="like-count" id="likeCount">${boardData.like_count}</span>
            </button>

            <!-- 목록 버튼 -->
            <button class="btn-list" onclick="goToList()">목록</button>

            <!-- 작성자 전용 버튼 -->
            ${isAuthor ? `
                <button class="btn-edit" onclick="goToEdit(${board.board_no})">수정</button>
                <button class="btn-delete" onclick="deleteBoard(${board.board_no})">삭제</button>
            ` : ''}
        </div>
    `;

    // 댓글 개수 업데이트
    document.getElementById('commentCount').textContent = boardData.comment_count;
}


/**
 * 목록으로 이동
 */
function goToList() {
    window.location.href = '/board/list'; // jinja2 SSR
}

/**
 * 수정 페이지로 이동 (다음 단계에서 구현)
 */
function goToEdit(boardNo) {
    window.location.href = `/board2/update/${boardNo}`;
}

/**
 * 게시글 삭제
 */
async function deleteBoard(boardNo) {
    if (!confirm('정말 삭제하시겠습니까?')) {
        return;
    }

    try {
        const response = await fetch(`/board2/delete/${boardNo}`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`서버 오류: ${response.status}`);
        }

        const result = await response.json();

        // 삭제 성공 여부 검사
        if (result.success && result.deleted_count === 1) {
            alert('게시글이 삭제되었습니다.');
            window.location.href = '/board/list';
        } else {
            alert(result.message || '게시글 삭제에 실패했습니다.');
        }

    } catch (error) {
        console.error('게시글 삭제 오류:', error);
        alert('네트워크 오류로 삭제에 실패했습니다.');
    }
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
 * 날짜 포맷팅
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 현재 사용자 정보 가져오기
 */
function base64UrlDecode(str) { // JWT payload가 -(dash), __(underscore)포함한경우 Base64불가, Base64URL써야함
    str = str.replace(/-/g, '+').replace(/_/g, '/');
    const pad = str.length % 4;
    if (pad) {
        str += '='.repeat(4 - pad);
    }
    return atob(str);
}

function getCurrentUserInfo() {
    const token = localStorage.getItem('access_token'); // JWT (JSON Web Token)
    console.log("getCurrentUserInfo: token =", token); // 세션만료되면 access_token사라지고, 로그인 안된상태라 token = undefined됨
    if (typeof token !== "string" || token.trim() === "") return null; // null, undefined, 빈문자열, 공백문자열 다 차단



    try {
        // JWT payload가 -(dash), __(underscore)포함한경우 Base64불가, Base64URL써야함
        const base64Payload = token.split('.')[1];
        console.log("base64Payload =", base64Payload); 

        if (typeof base64Payload !== "string" || base64Payload.trim() === "") return null; // base64Payload = undefined경우 방어: 그냥 null반환
        const payload = JSON.parse(base64UrlDecode(base64Payload));
        console.log("payload =", payload);

        return {
            memberNo: payload.member_no,
            memberEmail: payload.sub            
        };
    } catch (error) {
        console.error('토큰 파싱 오류:', error);
        return null;
    }
}
