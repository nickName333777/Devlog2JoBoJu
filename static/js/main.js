console.log('main.js loaded...');

// API_BASE_URL은 common.js에서 이미 선언됨

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', () => {
    loadRecentPosts();
});

// 최근 게시글 로딩 (예시)
async function loadRecentPosts() {
    const recentPostsContainer = document.getElementById('recentPosts');
    
    if (!recentPostsContainer) return;
    
    try {
        // TODO: 실제 API 연동 시 주석 해제
        // const response = await fetch(`${API_BASE_URL}/board/recent?limit=6`); // ${API_BASE_URL}/board/recent?limit=6 요청주소 처리필요
        // const posts = await response.json();
        
        // 임시 더미 데이터
        const posts = [
            {
                id: 1,
                title: 'FastAPI와 Spring Boot 비교',
                author: '개발자A',
                created_at: new Date(Date.now() - 3600000).toISOString(),
                content: 'FastAPI와 Spring Boot의 장단점을 비교해봅니다. 두 프레임워크 모두 각자의 강점이 있습니다...',
                views: 150,
                likes: 12
            },
            {
                id: 2,
                title: 'Docker Compose 활용법',
                author: '개발자B',
                created_at: new Date(Date.now() - 7200000).toISOString(),
                content: 'Docker Compose를 활용한 개발 환경 구성 방법을 소개합니다...',
                views: 203,
                likes: 25
            },
            {
                id: 3,
                title: 'Elasticsearch 검색 성능 최적화',
                author: '개발자C',
                created_at: new Date(Date.now() - 86400000).toISOString(),
                content: 'Elasticsearch의 검색 성능을 향상시키는 여러 방법들을 다룹니다...',
                views: 178,
                likes: 18
            },
            {
                id: 4,
                title: 'JWT 인증 구현하기',
                author: '개발자D',
                created_at: new Date(Date.now() - 172800000).toISOString(),
                content: 'JWT를 활용한 인증/인가 시스템 구현 방법을 단계별로 설명합니다...',
                views: 312,
                likes: 45
            },
            {
                id: 5,
                title: 'Oracle DB 성능 튜닝 팁',
                author: '개발자E',
                created_at: new Date(Date.now() - 259200000).toISOString(),
                content: 'Oracle Database의 성능을 개선할 수 있는 다양한 튜닝 기법들을 공유합니다...',
                views: 256,
                likes: 32
            },
            {
                id: 6,
                title: 'RESTful API 설계 원칙',
                author: '개발자F',
                created_at: new Date(Date.now() - 345600000).toISOString(),
                content: 'RESTful API를 설계할 때 지켜야 할 핵심 원칙들을 정리했습니다...',
                views: 421,
                likes: 56
            }
        ];
        
        renderPosts(posts);
        
    } catch (error) {
        console.error('게시글 로딩 오류:', error);
        recentPostsContainer.innerHTML = '<p style="text-align: center; padding: 40px;">게시글을 불러오는데 실패했습니다.</p>';
    }
}

// 게시글 렌더링
function renderPosts(posts) {
    const recentPostsContainer = document.getElementById('recentPosts');
    
    if (posts.length === 0) {
        recentPostsContainer.innerHTML = '<p style="text-align: center; padding: 40px;">게시글이 없습니다.</p>';
        return;
    }
    
    const postsHTML = posts.map(post => `
        <div class="post-card">
            <h3><a href="/board/view.html?id=${post.id}">${escapeHtml(post.title)}</a></h3>
            <div class="post-meta">
                <span><i class="fa-solid fa-user"></i> ${escapeHtml(post.author)}</span>
                <span><i class="fa-solid fa-clock"></i> ${formatDate(post.created_at)}</span>
            </div>
            <p>${escapeHtml(post.content)}</p>
            <div class="post-stats">
                <span><i class="fa-solid fa-eye"></i> ${post.views}</span>
                <span><i class="fa-solid fa-heart"></i> ${post.likes}</span>
            </div>
        </div>
    `).join('');
    
    recentPostsContainer.innerHTML = postsHTML;
}

// HTML 이스케이프 (XSS 방지)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 전역 검색 기능
const globalSearch = document.getElementById('globalSearch');
if (globalSearch) {
    globalSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = globalSearch.value.trim();
            if (query) {
                // 검색 페이지로 이동
                window.location.href = `/search.html?q=${encodeURIComponent(query)}`; // /search.html?q=${encodeURIComponent(query)} 요청주소 처리필요
            }
        }
    });
}
