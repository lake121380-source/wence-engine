FROM python:3.11-slim

WORKDIR /app

COPY requirements.runtime.txt .
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir --retries 5 --timeout 120 -i ${PIP_INDEX_URL} -r requirements.runtime.txt

COPY . .

EXPOSE 8080
# 单 worker：OTP验证码/登录限速使用进程内存，多worker会导致跨进程状态丢失
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
