"""
Custom Exceptions
Java Exception 클래스 Python 포팅

[ 에러 코드 체계 ]
코드			예외								상태	코드		설명
FILE_001	FileUploadException				400			파일 업로드 실패
FILE_002	ImageDeleteException			500			이미지 삭제 실패
FILE_003	InvalidFileExtensionException	400			잘못된 확장자
FILE_004	FileSizeLimitException			400			파일 크기 초과
AUTH_001	UnauthorizedException			401			인증 필요 (status_code=302?), login
AUTH_002	ForbiddenException				403			권한 없음 (status_code=302?), login-role
DATA_001	NotFoundException				404			데이터 없음
DATA_002	DuplicateException				409			중복 데이터
DATA_003	ValidationException				422			검증 실패
COMMON_001	DevlogException					500			일반 오류
COMMON_999	Exception						500			예상치 못한 오류
"""
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime


# ============================================
# 기본 예외 클래스
# ============================================

class JoBoJuException(Exception):
    """프로젝트 기본 예외 클래스"""
    
    def __init__(self, message: str = "서버 오류가 발생했습니다."):
        self.message = message
        super().__init__(self.message)


# ============================================
# 파일 관련 예외
# ============================================

class FileUploadException(JoBoJuException):
    """
    파일 업로드 예외
    Java: FileUploadException extends RuntimeException
    """
    
    def __init__(self, message: str = "파일 업로드 중 예외 발생"):
        super().__init__(message)


class ImageDeleteException(JoBoJuException):
    """
    이미지 삭제 예외
    Java: ImageDeleteException extends RuntimeException
    """
    
    def __init__(self, message: str = "이미지 삭제 중 예외 발생"):
        super().__init__(message)


class InvalidFileExtensionException(JoBoJuException):
    """잘못된 파일 확장자 예외"""
    
    def __init__(self, message: str = "허용되지 않은 파일 형식입니다."):
        super().__init__(message)


class FileSizeLimitException(JoBoJuException):
    """파일 크기 제한 초과 예외"""
    
    def __init__(self, message: str = "파일 크기가 제한을 초과했습니다."):
        super().__init__(message)


# ============================================
# 인증 관련 예외
# ============================================

class UnauthorizedException(JoBoJuException):
    """인증 실패 예외"""
    
    def __init__(self, message: str = "인증이 필요합니다."):
        super().__init__(message)


class ForbiddenException(JoBoJuException):
    """권한 없음 예외"""
    
    def __init__(self, message: str = "권한이 없습니다."):
        super().__init__(message)


# ============================================
# 데이터 관련 예외
# ============================================

class NotFoundException(JoBoJuException):
    """데이터 없음 예외"""
    
    def __init__(self, message: str = "요청한 데이터를 찾을 수 없습니다."):
        super().__init__(message)


class DuplicateException(JoBoJuException):
    """중복 데이터 예외"""
    
    def __init__(self, message: str = "이미 존재하는 데이터입니다."):
        super().__init__(message)


class ValidationException(JoBoJuException):
    """데이터 검증 실패 예외"""
    
    def __init__(self, message: str = "데이터 검증에 실패했습니다."):
        super().__init__(message)


# ============================================
# 에러 응답 DTO
# ============================================

class ErrorResponse:
    """
    에러 응답 DTO
    Java: ErrorResponseDTO
    """
    
    def __init__(self, code: str, message: str, timestamp: str = None):
        self.code = code
        self.message = message
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "timestamp": self.timestamp
        }


# ============================================
# 전역 예외 핸들러 (FastAPI용)
# ============================================

def create_error_response(code: str, message: str, status_code: int = 500):
    """
    에러 응답 생성 헬퍼 함수
    
    Args:
        code: 에러 코드
        message: 에러 메시지
        status_code: HTTP 상태 코드
        
    Returns:
        HTTPException
    """
    error = ErrorResponse(code=code, message=message)
    raise HTTPException(
        status_code=status_code,
        detail=error.to_dict()
    )


# ============================================
# 예외 핸들러 등록 함수
# ============================================

def register_exception_handlers(app):
    """
    FastAPI 앱에 전역 예외 핸들러 등록
    
    Usage:
        app = FastAPI()
        register_exception_handlers(app)
    """
    from fastapi.responses import JSONResponse
    
    @app.exception_handler(FileUploadException)
    async def file_upload_exception_handler(request, exc: FileUploadException):
        error = ErrorResponse(
            code="FILE_001",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error.to_dict()
        )
    
    @app.exception_handler(ImageDeleteException)
    async def image_delete_exception_handler(request, exc: ImageDeleteException):
        error = ErrorResponse(
            code="FILE_002",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error.to_dict()
        )
    
    @app.exception_handler(InvalidFileExtensionException)
    async def invalid_file_extension_handler(request, exc: InvalidFileExtensionException):
        error = ErrorResponse(
            code="FILE_003",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error.to_dict()
        )
    
    @app.exception_handler(FileSizeLimitException)
    async def file_size_limit_handler(request, exc: FileSizeLimitException):
        error = ErrorResponse(
            code="FILE_004",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error.to_dict()
        )
    
    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request, exc: UnauthorizedException):
        error = ErrorResponse(
            code="AUTH_001",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error.to_dict()
        )
    
    @app.exception_handler(ForbiddenException)
    async def forbidden_handler(request, exc: ForbiddenException):
        error = ErrorResponse(
            code="AUTH_002",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error.to_dict()
        )
    
    @app.exception_handler(NotFoundException)
    async def not_found_handler(request, exc: NotFoundException):
        error = ErrorResponse(
            code="DATA_001",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.to_dict()
        )
    
    @app.exception_handler(DuplicateException)
    async def duplicate_handler(request, exc: DuplicateException):
        error = ErrorResponse(
            code="DATA_002",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error.to_dict()
        )
    
    @app.exception_handler(ValidationException)
    async def validation_handler(request, exc: ValidationException):
        error = ErrorResponse(
            code="DATA_003",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error.to_dict()
        )
    
    @app.exception_handler(JoBoJuException)
    async def joboju_exception_handler(request, exc: JoBoJuException):
        error = ErrorResponse(
            code="COMMON_001",
            message=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        # 일반 예외 (예상하지 못한 오류)
        error = ErrorResponse(
            code="COMMON_999",
            message="서버 오류가 발생했습니다."
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error.to_dict()
        )
