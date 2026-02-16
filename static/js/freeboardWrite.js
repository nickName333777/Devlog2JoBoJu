/**
 * Basic vs Kong 챗봇 팝업 전환
 */

let win_basic = null;
let win_kong = null;

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

document.getElementById("optionBtn").addEventListener('click', function() {

    console.log("optionBtn clicked...")
    const select = document.getElementById("chatbotType");
    const selectedValue = select.value; // "basic" or "kong"
	const chatbotProfileImg = document.getElementById("chatbotProfileImg");

    let url = "";
    let pWinName = ""; // 팝업차이름 win-basic vs. win-kong 

    // 자식1 팝업 → 자식2 팝업으로 전역 변수 전달
    window.globalData = {
        boardNo: window.boardNo,
        loginMemberNo: window.loginMemberNo,
        //boardNo: window.boardNo,
        //boardCode: window.boardCode,
        //boardTitle: window.boardTitle,
        //
        //loginMemberNo: window.loginMemberNo,
        //memberNickname: window.memberNickname,
        //profileImg: window.profileImg,
        //beansAmount: window.beansAmount        
        // more variables
    };    

    if (selectedValue === "basic") {
        // win_kong 닫기
        if (win_kong && !win_kong.closed) {
            win_kong.close();
            win_kong = null;
        }
		
		// 챗봇 이미지 업데이트
		chatbotProfileImg.src="/static/images/board/freeboard/chatbot1.png"

        url = "/api/chatbot/freeboard/popupBasicChatbot";
        pWinName = "win-basic";
        win_basic = window.open(url, pWinName, "width=650,height=760");
    } else if (selectedValue === "kong") {
        // win_basic 닫기
        if (win_basic && !win_basic.closed) {
            win_basic.close();
            win_basic = null;
        }  
        
		// 챗봇 이미지 업데이트
		chatbotProfileImg.src="/static/images/board/freeboard/chatbot5.png"
		
        url = "/api/chatbot/freeboard/popupKongChatbot";
        pWinName = "win-kong";
        win_kong = window.open(url, pWinName, "width=650,height=760");
    }

});
