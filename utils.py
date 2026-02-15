"""
Utility Functions
Java Util 클래스 Python 포팅
"""
import re
import uuid
from datetime import datetime, date
from typing import Optional


class Util:
    """유틸리티 함수 모음"""
    
    @staticmethod
    def xss_handling(content: str) -> str:
        """
        XSS(Cross Site Scripting) 방지 처리
        HTML 특수 문자를 이스케이프 처리
        
        Args:
            content: 원본 문자열
            
        Returns:
            이스케이프 처리된 문자열
        """
        if not content:
            return content
        
        # HTML 특수 문자 이스케이프
        content = content.replace("&", "&amp;")   # & 먼저 처리 (중요!)
        content = content.replace("<", "&lt;")    # <
        content = content.replace(">", "&gt;")    # >
        content = content.replace('"', "&quot;")  # "
        
        return content
    
    @staticmethod
    def file_rename(origin_filename: str) -> str:
        """
        파일명 변경 (중복 방지)
        형식: yyyyMMddHHmmss_랜덤5자리.확장자
        
        Args:
            origin_filename: 원본 파일명
            
        Returns:
            변경된 파일명
            
        Example:
            >>> Util.file_rename("photo.jpg")
            "20260128153045_12345.jpg"
        """
        # 현재 시간 (yyyyMMddHHmmss)
        date_str = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 5자리 랜덤 숫자
        import random
        ran_num = random.randint(0, 99999)
        str_num = f"_{ran_num:05d}"
        
        # 확장자 추출
        if "." in origin_filename:
            ext = origin_filename[origin_filename.rfind("."):]
        else:
            ext = ""
        
        return date_str + str_num + ext
    
    @staticmethod
    def file_rename_uuid(origin_filename: str) -> str:
        """
        파일명 변경 (UUID 사용 - 더 안전)
        형식: uuid.확장자
        
        Args:
            origin_filename: 원본 파일명
            
        Returns:
            변경된 파일명
            
        Example:
            >>> Util.file_rename_uuid("photo.jpg")
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg"
        """
        # 확장자 추출
        if "." in origin_filename:
            ext = origin_filename[origin_filename.rfind("."):]
        else:
            ext = ""
        
        # UUID 생성
        unique_id = str(uuid.uuid4())
        
        return unique_id + ext
    
    @staticmethod
    def format_chat_time(time: Optional[datetime]) -> str:
        """
        채팅 시간 포맷팅
        - 오늘: HH:mm
        - 과거: yyyy.MM.dd
        
        Args:
            time: datetime 객체
            
        Returns:
            포맷된 시간 문자열
        """
        if not time:
            return ""
        
        today = date.today()
        time_date = time.date()
        
        if time_date == today:
            # 오늘: 시간만
            return time.strftime("%H:%M")
        else:
            # 과거: 날짜
            return time.strftime("%Y.%m.%d")
    
    @staticmethod
    def format_noti_time(time: Optional[datetime]) -> str:
        """
        알림 시간 포맷팅
        - 오늘: HH:mm
        - 과거: MM.dd
        
        Args:
            time: datetime 객체
            
        Returns:
            포맷된 시간 문자열
        """
        if not time:
            return ""
        
        today = date.today()
        time_date = time.date()
        
        if time_date == today:
            # 오늘: 시간만
            return time.strftime("%H:%M")
        else:
            # 과거: 월.일
            return time.strftime("%m.%d")
    
    @staticmethod
    def validate_image_extension(filename: str, allowed_extensions: list = None) -> bool:
        """
        이미지 파일 확장자 검증
        
        Args:
            filename: 파일명
            allowed_extensions: 허용 확장자 리스트 (기본값: jpg, jpeg, png, gif, webp)
            
        Returns:
            유효하면 True, 아니면 False
        """
        if allowed_extensions is None:
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        
        if "." not in filename:
            return False
        
        ext = filename[filename.rfind(".") + 1:].lower()
        return ext in allowed_extensions
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        파일명 안전하게 처리 (특수문자 제거)
        
        Args:
            filename: 원본 파일명
            
        Returns:
            안전한 파일명
        """
        # 위험한 문자 제거 (경로 조작 방지)
        filename = filename.replace("..", "")
        filename = filename.replace("/", "")
        filename = filename.replace("\\", "")
        
        # 파일명만 추출 (경로 제거)
        if "/" in filename:
            filename = filename.split("/")[-1]
        if "\\" in filename:
            filename = filename.split("\\")[-1]
        
        return filename


# Jinja2 템플릿 필터로 등록할 함수들
def template_filters():
    """Jinja2 템플릿에서 사용할 필터 함수들"""
    return {
        'xss': Util.xss_handling,
        'chat_time': Util.format_chat_time,
        'noti_time': Util.format_noti_time,
    }
