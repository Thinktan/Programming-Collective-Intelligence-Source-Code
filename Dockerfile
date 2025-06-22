FROM python:2.7

# 设置工作目录（与本地挂载目录一致）
WORKDIR /app

# 可选：复制 requirements.txt 并安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 默认命令（PyCharm 会覆盖这个）
CMD ["python"]