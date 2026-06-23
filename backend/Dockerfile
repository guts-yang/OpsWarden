# 默认 Docker Hub；若本机 IPv6 访问 hub 失败，在 .env 中设置 DOCKERHUB_PYTHON_IMAGE（见 .env.example）
ARG PYTHON_BASE_IMAGE=python:3.11-slim-bookworm
FROM ${PYTHON_BASE_IMAGE}

WORKDIR /app

# 直接安装 Python 依赖（使用官方 PyPI，添加 trusted-host 解决 SSL 问题）
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com -r /app/requirements.txt

COPY backend /app/backend

WORKDIR /app/backend

# config.py resolves repo-root .env at /app/.env; empty file avoids missing-path edge cases
RUN touch /app/.env

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
