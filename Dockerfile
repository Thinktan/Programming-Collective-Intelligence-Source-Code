FROM python:2.7

# 与 PyCharm 挂载点保持一致，避免路径错乱
WORKDIR /app

# 只复制 pip 依赖文件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 可选：复制代码（非必要，PyCharm会挂载）
# COPY . .

CMD ["python"]