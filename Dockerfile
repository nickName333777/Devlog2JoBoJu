FROM python:3.10

RUN apt-get update && apt-get install -y \
    iputils-ping curl net-tools vim htop \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app
    
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
