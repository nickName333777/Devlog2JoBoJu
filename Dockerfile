# Python 3.10 베이스 이미지
# 슬림 버전 (이전 사용-> issue로 사용중지) - 최소화된 이미지 (~120MB)
#FROM python:3.10-slim
#
# 풀 버전 (모든 유틸리티 포함) - ~900MB
FROM python:3.10
#또는 더 구체적으로:
# Debian 기반 풀 버전
#FROM python:3.10-bullseye
# Ubuntu 기반 풀 버전  
#FROM python:3.10-focal

RUN apt-get update && apt-get install -y \
    iputils-ping curl net-tools vim htop \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Oracle Instant Client 설치를 위한 필수 패키지
# libaio 심볼릭 링크 **정확히 이렇게* 
#    && ln -sf /usr/lib/x86_64-linux-gnu/libaio1t64.so.1 /usr/lib/x86_64-linux-gnu/libaio.so.1 \ # Wrong
#    && ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1 \  # Correct
#    && ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so \ # Correct
#    && ldconfig \  
    
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libaio1t64 \
    && ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1 \
    && ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so \
    && ldconfig \
    && rm -rf /var/lib/apt/lists/*

# Oracle Instant Client 다운로드 및 설치
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    wget https://download.oracle.com/otn_software/linux/instantclient/2115000/instantclient-basic-linux.x64-21.15.0.0.0dbru.zip && \
    unzip instantclient-basic-linux.x64-21.15.0.0.0dbru.zip && \
    rm -f instantclient-basic-linux.x64-21.15.0.0.0dbru.zip && \
    cd /opt/oracle/instantclient* && \
    rm -f *jdbc* *occi* *mysql* *README *jar uidrvci genezi adrci && \
    echo /opt/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

# 환경 변수 설정
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_15:$LD_LIBRARY_PATH
ENV PATH=/opt/oracle/instantclient_21_15:$PATH

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 정적 파일 디렉토리 생성
RUN mkdir -p /app/static/css /app/static/js /app/static/images

# 포트 노출
EXPOSE 8880

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8880", "--reload"]
