"""
Jinja2 설정
"""
from fastapi.templating import Jinja2Templates

from pathlib import Path
import os
from dotenv import load_dotenv
# 환경 변수 로드, .env 파일 명시적 로드 (최우선)
load_dotenv(override=True)

# Jinja2 템플릿
TEMPLATE_DIR = os.getenv("TEMPLATE_DIR")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# 템플릿 전역 함수 추가 (URL 생성용)
def url_for(request, name: str, **path_params):
    """템플릿에서 URL 생성"""
    return request.url_for(name, **path_params)

templates.env.globals['url_for'] = url_for

